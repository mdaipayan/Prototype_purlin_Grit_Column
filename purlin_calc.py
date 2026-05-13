"""Purlin design calculations for the Streamlit UI and PDF report.

The module keeps the engineering arithmetic in one place so that the web page
and the generated report always use the same values.  Units are noted at each
conversion boundary because most section properties are stored in traditional
steel-table units (cm², cm³, cm⁴) while IS 800 equations use N-mm units.
"""

from __future__ import annotations

import math
from typing import Any


SECTION_CLASS_ORDER = {"Plastic": 1, "Compact": 2, "Semi-compact": 3, "Slender": 4}


def _as_float(value: Any, default: float = 0.0) -> float:
    """Return a numeric value without letting bad UI/session data crash a run."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _classify_ratio(ratio: float, limits: list[float]) -> str:
    if ratio <= limits[0]:
        return "Plastic"
    if ratio <= limits[1]:
        return "Compact"
    if ratio <= limits[2]:
        return "Semi-compact"
    return "Slender"


def _section_classification(sp: dict[str, Any], fy: float) -> dict[str, Any]:
    """Classify flanges/webs using IS 800:2007 Table 2 style limits."""
    epsilon = math.sqrt(250.0 / fy) if fy > 0 else 1.0

    bf = _as_float(sp.get("bf"))
    tw = _as_float(sp.get("tw"), 1.0)
    tf = _as_float(sp.get("tf"), 1.0)
    h = _as_float(sp.get("h"))

    b_tf = max((bf - tw) / (2.0 * tf), 0.0) if tf else math.inf
    d_tw = max((h - 2.0 * tf) / tw, 0.0) if tw else math.inf

    flange_limits = [9.4 * epsilon, 13.6 * epsilon, 15.7 * epsilon]
    web_limits = [84.0 * epsilon, 105.0 * epsilon, 126.0 * epsilon]

    flange_class = _classify_ratio(b_tf, flange_limits)
    web_class = _classify_ratio(d_tw, web_limits)
    overall = max([flange_class, web_class], key=lambda label: SECTION_CLASS_ORDER[label])

    return {
        "name": overall,
        "overall": overall,
        "class_type": SECTION_CLASS_ORDER[overall],
        "epsilon": epsilon,
        "b_tf": b_tf,
        "d_tw": d_tw,
        "flange_class": flange_class,
        "web_class": web_class,
        "limits": {"flange": flange_limits, "web": web_limits},
    }


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return math.inf if numerator > 0 else 0.0
    return numerator / denominator


def run_purlin_design(inp: dict[str, Any]) -> dict[str, Any]:
    """Run purlin design checks and return all values needed by UI/PDF.

    Input keys mirror the Streamlit controls.  Returned values are intentionally
    verbose so formula blocks, summary tables, and reports do not recalculate or
    diverge from the governing design result.
    """
    sp = dict(inp.get("section_props") or {})

    span_m = _as_float(inp.get("span_m"), 5.0)
    spacing_m = _as_float(inp.get("spacing_m"), 1.5)
    slope_deg = _as_float(inp.get("roof_slope_deg", inp.get("slope_deg")), 10.0)
    dead_load = _as_float(inp.get("dead_load"), 0.55)
    live_load = _as_float(inp.get("live_load"), 0.75)
    wind_pressure = _as_float(inp.get("wind_pressure"), 0.70)
    cpe = _as_float(inp.get("Cp_ext", inp.get("Cpe")), -0.8)
    cpi = _as_float(inp.get("Cp_int", inp.get("Cpi")), 0.2)
    fy = _as_float(inp.get("fy"), 250.0)
    gm0 = _as_float(inp.get("gm0"), 1.10)

    theta = math.radians(slope_deg)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)

    # kg/m × g / 1000 = kN/m.
    sw_kNm = _as_float(sp.get("weight")) * 9.81 / 1000.0
    w_dl_total = dead_load * spacing_m + sw_kNm
    w_ll_total = live_load * spacing_m

    wz_DL = w_dl_total * cos_t
    wy_DL = w_dl_total * sin_t
    wz_LL = w_ll_total * cos_t
    wy_LL = w_ll_total * sin_t

    # Net wind is taken normal to the roof sheeting.  Negative values indicate
    # uplift/suction; design effects use absolute governing magnitudes below.
    w_wind = wind_pressure * (cpe - cpi) * spacing_m

    signed_combos = {
        "LC1: 1.5(DL+LL)": (1.5 * (wz_DL + wz_LL), 1.5 * (wy_DL + wy_LL)),
        "LC2: 1.2(DL+LL+Wind)": (1.2 * (wz_DL + wz_LL + w_wind), 1.2 * (wy_DL + wy_LL)),
        "LC3: 0.9DL+1.5Wind": (0.9 * wz_DL + 1.5 * w_wind, 0.9 * wy_DL),
    }
    governing_combo, (wz_signed, wy_signed) = max(
        signed_combos.items(), key=lambda item: abs(item[1][0]) + abs(item[1][1])
    )
    wz_d = abs(wz_signed)
    wy_d = abs(wy_signed)

    Mz_kNm = wz_d * span_m**2 / 8.0
    My_kNm = wy_d * span_m**2 / 8.0
    Vz_kN = wz_d * span_m / 2.0
    Vy_kN = wy_d * span_m / 2.0

    cls = _section_classification(sp, fy)
    use_plastic = cls["overall"] in ("Plastic", "Compact")
    z_major = _as_float(sp.get("Zpx" if use_plastic else "Zxx"))
    z_minor = _as_float(sp.get("Zpy" if use_plastic else "Zyy"))

    Mdz_kNm = z_major * fy / (gm0 * 1000.0) if gm0 else 0.0
    Mdy_kNm = z_minor * fy / (gm0 * 1000.0) if gm0 else 0.0
    biaxial_ratio = _safe_ratio(My_kNm, Mdy_kNm) + _safe_ratio(Mz_kNm, Mdz_kNm)
    biaxial_ok = biaxial_ratio <= 1.0 and cls["overall"] != "Slender"

    Av_mm2 = _as_float(sp.get("h")) * _as_float(sp.get("tw"))
    Vd_kN = Av_mm2 * fy / (math.sqrt(3.0) * gm0 * 1000.0) if gm0 else 0.0
    shear_ratio = _safe_ratio(Vz_kN, Vd_kN)
    shear_ok = shear_ratio <= 1.0

    E = 2.0e5  # MPa = N/mm²
    L_mm = span_m * 1000.0
    Ixx_mm4 = _as_float(sp.get("Ixx")) * 1.0e4
    service_w = wz_DL + wz_LL  # kN/m == N/mm
    delta_max_mm = (5.0 * service_w * L_mm**4 / (384.0 * E * Ixx_mm4)) if Ixx_mm4 else math.inf
    delta_limit_mm = L_mm / 180.0
    defl_ratio = _safe_ratio(delta_max_mm, delta_limit_mm)
    defl_ok = defl_ratio <= 1.0

    checks_ok = [biaxial_ok, shear_ok, defl_ok, cls["overall"] != "Slender"]
    overall_status = "SAFE" if all(checks_ok) else "UNSAFE"

    wz_values = list(signed_combos.values())
    return {
        "status": "Purlin calculations complete.",
        "overall_status": overall_status,
        "section_name": inp.get("section_name", "Unknown Section"),
        "section_props": sp,
        "span_m": span_m,
        "spacing_m": spacing_m,
        "slope_deg": slope_deg,
        "dead_load": dead_load,
        "live_load": live_load,
        "wind_pressure": wind_pressure,
        "Cpe": cpe,
        "Cpi": cpi,
        "Cp_net": cpe - cpi,
        "fy": fy,
        "gm0": gm0,
        "sw_kNm": sw_kNm,
        "w_dl_total": w_dl_total,
        "w_ll_total": w_ll_total,
        "wz_DL": wz_DL,
        "wy_DL": wy_DL,
        "wz_LL": wz_LL,
        "wy_LL": wy_LL,
        "w_wind": w_wind,
        "w_wind_abs": abs(w_wind),
        "wz_1": wz_values[0][0],
        "wy_1": wz_values[0][1],
        "wz_2": wz_values[1][0],
        "wy_2": wz_values[1][1],
        "wz_3": wz_values[2][0],
        "wy_3": wz_values[2][1],
        "wz_d_signed": wz_signed,
        "wy_d_signed": wy_signed,
        "wz_d": wz_d,
        "wy_d": wy_d,
        "governing_combo": governing_combo,
        "Mz_kNm": Mz_kNm,
        "My_kNm": My_kNm,
        "Vz_kN": Vz_kN,
        "Vy_kN": Vy_kN,
        "section_class": cls,
        "Mdz_kNm": Mdz_kNm,
        "Mdy_kNm": Mdy_kNm,
        "biaxial_ratio": biaxial_ratio,
        "biaxial_ok": biaxial_ok,
        "Av_mm2": Av_mm2,
        "Vd_kN": Vd_kN,
        "shear_ratio": shear_ratio,
        "shear_ok": shear_ok,
        "delta_max_mm": delta_max_mm,
        "delta_limit_mm": delta_limit_mm,
        "defl_ratio": defl_ratio,
        "defl_ok": defl_ok,
    }
