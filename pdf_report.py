"""
PDF Report Generator — IS 800:2007 Steel Design Suite
Uses ReportLab Platypus for professional, structured engineering reports.
"""
import io, math
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak
)

# ── Colour Palette ──────────────────────────────────────────────────────────
DARK_BLUE  = colors.HexColor("#1A3557")
MID_BLUE   = colors.HexColor("#2E6DA4")
LIGHT_BLUE = colors.HexColor("#D6E8F7")
ACCENT     = colors.HexColor("#E84040")
GREEN      = colors.HexColor("#1A7A4A")
YELLOW_BG  = colors.HexColor("#FFFBE6")
GREY_LIGHT = colors.HexColor("#F4F4F4")
GREY_MID   = colors.HexColor("#CCCCCC")
WHITE      = colors.white

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm

# ── Style Factory ────────────────────────────────────────────────────────────
def _styles():
    base = getSampleStyleSheet()
    s = {}

    s["title"] = ParagraphStyle("title", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=17, textColor=WHITE,
        alignment=TA_CENTER, spaceAfter=4)

    s["subtitle"] = ParagraphStyle("subtitle", parent=base["Normal"],
        fontName="Helvetica", fontSize=10, textColor=LIGHT_BLUE,
        alignment=TA_CENTER, spaceAfter=2)

    s["h1"] = ParagraphStyle("h1", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=12, textColor=WHITE,
        spaceAfter=4, spaceBefore=8, leftIndent=0,
        backColor=DARK_BLUE, borderPad=5)

    s["h2"] = ParagraphStyle("h2", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=10.5, textColor=DARK_BLUE,
        spaceBefore=8, spaceAfter=3, borderPad=3,
        borderColor=MID_BLUE, borderWidth=0, leftIndent=0)

    s["body"] = ParagraphStyle("body", parent=base["Normal"],
        fontName="Helvetica", fontSize=9.2, leading=13,
        textColor=colors.black, spaceAfter=2)

    s["formula"] = ParagraphStyle("formula", parent=base["Normal"],
        fontName="Courier-Bold", fontSize=9, textColor=DARK_BLUE,
        backColor=GREY_LIGHT, borderPad=4, leftIndent=8,
        spaceAfter=3, spaceBefore=3)

    s["result_ok"] = ParagraphStyle("result_ok", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=9.5, textColor=GREEN,
        backColor=colors.HexColor("#E6F4ED"), borderPad=4,
        spaceAfter=3, alignment=TA_LEFT)

    s["result_fail"] = ParagraphStyle("result_fail", parent=base["Normal"],
        fontName="Helvetica-Bold", fontSize=9.5, textColor=ACCENT,
        backColor=colors.HexColor("#FDECEA"), borderPad=4,
        spaceAfter=3, alignment=TA_LEFT)

    s["caption"] = ParagraphStyle("caption", parent=base["Normal"],
        fontName="Helvetica-Oblique", fontSize=8, textColor=colors.grey,
        spaceAfter=2, alignment=TA_CENTER)

    s["ref"] = ParagraphStyle("ref", parent=base["Normal"],
        fontName="Helvetica-Oblique", fontSize=8.2, textColor=MID_BLUE,
        leftIndent=6, spaceAfter=1)

    s["footer"] = ParagraphStyle("footer", parent=base["Normal"],
        fontName="Helvetica", fontSize=7.5, textColor=colors.grey,
        alignment=TA_CENTER)

    return s


# ── Helper Builders ──────────────────────────────────────────────────────────

def _header_table(title: str, subtitle: str, project: str, date_str: str, s: dict):
    """Dark-blue title banner with project info."""
    data = [[Paragraph(title, s["title"])],
            [Paragraph(subtitle, s["subtitle"])]]
    t = Table(data, colWidths=[PAGE_W - 2 * MARGIN])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
    ]))
    proj_data = [
        ["Project :", project or "—",
         "Date :", date_str,
         "Ref. Code :", "IS 800:2007"]
    ]
    pt = Table(proj_data, colWidths=[None, None, None, None, None, None])
    pt.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",  (0, 0), (-1, -1), 8.5),
        ("FONTNAME",  (0, 0), (0, 0),  "Helvetica-Bold"),
        ("FONTNAME",  (2, 0), (2, 0),  "Helvetica-Bold"),
        ("FONTNAME",  (4, 0), (4, 0),  "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (-1, -1), DARK_BLUE),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return [t, Spacer(1, 4), pt, HRFlowable(width="100%", thickness=1.5,
            color=MID_BLUE, spaceAfter=6, spaceBefore=3)]


def _section_heading(text: str, s: dict):
    return [Paragraph(f"  {text}", s["h1"]), Spacer(1, 3)]


def _subheading(text: str, s: dict):
    return [Paragraph(text, s["h2"])]


def _input_table(rows: list, s: dict, title: str = ""):
    """Two-column table: Parameter | Value."""
    elems = []
    if title:
        elems += _subheading(title, s)
    data = [["Parameter", "Value / Unit"]] + rows
    cw = [(PAGE_W - 2*MARGIN) * 0.62, (PAGE_W - 2*MARGIN) * 0.38]
    t = Table(data, colWidths=cw)
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0),  MID_BLUE),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8.8),
        ("FONTNAME",    (0, 1), (-1, -1), "Helvetica"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GREY_LIGHT]),
        ("GRID",        (0, 0), (-1, -1), 0.4, GREY_MID),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("ALIGN",       (1, 0), (1, -1),  "RIGHT"),
    ]))
    elems += [t, Spacer(1, 5)]
    return elems


def _result_box(label: str, value: str, ok: bool, s: dict):
    colour = GREEN if ok else ACCENT
    symbol = "✓ PASS" if ok else "✗ FAIL"
    bg     = colors.HexColor("#E6F4ED") if ok else colors.HexColor("#FDECEA")
    data = [[label, value, symbol]]
    cw = [(PAGE_W-2*MARGIN)*0.55, (PAGE_W-2*MARGIN)*0.25, (PAGE_W-2*MARGIN)*0.20]
    t = Table(data, colWidths=cw)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), bg),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 9),
        ("TEXTCOLOR",     (2, 0), (2, 0),  colour),
        ("GRID",          (0, 0), (-1, -1), 0.4, colour),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("ALIGN",         (1, 0), (2, 0),  "CENTER"),
    ]))
    return [t, Spacer(1, 4)]


def _formula_block(formula: str, s: dict, ref: str = ""):
    elems = [Paragraph(formula, s["formula"])]
    if ref:
        elems.append(Paragraph(f"[Ref: {ref}]", s["ref"]))
    return elems + [Spacer(1, 2)]


def _overall_verdict(status: str, s: dict):
    ok = "SAFE" in status
    bg = colors.HexColor("#D4EDDA") if ok else colors.HexColor("#F8D7DA")
    fg = GREEN if ok else ACCENT
    data = [[f"OVERALL DESIGN STATUS:   {status}"]]
    t = Table(data, colWidths=[PAGE_W - 2*MARGIN])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("TEXTCOLOR",     (0, 0), (-1, -1), fg),
        ("FONTNAME",      (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 12),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 1.5, fg),
    ]))
    return [Spacer(1, 6), t, Spacer(1, 8)]


# ============================================================
# PURLIN REPORT
# ============================================================
def generate_purlin_pdf(r: dict, project: str = "") -> bytes:
    buf = io.BytesIO()
    s   = _styles()
    doc = SimpleDocTemplate(buf, pagesize=A4,
          topMargin=MARGIN, bottomMargin=MARGIN,
          leftMargin=MARGIN, rightMargin=MARGIN)

    sp   = r["section_props"]
    cls  = r["section_class"]
    date = datetime.today().strftime("%d %b %Y")
    story = []

    # ── Header ─────────────────────────────────────────────
    story += _header_table("PURLIN DESIGN REPORT",
        "As per IS 800:2007 | IS 875 (Part 1, 2, 3) | SP 6(1):1964",
        project, date, s)

    # ── 1. Design Inputs ────────────────────────────────────
    story += _section_heading("1.  DESIGN INPUTS", s)
    rows = [
        ["Purlin Span (L)",                f"{r['span_m']:.2f} m"],
        ["Purlin Spacing (s)",              f"{r['spacing_m']:.2f} m"],
        ["Roof Slope (θ)",                  f"{r['slope_deg']:.1f}°"],
        ["Dead Load Intensity (DL)",        f"{r['dead_load']:.2f} kN/m²  [IS 875 Pt.1]"],
        ["Live / Imposed Load (LL)",        f"{r['live_load']:.2f} kN/m²  [IS 875 Pt.2]"],
        ["Design Wind Pressure (qd)",       f"{r['wind_pressure']:.2f} kN/m²  [IS 875 Pt.3]"],
        ["Ext. Pressure Coeff (Cpe)",       f"{r['Cpe']:.2f}"],
        ["Int. Pressure Coeff (Cpi)",       f"{r['Cpi']:.2f}"],
        ["Yield Strength (fy)",             f"{r['fy']:.0f} MPa  [IS 2062 E250]"],
        ["Partial Safety Factor (γm0)",     f"{r['gm0']:.2f}  [IS 800 Cl. 5.4.1]"],
        ["Modulus of Elasticity (E)",       f"2×10⁵ MPa"],
    ]
    story += _input_table(rows, s, "1.1  Loading & Material Data")

    sec_rows = [
        ["Section Designation",              r.get("section_name", "Unknown")],
        ["Cross-sectional Area (A)",         f"{sp.get('Area', 0.0):.2f} cm²"],
        ["Overall Depth (h)",                f"{sp.get('h', 0.0)} mm"],
        ["Flange Width (bf)",                f"{sp.get('bf', 0.0)} mm"],
        ["Flange Thickness (tf)",            f"{sp.get('tf', 0.0)} mm"],
        ["Web Thickness (tw)",               f"{sp.get('tw', 0.0)} mm"],
        ["Moment of Inertia Ixx (Izz)",      f"{sp.get('Ixx', 0.0):.1f} cm⁴"],
        ["Moment of Inertia Iyy",            f"{sp.get('Iyy', 0.0):.2f} cm⁴"],
        ["Elastic Mod. Zxx (Zzz)",           f"{sp.get('Zxx', 0.0):.2f} cm³"],
        ["Elastic Mod. Zyy",                 f"{sp.get('Zyy', 0.0):.2f} cm³"],
        ["Plastic Mod. Zpx",                 f"{sp.get('Zpx', 0.0):.2f} cm³"],
        ["Plastic Mod. Zpy",                 f"{sp.get('Zpy', 0.0):.2f} cm³"],
        ["Radius of Gyration rxx (rzz)",     f"{sp.get('rxx', 0.0):.2f} cm"],
        ["Radius of Gyration ryy",           f"{sp.get('ryy', 0.0):.2f} cm"],
        ["Self Weight",                      f"{sp.get('weight', 0.0):.1f} kg/m  [{r.get('sw_kNm', 0.0):.4f} kN/m]"],
    ]
    story += _input_table(sec_rows, s, "1.2  Section Properties  [Ref: SP 6(1):1964 / IS 808:1989]")

    # ── 2. Load Calculation ─────────────────────────────────
    story += _section_heading("2.  LOAD CALCULATION", s)

    story += _subheading("2.1  Distributed Loads on Purlin", s)
    story += [Paragraph(
        "Loads are resolved parallel (w<sub>y</sub>) and perpendicular (w<sub>z</sub>) "
        "to the roof slope to account for biaxial bending.", s["body"]),
        Spacer(1, 3)]

    story += _formula_block(
        "w_DL  = DL × s + SW  =  "
        f"{r['dead_load']:.2f} × {r['spacing_m']:.2f} + {r['sw_kNm']:.4f}  =  "
        f"{r['wz_DL']/math.cos(math.radians(r['slope_deg'])):.4f} kN/m  (total)",
        s, "IS 875 Pt.1")
    story += _formula_block(
        f"w_z,DL = w_DL × cos θ  =  {r['wz_DL']:.4f} kN/m  (perp. to slope → Mz)",
        s)
    story += _formula_block(
        f"w_y,DL = w_DL × sin θ  =  {r['wy_DL']:.4f} kN/m  (along slope → My)",
        s)
    story += _formula_block(
        f"w_z,LL = LL × s × cos θ  =  {r['wz_LL']:.4f} kN/m",
        s, "IS 875 Pt.2")
    story += _formula_block(
        f"w_y,LL = LL × s × sin θ  =  {r['wy_LL']:.4f} kN/m",
        s)
    story += _formula_block(
        f"w_wind = qd × (Cpe - Cpi) × s  =  {r['wind_pressure']:.2f} × "
        f"({r['Cpe']:.2f} - {r['Cpi']:.2f}) × {r['spacing_m']:.2f}  =  {r['w_wind']:.4f} kN/m",
        s, "IS 875 Pt.3")

    story += _subheading("2.2  Load Combinations  [IS 800:2007 Table 4 / IS 875 Pt.5]", s)
    combo_data = [
        ["Combo", "Description", "wz,d (kN/m)", "wy,d (kN/m)"],
        ["LC1", "1.5(DL + LL)",          f"{r['wz_1']:.4f}", f"{r['wy_1']:.4f}"],
        ["LC2", "1.2(DL + LL + Wind)",   f"{r['wz_2']:.4f}", f"{r['wy_2']:.4f}"],
        ["LC3", "0.9 DL + 1.5 Wind",     f"{r['wz_3']:.4f}", f"{r['wy_3']:.4f}"],
        ["DESIGN", "Max (Governing)", f"{r['wz_d']:.4f}", f"{r['wy_d']:.4f}"],
    ]
    cw2 = [(PAGE_W-2*MARGIN)*f for f in [0.12, 0.45, 0.22, 0.21]]
    tc2 = Table(combo_data, colWidths=cw2)
    tc2.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), MID_BLUE),
        ("TEXTCOLOR",   (0, 0), (-1, 0), WHITE),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",    (0, 4), (-1, 4), "Helvetica-Bold"),
        ("BACKGROUND",  (0, 4), (-1, 4), LIGHT_BLUE),
        ("FONTSIZE",    (0, 0), (-1, -1), 8.8),
        ("GRID",        (0, 0), (-1, -1), 0.4, GREY_MID),
        ("ROWBACKGROUNDS", (0, 1), (-1, 3), [WHITE, GREY_LIGHT, WHITE]),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("ALIGN",         (2, 0), (-1, -1), "CENTER"),
    ]))
    story += [tc2, Spacer(1, 6)]

    # ── 3. Section Classification ───────────────────────────
    story += _section_heading("3.  SECTION CLASSIFICATION  [IS 800:2007 Table 2]", s)
    eps = cls["epsilon"]
    story += _formula_block(
        f"ε  =  √(250/fy)  =  √(250/{r['fy']:.0f})  =  {eps:.4f}", s)
    story += _formula_block(
        f"Outstand flange ratio:  b/tf  =  (bf/2 - tw/2) / tf  =  "
        f"({sp['bf']}/2 - {sp['tw']}/2) / {sp['tf']}  =  {cls['b_tf']:.2f}\n"
        f"   Plastic limit: 9.4ε = {cls['limits']['flange'][0]:.2f}  |  "
        f"Compact: {cls['limits']['flange'][1]:.2f}  |  "
        f"Semi-compact: {cls['limits']['flange'][2]:.2f}\n"
        f"   → Flange Classification: {cls['flange_class']}",
        s)
    story += _formula_block(
        f"Web ratio:  d/tw  =  (h - 2tf) / tw  =  "
        f"({sp['h']} - 2×{sp['tf']}) / {sp['tw']}  =  {cls['d_tw']:.2f}\n"
        f"   Plastic limit: 84ε = {cls['limits']['web'][0]:.2f}  |  "
        f"Compact: {cls['limits']['web'][1]:.2f}  |  "
        f"Semi-compact: {cls['limits']['web'][2]:.2f}\n"
        f"   → Web Classification: {cls['web_class']}",
        s)
    story += _result_box(
        f"Overall Section Classification", cls["overall"],
        cls["overall"] != "Slender", s)

    # ── 4. Design Bending Moments ───────────────────────────
    story += _section_heading("4.  DESIGN BENDING MOMENTS & SHEAR", s)
    story += _formula_block(
        f"Mz  =  wz,d × L² / 8  =  {r['wz_d']:.4f} × {r['span_m']:.2f}² / 8  =  {r['Mz_kNm']:.4f} kNm",
        s, "IS 800 Cl. 8.2.1")
    story += _formula_block(
        f"My  =  wy,d × L² / 8  =  {r['wy_d']:.4f} × {r['span_m']:.2f}² / 8  =  {r['My_kNm']:.4f} kNm",
        s)
    story += _formula_block(
        f"Vz  =  wz,d × L / 2  =  {r['wz_d']:.4f} × {r['span_m']:.2f} / 2  =  {r['Vz_kN']:.4f} kN",
        s)

    # ── 5. Moment Capacity ──────────────────────────────────
    story += _section_heading("5.  DESIGN MOMENT CAPACITY  [IS 800:2007 Cl. 8.2.1]", s)
    section_class_label = cls["overall"]
    if section_class_label in ("Plastic", "Compact"):
        story += [Paragraph(
            f"Section is <b>{section_class_label}</b> → use plastic section modulus (Zpx, Zpy).",
            s["body"]), Spacer(1, 3)]
        story += _formula_block(
            f"Mdz  =  βb × Zpx × fy / γm0  =  1.0 × {sp['Zpx']:.2f} × {r['fy']:.0f} / "
            f"({r['gm0']:.2f} × 1000)  =  {r['Mdz_kNm']:.4f} kNm",
            s, "IS 800 Cl. 8.2.1.2")
        story += _formula_block(
            f"Mdy  =  βb × Zpy × fy / γm0  =  1.0 × {sp['Zpy']:.2f} × {r['fy']:.0f} / "
            f"({r['gm0']:.2f} × 1000)  =  {r['Mdy_kNm']:.4f} kNm",
            s)
    else:
        story += [Paragraph(
            f"Section is <b>Semi-compact</b> → use elastic section modulus (Zxx, Zyy).",
            s["body"]), Spacer(1, 3)]
        story += _formula_block(
            f"Mdz  =  Zxx × fy / γm0  =  {sp['Zxx']:.2f} × {r['fy']:.0f} / "
            f"({r['gm0']:.2f} × 1000)  =  {r['Mdz_kNm']:.4f} kNm",
            s)
        story += _formula_block(
            f"Mdy  =  Zyy × fy / γm0  =  {sp['Zyy']:.2f} × {r['fy']:.0f} / "
            f"({r['gm0']:.2f} × 1000)  =  {r['Mdy_kNm']:.4f} kNm",
            s)

    # ── 6. Biaxial Bending Check ────────────────────────────
    story += _section_heading("6.  BIAXIAL BENDING CHECK  [IS 800:2007 Cl. 9.3.1.1]", s)
    story += _formula_block(
        "My / Mdy  +  Mz / Mdz  ≤  1.0", s)
    story += _formula_block(
        f"{r['My_kNm']:.4f} / {r['Mdy_kNm']:.4f}  +  "
        f"{r['Mz_kNm']:.4f} / {r['Mdz_kNm']:.4f}  =  {r['biaxial_ratio']:.4f}",
        s)
    story += _result_box(
        f"Biaxial Bending  My/Mdy + Mz/Mdz",
        f"{r['biaxial_ratio']:.4f}  ≤  1.0",
        r["biaxial_ok"], s)

    # ── 7. Shear Check ──────────────────────────────────────
    story += _section_heading("7.  SHEAR CAPACITY CHECK  [IS 800:2007 Cl. 8.4.1]", s)
    story += _formula_block(
        f"Shear Area:  Av  =  h × tw  =  {sp['h']} × {sp['tw']}  =  {r['Av_mm2']:.0f} mm²",
        s, "IS 800 Cl. 8.4.1")
    story += _formula_block(
        f"Vd  =  Av × fy / (√3 × γm0)  =  "
        f"{r['Av_mm2']:.0f} × {r['fy']:.0f} / (√3 × {r['gm0']:.2f} × 1000)  =  "
        f"{r['Vd_kN']:.4f} kN",
        s)
    story += _result_box(
        f"Shear Check  Vz = {r['Vz_kN']:.4f} kN  ≤  Vd = {r['Vd_kN']:.4f} kN",
        f"{r['Vz_kN']:.4f} / {r['Vd_kN']:.4f} = {r['Vz_kN']/r['Vd_kN']:.4f}",
        r["shear_ok"], s)

    # ── 8. Deflection Check ─────────────────────────────────
    story += _section_heading("8.  DEFLECTION CHECK  [IS 800:2007 Table 6]", s)
    story += _formula_block(
        f"δ_max  =  5 w L⁴ / (384 E I)  =  "
        f"5 × {(r['wz_DL']+r['wz_LL']):.4f} × ({r['span_m']*1000:.0f})⁴ / "
        f"(384 × 2×10⁵ × {sp['Ixx']:.1f}×10⁴)  =  {r['delta_max_mm']:.3f} mm",
        s, "IS 800 Table 6")
    story += _formula_block(
        f"Permissible deflection:  L/180  =  {r['span_m']*1000:.0f} / 180  =  "
        f"{r['delta_limit_mm']:.3f} mm",
        s)
    story += _result_box(
        f"Deflection Check  δ = {r['delta_max_mm']:.3f} mm  ≤  L/180 = {r['delta_limit_mm']:.3f} mm",
        f"{r['delta_max_mm']:.3f} / {r['delta_limit_mm']:.3f} = "
        f"{r['delta_max_mm']/r['delta_limit_mm']:.4f}",
        r["defl_ok"], s)

    # ── Overall Verdict ─────────────────────────────────────
    story += _overall_verdict(r["overall_status"], s)

    # ── References ──────────────────────────────────────────
    story += _section_heading("REFERENCES", s)
    refs = [
        "IS 800:2007 — Code of Practice for General Construction in Steel (3rd Revision), BIS New Delhi",
        "IS 875 (Part 1):1987 — Code of Practice for Design Loads: Dead Loads, BIS",
        "IS 875 (Part 2):1987 — Code of Practice for Design Loads: Imposed Loads, BIS",
        "IS 875 (Part 3):2015 — Code of Practice for Design Loads: Wind Loads, BIS",
        "SP 6(1):1964 — Handbook for Structural Engineers, Structural Steel Sections, BIS",
        "IS 808:1989 — Dimensions for Hot Rolled Steel Beam, Column, Channel and Angle Sections, BIS",
        "IS 2062:2011 — Hot Rolled Medium and High Tensile Structural Steel Specification, BIS",
    ]
    for ref in refs:
        story.append(Paragraph(f"• {ref}", s["ref"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Generated by IS Steel Design Suite | For engineering use only — verify against current code provisions.",
        s["footer"]))

    doc.build(story)
    return buf.getvalue()


# ============================================================
# GIRT REPORT
# ============================================================
def generate_girt_pdf(r: dict, project: str = "") -> bytes:
    buf = io.BytesIO()
    s   = _styles()
    doc = SimpleDocTemplate(buf, pagesize=A4,
          topMargin=MARGIN, bottomMargin=MARGIN,
          leftMargin=MARGIN, rightMargin=MARGIN)

    sp   = r["section_props"]
    cls  = r["section_class"]
    date = datetime.today().strftime("%d %b %Y")
    story = []

    story += _header_table("GIRT DESIGN REPORT",
        "As per IS 800:2007 | IS 875 (Part 1, 3) | SP 6(1):1964",
        project, date, s)

    # ── 1. Inputs ────────────────────────────────────────────
    story += _section_heading("1.  DESIGN INPUTS", s)
    rows = [
        ["Girt Span (L)",                   f"{r['span_m']:.2f} m"],
        ["Girt Spacing (s)",                f"{r['spacing_m']:.2f} m"],
        ["Cladding Dead Load (DL)",         f"{r['dead_load']:.2f} kN/m²  [IS 875 Pt.1]"],
        ["Design Wind Pressure (qd)",       f"{r['wind_pressure']:.2f} kN/m²  [IS 875 Pt.3]"],
        ["External Pressure Coeff (Cpe)",   f"{r['Cpe']:.2f}"],
        ["Internal Pressure Coeff (Cpi)",   f"{r['Cpi']:.2f}"],
        ["Net Cpe − Cpi (inward)",          f"{r['Cp_net_max']:.3f}"],
        ["Yield Strength (fy)",             f"{r['fy']:.0f} MPa"],
        ["Partial Safety Factor (γm0)",     f"{r['gm0']:.2f}"],
    ]
    story += _input_table(rows, s, "1.1  Loading & Material Data")

    sec_rows = [
        ["Section Designation",             r["section_name"]],
        ["Cross-sectional Area (A)",        f"{sp['Area']:.2f} cm²"],
        ["h × bf × tf × tw",               f"{sp['h']} × {sp['bf']} × {sp['tf']} × {sp['tw']} mm"],
        ["Ixx (cm⁴)",                       f"{sp['Ixx']:.2f}"],
        ["Iyy (cm⁴)",                       f"{sp['Iyy']:.2f}"],
        ["Zpx / Zpy (cm³)",                 f"{sp['Zpx']:.2f} / {sp['Zpy']:.2f}"],
        ["Self Weight",                     f"{sp['weight']:.1f} kg/m ({r['sw_kNm']:.4f} kN/m)"],
    ]
    story += _input_table(sec_rows, s, "1.2  Section Properties  [SP 6(1):1964]")

    # ── 2. Load Calculation ──────────────────────────────────
    story += _section_heading("2.  LOAD CALCULATION  [IS 875 Pt.3, Cl. 6.2]", s)
    story += [Paragraph(
        "For wall girts, <b>major-axis bending (Mz)</b> is caused by horizontal wind load "
        "(perpendicular to wall), and <b>minor-axis bending (My)</b> by vertical cladding "
        "dead load (gravity).", s["body"]), Spacer(1, 4)]

    story += _formula_block(
        f"w_DL  =  DL × s + SW  =  {r['dead_load']:.2f} × {r['spacing_m']:.2f} + "
        f"{r['sw_kNm']:.4f}  =  {r['w_DL']:.4f} kN/m  (vertical → My)",
        s, "IS 875 Pt.1")
    story += _formula_block(
        f"w_wind,max  =  qd × (Cpe − Cpi) × s  =  {r['wind_pressure']:.2f} × "
        f"{r['Cp_net_max']:.3f} × {r['spacing_m']:.2f}  =  {r['w_wind_max']:.4f} kN/m  (inward → Mz)",
        s, "IS 875 Pt.3")
    story += _formula_block(
        f"w_wind,suc  =  qd × |Cpe + Cpi| × s  =  {r['w_wind_suc']:.4f} kN/m  (suction)",
        s)

    combo_data = [
        ["Combo", "Description",                  "wz,d (kN/m)", "wy,d (kN/m)"],
        ["LC1", "1.5(DL + Wind inward)",           f"{r['wz_1']:.4f}", f"{r['wy_1']:.4f}"],
        ["LC2", "1.5(DL + Wind suction)",          f"{r['wz_2']:.4f}", f"{r['wy_2']:.4f}"],
        ["LC3", "0.9 DL + 1.5 Wind suction",       f"{r['wz_3']:.4f}", f"{r['wy_3']:.4f}"],
        ["DESIGN", "Governing",                    f"{r['wz_d']:.4f}", f"{r['wy_d']:.4f}"],
    ]
    cw2 = [(PAGE_W-2*MARGIN)*f for f in [0.12, 0.45, 0.22, 0.21]]
    tc2 = Table(combo_data, colWidths=cw2)
    tc2.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1, 0), MID_BLUE),
        ("TEXTCOLOR",      (0, 0), (-1, 0), WHITE),
        ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME",       (0, 4), (-1, 4), "Helvetica-Bold"),
        ("BACKGROUND",     (0, 4), (-1, 4), LIGHT_BLUE),
        ("FONTSIZE",       (0, 0), (-1, -1), 8.8),
        ("GRID",           (0, 0), (-1, -1), 0.4, GREY_MID),
        ("ROWBACKGROUNDS", (0, 1), (-1, 3), [WHITE, GREY_LIGHT, WHITE]),
        ("TOPPADDING",     (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 4),
        ("ALIGN",          (2, 0), (-1, -1), "CENTER"),
    ]))
    story += [tc2, Spacer(1, 6)]

    # ── 3. Section Classification ────────────────────────────
    story += _section_heading("3.  SECTION CLASSIFICATION  [IS 800:2007 Table 2]", s)
    story += _formula_block(
        f"ε  =  √(250/{r['fy']:.0f})  =  {cls['epsilon']:.4f}", s)
    story += _formula_block(
        f"b/tf  =  {cls['b_tf']:.2f}  →  {cls['flange_class']}  "
        f"(limits: {cls['limits']['flange'][0]:.2f} / {cls['limits']['flange'][1]:.2f} / {cls['limits']['flange'][2]:.2f})", s)
    story += _formula_block(
        f"d/tw  =  {cls['d_tw']:.2f}  →  {cls['web_class']}  "
        f"(limits: {cls['limits']['web'][0]:.2f} / {cls['limits']['web'][1]:.2f} / {cls['limits']['web'][2]:.2f})", s)
    story += _result_box("Section Classification", cls["overall"], cls["overall"] != "Slender", s)

    # ── 4. BM & Shear ────────────────────────────────────────
    story += _section_heading("4.  DESIGN BENDING MOMENTS & SHEAR", s)
    story += _formula_block(
        f"Mz  =  wz,d × L²/8  =  {r['wz_d']:.4f} × {r['span_m']:.2f}²/8  =  {r['Mz_kNm']:.4f} kNm",
        s)
    story += _formula_block(
        f"My  =  wy,d × L²/8  =  {r['wy_d']:.4f} × {r['span_m']:.2f}²/8  =  {r['My_kNm']:.4f} kNm",
        s)

    # ── 5. Moment Capacity ───────────────────────────────────
    story += _section_heading("5.  DESIGN MOMENT CAPACITY  [IS 800:2007 Cl. 8.2.1]", s)
    if cls["overall"] in ("Plastic", "Compact"):
        story += _formula_block(
            f"Mdz  =  Zpx × fy / γm0  =  {sp['Zpx']:.2f} × {r['fy']:.0f} / ({r['gm0']:.2f}×1000)  =  {r['Mdz_kNm']:.4f} kNm",
            s)
        story += _formula_block(
            f"Mdy  =  Zpy × fy / γm0  =  {sp['Zpy']:.2f} × {r['fy']:.0f} / ({r['gm0']:.2f}×1000)  =  {r['Mdy_kNm']:.4f} kNm",
            s)
    else:
        story += _formula_block(
            f"Mdz  =  Zxx × fy / γm0  =  {sp['Zxx']:.2f} × {r['fy']:.0f} / ({r['gm0']:.2f}×1000)  =  {r['Mdz_kNm']:.4f} kNm",
            s)
        story += _formula_block(
            f"Mdy  =  Zyy × fy / γm0  =  {sp['Zyy']:.2f} × {r['fy']:.0f} / ({r['gm0']:.2f}×1000)  =  {r['Mdy_kNm']:.4f} kNm",
            s)

    # ── 6. Biaxial ────────────────────────────────────────────
    story += _section_heading("6.  BIAXIAL BENDING CHECK  [IS 800:2007 Cl. 9.3.1.1]", s)
    story += _formula_block("My/Mdy  +  Mz/Mdz  ≤  1.0", s)
    story += _formula_block(
        f"{r['My_kNm']:.4f}/{r['Mdy_kNm']:.4f}  +  {r['Mz_kNm']:.4f}/{r['Mdz_kNm']:.4f}  =  {r['biaxial_ratio']:.4f}",
        s)
    story += _result_box(
        "Biaxial Bending  My/Mdy + Mz/Mdz",
        f"{r['biaxial_ratio']:.4f}  ≤  1.0", r["biaxial_ok"], s)

    # ── 7. Shear ──────────────────────────────────────────────
    story += _section_heading("7.  SHEAR CAPACITY  [IS 800:2007 Cl. 8.4.1]", s)
    story += _formula_block(
        f"Av  =  h × tw  =  {sp['h']} × {sp['tw']}  =  {r['Av_mm2']:.0f} mm²", s)
    story += _formula_block(
        f"Vd  =  Av × fy / (√3 × γm0)  =  "
        f"{r['Av_mm2']:.0f} × {r['fy']:.0f} / (√3 × {r['gm0']:.2f} × 1000)  =  {r['Vd_kN']:.4f} kN",
        s)
    story += _result_box(
        f"Shear  Vz = {r['Vz_kN']:.4f} kN  ≤  Vd = {r['Vd_kN']:.4f} kN",
        f"{r['Vz_kN']:.4f}/{r['Vd_kN']:.4f} = {r['Vz_kN']/r['Vd_kN']:.4f}",
        r["shear_ok"], s)

    # ── 8. Deflection ─────────────────────────────────────────
    story += _section_heading("8.  DEFLECTION CHECK  [IS 800:2007 Table 6]", s)
    story += _formula_block(
        f"δ  =  5wL⁴/(384EI)  =  5×{r['w_wind_max']:.4f}×({r['span_m']*1000:.0f})⁴ / "
        f"(384×2×10⁵×{sp['Ixx']:.1f}×10⁴)  =  {r['delta_max_mm']:.3f} mm",
        s, "IS 800 Table 6")
    story += _formula_block(
        f"Limit: L/150  =  {r['span_m']*1000:.0f}/150  =  {r['delta_limit_mm']:.3f} mm",
        s)
    story += _result_box(
        f"Deflection δ = {r['delta_max_mm']:.3f} mm  ≤  L/150 = {r['delta_limit_mm']:.3f} mm",
        f"{r['delta_max_mm']:.3f}/{r['delta_limit_mm']:.3f} = {r['delta_max_mm']/r['delta_limit_mm']:.4f}",
        r["defl_ok"], s)

    story += _overall_verdict(r["overall_status"], s)

    story += _section_heading("REFERENCES", s)
    refs = [
        "IS 800:2007 — Code of Practice for General Construction in Steel, BIS New Delhi",
        "IS 875 (Part 1):1987 — Dead Loads, BIS", "IS 875 (Part 3):2015 — Wind Loads, BIS",
        "SP 6(1):1964 — Handbook for Structural Engineers: Structural Steel Sections, BIS",
    ]
    for ref in refs:
        story.append(Paragraph(f"• {ref}", s["ref"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Generated by IS Steel Design Suite | For engineering use only.",
        s["footer"]))

    doc.build(story)
    return buf.getvalue()


# ============================================================
# COLUMN REPORT
# ============================================================
def generate_column_pdf(r: dict, project: str = "") -> bytes:
    buf = io.BytesIO()
    s   = _styles()
    doc = SimpleDocTemplate(buf, pagesize=A4,
          topMargin=MARGIN, bottomMargin=MARGIN,
          leftMargin=MARGIN, rightMargin=MARGIN)

    sp   = r["section_props"]
    cls  = r["section_class"]
    date = datetime.today().strftime("%d %b %Y")
    story = []

    story += _header_table("STEEL COLUMN DESIGN REPORT",
        "As per IS 800:2007, Chapter 7 & 9 | SP 6(1):1964",
        project, date, s)

    # ── 1. Inputs ─────────────────────────────────────────────
    story += _section_heading("1.  DESIGN INPUTS", s)
    rows = [
        ["Factored Axial Load (P)",          f"{r['P_kN']:.2f} kN"],
        ["Applied Moment Mz (major axis)",   f"{r['Mz_app']:.2f} kNm"],
        ["Applied Moment My (minor axis)",   f"{r['My_app']:.2f} kNm"],
        ["Effective Length KLz (z-z axis)",  f"{r['KLz_mm']/1000:.2f} m"],
        ["Effective Length KLy (y-y axis)",  f"{r['KLy_mm']/1000:.2f} m"],
        ["Yield Strength (fy)",              f"{r['fy']:.0f} MPa"],
        ["Modulus of Elasticity (E)",        f"2×10⁵ MPa"],
        ["Partial Safety Factor (γm0)",      f"{r['gm0']:.2f}  [IS 800 Cl.5.4.1]"],
        ["Cm factor (z-axis)",               f"{r['Cmz']:.2f}"],
        ["Cm factor (y-axis)",               f"{r['Cmy']:.2f}"],
    ]
    story += _input_table(rows, s, "1.1  Load & Material Data")

    sec_rows = [
        ["Section Designation",             r["section_name"]],
        ["Section Type",                    r["section_type"]],
        ["Area (A)",                        f"{r['A_mm2']:.2f} mm²  ({sp['Area']:.2f} cm²)"],
        ["h × bf × tf × tw",               f"{sp['h']} × {sp['bf']} × {sp['tf']} × {sp['tw']} mm"],
        ["Ixx / Iyy (cm⁴)",                f"{sp['Ixx']:.2f} / {sp['Iyy']:.2f}"],
        ["rxx (rzz) / ryy (cm)",            f"{sp['rxx']:.2f} / {sp['ryy']:.2f}"],
        ["rz (mm) / ry (mm)",              f"{r['rz_mm']:.2f} / {r['ry_mm']:.2f}"],
        ["Zpx / Zpy (cm³)",                f"{sp['Zpx']:.2f} / {sp['Zpy']:.2f}"],
        ["Zxx / Zyy (cm³)",                f"{sp['Zxx']:.2f} / {sp['Zyy']:.2f}"],
        ["Self Weight",                    f"{sp['weight']:.1f} kg/m"],
    ]
    story += _input_table(sec_rows, s, "1.2  Section Properties  [SP 6(1):1964]")

    # ── 2. Section Classification ────────────────────────────
    story += _section_heading("2.  SECTION CLASSIFICATION  [IS 800:2007 Table 2]", s)
    story += _formula_block(
        f"ε  =  √(250/fy)  =  √(250/{r['fy']:.0f})  =  {cls['epsilon']:.4f}", s)
    story += _formula_block(
        f"Outstand flange b/tf  =  {cls['b_tf']:.2f}  →  {cls['flange_class']}  "
        f"(Plastic ≤ {cls['limits']['flange'][0]:.2f}ε; Compact ≤ {cls['limits']['flange'][1]:.2f}ε)", s)
    story += _formula_block(
        f"Web d/tw  =  {cls['d_tw']:.2f}  →  {cls['web_class']}  "
        f"(Plastic ≤ {cls['limits']['web'][0]:.2f}ε; Compact ≤ {cls['limits']['web'][1]:.2f}ε)", s)
    story += _result_box("Section Classification", cls["overall"], cls["overall"] != "Slender", s)

    # ── 3. Slenderness ────────────────────────────────────────
    story += _section_heading("3.  SLENDERNESS RATIO CHECK  [IS 800:2007 Cl. 7.3.2]", s)
    story += _formula_block(
        f"λ_z  =  KLz / rz  =  {r['KLz_mm']:.0f} / {r['rz_mm']:.2f}  =  {r['lambda_z']:.2f}",
        s, "IS 800 Cl. 7.1.2")
    story += _formula_block(
        f"λ_y  =  KLy / ry  =  {r['KLy_mm']:.0f} / {r['ry_mm']:.2f}  =  {r['lambda_y']:.2f}",
        s)
    story += _formula_block(
        f"λ_max  =  max(λ_z, λ_y)  =  {r['lambda_max']:.2f}  ≤  limit 180",
        s)
    story += _result_box(
        f"Slenderness  λ_max = {r['lambda_max']:.2f}  ≤  180",
        f"{r['lambda_max']:.2f} / 180 = {r['lambda_max']/180:.3f}",
        r["slender_ok"], s)

    # ── 4. Euler Critical Stress ──────────────────────────────
    story += _section_heading("4.  EULER CRITICAL STRESS  [IS 800:2007 Cl. 7.1.2]", s)
    story += _formula_block(
        f"fcc,z  =  π² E / λ_z²  =  π² × 2×10⁵ / {r['lambda_z']:.2f}²  =  {r['fcc_z']:.3f} MPa",
        s)
    story += _formula_block(
        f"fcc,y  =  π² E / λ_y²  =  π² × 2×10⁵ / {r['lambda_y']:.2f}²  =  {r['fcc_y']:.3f} MPa",
        s)

    # ── 5. Non-dimensional Slenderness ────────────────────────
    story += _section_heading("5.  NON-DIMENSIONAL SLENDERNESS  [IS 800:2007 Cl. 7.1.2]", s)
    story += _formula_block(
        f"λ̄_z  =  √(fy / fcc,z)  =  √({r['fy']:.0f} / {r['fcc_z']:.3f})  =  {r['lam_bar_z']:.4f}",
        s)
    story += _formula_block(
        f"λ̄_y  =  √(fy / fcc,y)  =  √({r['fy']:.0f} / {r['fcc_y']:.3f})  =  {r['lam_bar_y']:.4f}",
        s)

    # ── 6. Buckling Curves ────────────────────────────────────
    story += _section_heading("6.  BUCKLING CURVE SELECTION  [IS 800:2007 Table 10]", s)
    story += [Paragraph(
        f"Section type: <b>{r['section_type']}</b>  →  "
        f"z-z axis: Curve <b>{r['curve_z'].upper()}</b> (α = {r['alpha_z']})  |  "
        f"y-y axis: Curve <b>{r['curve_y'].upper()}</b> (α = {r['alpha_y']})  "
        f"[IS 800:2007 Table 7]",
        s["body"]), Spacer(1, 4)]

    curve_data = [
        ["Curve", "Imperfection Factor α", "Application (typical)"],
        ["a", "0.21", "Hot-finished CHS/SHS; ISHB z-z"],
        ["b", "0.34", "Welded I-sections (thick flanges); ISMB/ISLB z-z; ISHB y-y"],
        ["c", "0.49", "ISMB/ISLB y-y; ISMC; welded box sections"],
        ["d", "0.76", "Solid sections; welded I-sections (thin flanges)"],
    ]
    cw_c = [(PAGE_W-2*MARGIN)*f for f in [0.12, 0.28, 0.60]]
    tc_curve = Table(curve_data, colWidths=cw_c)
    tc_curve.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), MID_BLUE),
        ("TEXTCOLOR",   (0, 0), (-1, 0), WHITE),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8.5),
        ("GRID",        (0, 0), (-1, -1), 0.4, GREY_MID),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, GREY_LIGHT, WHITE, GREY_LIGHT]),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story += [tc_curve, Spacer(1, 5)]

    # ── 7. Stress Reduction Factor ────────────────────────────
    story += _section_heading("7.  STRESS REDUCTION FACTOR (χ)  [IS 800:2007 Cl. 7.1.2]", s)
    for axis, lam, phi, chi, alpha, curve in [
        ("z-z", r["lam_bar_z"], r["phi_z"], r["chi_z"], r["alpha_z"], r["curve_z"]),
        ("y-y", r["lam_bar_y"], r["phi_y"], r["chi_y"], r["alpha_y"], r["curve_y"]),
    ]:
        story += [Paragraph(f"<b>Axis {axis}  (Curve {curve.upper()},  α = {alpha})</b>", s["body"])]
        story += _formula_block(
            f"φ_{axis[:1]}  =  0.5 [1 + α(λ̄ − 0.2) + λ̄²]\n"
            f"     =  0.5 [1 + {alpha}×({lam:.4f}−0.2) + {lam:.4f}²]  =  {phi:.4f}",
            s)
        story += _formula_block(
            f"χ_{axis[:1]}  =  1 / (φ + √(φ² − λ̄²))\n"
            f"     =  1 / ({phi:.4f} + √({phi:.4f}² − {lam:.4f}²))  =  {chi:.4f}",
            s)

    story += [Paragraph(
        f"Governing axis: <b>{r['governing_axis']}</b>  →  χ_min  =  <b>{r['chi_min']:.4f}</b>",
        s["body"]), Spacer(1, 4)]

    # ── 8. Design Compressive Strength ───────────────────────
    story += _section_heading("8.  DESIGN COMPRESSIVE STRENGTH  [IS 800:2007 Cl. 7.1.2]", s)
    story += _formula_block(
        f"fcd  =  χ_min × fy / γm0  =  {r['chi_min']:.4f} × {r['fy']:.0f} / {r['gm0']:.2f}  =  {r['fcd']:.3f} MPa",
        s)
    story += _formula_block(
        f"Pd   =  fcd × A  =  {r['fcd']:.3f} × {r['A_mm2']:.2f} / 1000  =  {r['Pd_kN']:.3f} kN",
        s)
    story += _result_box(
        f"Axial Check  P = {r['P_kN']:.2f} kN  ≤  Pd = {r['Pd_kN']:.3f} kN",
        f"P/Pd  =  {r['axial_ratio']:.4f}",
        r["axial_ok"], s)

    # ── 9. Combined Axial + Bending ───────────────────────────
    if r["has_moments"]:
        story += _section_heading("9.  COMBINED AXIAL FORCE + BENDING  [IS 800:2007 Cl. 9.3.2.2]", s)
        story += [Paragraph(
            "Interaction formula for beam-column with axial compression and biaxial bending:",
            s["body"]), Spacer(1, 3)]
        story += _formula_block(
            "P/Pd  +  (Cmz × Mz) / [Mdz × (1 − P/Pez)]  +  (Cmy × My) / [Mdy × (1 − P/Pey)]  ≤  1.0",
            s, "IS 800:2007 Cl. 9.3.2.2")
        story += _formula_block(
            f"Pez  =  π²EIzz / (KLz)²  =  π²×2×10⁵×{sp['Ixx']:.2f}×10⁴ / ({r['KLz_mm']:.0f})²  =  {r['Pez_kN']:.3f} kN",
            s)
        story += _formula_block(
            f"Pey  =  π²EIyy / (KLy)²  =  π²×2×10⁵×{sp['Iyy']:.2f}×10⁴ / ({r['KLy_mm']:.0f})²  =  {r['Pey_kN']:.3f} kN",
            s)
        story += _formula_block(
            f"Mdz  =  {r['Mdz_kNm']:.3f} kNm  |  Mdy  =  {r['Mdy_kNm']:.3f} kNm\n"
            f"Cmz = {r['Cmz']:.2f}  |  Cmy = {r['Cmy']:.2f}",
            s)
        story += _formula_block(
            f"Interaction ratio  =  {r['P_kN']:.2f}/{r['Pd_kN']:.3f}  +  "
            f"({r['Cmz']:.2f}×{r['Mz_app']:.2f})/[{r['Mdz_kNm']:.3f}×(1−{r['P_kN']:.2f}/{r['Pez_kN']:.3f})]  +  "
            f"({r['Cmy']:.2f}×{r['My_app']:.2f})/[{r['Mdy_kNm']:.3f}×(1−{r['P_kN']:.2f}/{r['Pey_kN']:.3f})]"
            f"\n     =  {r['combined_ratio']:.4f}",
            s)
        story += _result_box(
            "Combined Interaction Ratio",
            f"{r['combined_ratio']:.4f}  ≤  1.0",
            r["combined_ok"], s)
    else:
        story += _section_heading("9.  COMBINED AXIAL FORCE + BENDING  [IS 800:2007 Cl. 9.3.2.2]", s)
        story += [Paragraph("No applied moments — combined check not required.", s["body"]), Spacer(1,4)]

    story += _overall_verdict(r["overall_status"], s)

    story += _section_heading("REFERENCES", s)
    refs = [
        "IS 800:2007 — Code of Practice for General Construction in Steel, BIS New Delhi",
        "SP 6(1):1964 — Handbook for Structural Engineers: Structural Steel Sections, BIS",
        "IS 808:1989 — Dimensions for Hot Rolled Steel Sections, BIS",
        "IS 2062:2011 — Hot Rolled Structural Steel Specification, BIS",
    ]
    for ref in refs:
        story.append(Paragraph(f"• {ref}", s["ref"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "Generated by IS Steel Design Suite | For engineering use only — verify against current code provisions.",
        s["footer"]))

    doc.build(story)
    return buf.getvalue()
