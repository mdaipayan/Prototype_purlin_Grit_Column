"""
Page 1 — Purlin Design
IS 800:2007 + IS 875 (Part 1, 2, 3)
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import streamlit as st
import pandas as pd
from utils.sections import ISMB, ISLB, ISMC, ALL_SECTIONS
from utils.purlin_calc import run_purlin_design
from utils.pdf_report import generate_purlin_pdf

st.set_page_config(page_title="Purlin Design | IS 800:2007", page_icon="📐", layout="wide")

st.markdown("""
<style>
.step-header{background:#1A3557;color:white;padding:7px 14px;border-radius:5px;
             font-weight:700;margin:14px 0 6px 0;font-size:.97rem;}
.formula-box{background:#F0F4FA;border:1px solid #B8D0EA;border-radius:6px;
             padding:10px 14px;font-family:'Courier New',monospace;
             font-size:.87rem;color:#1A3557;margin:6px 0;white-space:pre-wrap;}
.result-safe{background:#E6F4ED;border-left:5px solid #1A7A4A;
             padding:10px 14px;border-radius:5px;margin:6px 0;}
.result-fail{background:#FDECEA;border-left:5px solid #E84040;
             padding:10px 14px;border-radius:5px;margin:6px 0;}
.ref-tag{color:#2E6DA4;font-size:.79rem;font-style:italic;}
section[data-testid="stSidebar"]{background:linear-gradient(160deg,#1A3557,#2E6DA4);}
section[data-testid="stSidebar"] *{color:#FFF!important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:linear-gradient(90deg,#1A3557,#2E6DA4);padding:22px 26px;border-radius:14px;margin-bottom:14px;color:white;">
  <h1 style="margin:0;color:white;">📐 Purlin Design — IS 800:2007</h1>
  <p style="margin:6px 0 0;color:#D6E8F7;">Step-by-step roof purlin loading, biaxial bending, shear, deflection, and PDF report generation.</p>
</div>
""", unsafe_allow_html=True)
st.caption("Loading: IS 875 Pt.1 (DL) + Pt.2 (LL) + Pt.3 (Wind)  |  "
           "Section check: IS 800:2007 Cl. 8.2.1, 9.3.1.1, 8.4.1  |  "
           "Sections: SP 6(1):1964 / IS 808:1989")

# ── Sidebar — Project info ─────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/a/a8/Bureau_of_Indian_Standards_%28BIS%29_Logo.svg/220px-Bureau_of_Indian_Standards_%28BIS%29_Logo.svg.png", width=80)
    st.markdown("### Purlin Design")
    st.markdown("**References**")
    st.markdown("- IS 800:2007 Cl. 8.2.1\n- IS 800:2007 Cl. 9.3.1.1\n- IS 800:2007 Cl. 8.4.1\n- IS 875 Pt.1/2/3\n- SP 6(1):1964")
    project_name = st.text_input("Project Name", "My Project")

# ── Input Columns ──────────────────────────────────────────────────────────
st.markdown("### 🔢 Design Inputs")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("**Geometry**")
    span    = st.number_input("Span L (m)", 1.0, 20.0, 5.0, 0.25, help="Purlin span between supports (m)")
    spacing = st.number_input("Purlin Spacing (m)", 0.5, 5.0, 1.5, 0.25, help="Centre-to-centre spacing of purlins (m)")
    slope   = st.number_input("Roof Slope θ (°)", 0.0, 45.0, 10.0, 0.5, help="Inclination of roof surface with horizontal")

with c2:
    st.markdown("**Loading  (IS 875)**")
    dead_load = st.number_input("Dead Load (kN/m²)", 0.1, 3.0, 0.55, 0.05, help="Roofing + insulation (excluding purlin self-wt)")
    live_load = st.number_input("Live Load (kN/m²)", 0.0, 2.0, 0.75, 0.05, help="IS 875 Pt.2: 0.75 kN/m² for slopes ≤ 10°")
    wind_pres = st.number_input("Design Wind Pressure qd (kN/m²)", 0.1, 3.0, 0.70, 0.05, help="Design wind pressure from IS 875 Pt.3 Cl.5.4")
    Cpe       = st.number_input("Ext. Pressure Coeff Cpe", -2.0, 2.0, -0.8, 0.05, help="For roof: typically −0.8 (suction) on windward slope")
    Cpi       = st.number_input("Int. Pressure Coeff Cpi", -0.5, 0.5, 0.2, 0.05, help="Dominant openings: +0.2 or −0.2 per IS 875 Pt.3")

with c3:
    st.markdown("**Material & Section**")
    fy  = st.selectbox("Steel Grade fy (MPa)", [250, 345, 410], index=0, help="IS 2062: E250=250 MPa, E350=345 MPa, E410=410 MPa")
    gm0 = st.number_input("γm0", 1.00, 1.25, 1.10, 0.01, help="IS 800 Cl.5.4.1 — Partial safety factor for resistance")

    all_sec_types = {
        "ISMB (I-Beam)": ISMB,
        "ISLB (Light Beam)": ISLB,
        "ISMC (Channel)": ISMC,
    }
    sec_type_label = st.selectbox("Section Type", list(all_sec_types.keys()))
    sec_dict  = all_sec_types[sec_type_label]
    sec_names = list(sec_dict.keys())
    sec_name  = st.selectbox("Section Designation", sec_names, index=min(4, len(sec_names)-1))
    sp = sec_dict[sec_name]

    with st.expander("📋 Section Properties (auto-filled from SP 6(1):1964)"):
        col_a, col_b = st.columns(2)
        col_a.metric("A (cm²)", sp.get("Area", 0))
        col_a.metric("Ixx (cm⁴)", sp.get("Ixx", 0))
        col_a.metric("Zpx (cm³)", sp.get("Zpx", 0))
        col_b.metric("h × bf (mm)", f"{sp.get('h', 0)} × {sp.get('bf', 0)}")
        col_b.metric("tf / tw (mm)", f"{sp.get('tf', 0)} / {sp.get('tw', 0)}")
        col_b.metric("Weight (kg/m)", sp.get("weight", 0))

# ── Run Calculation ────────────────────────────────────────────────────────
if st.button("▶  Run Purlin Design", use_container_width=True, type="primary"):
    inp = {
        "span_m": span, "spacing_m": spacing, "roof_slope_deg": slope,
        "dead_load": dead_load, "live_load": live_load,
        "wind_pressure": wind_pres, "Cp_ext": Cpe, "Cp_int": Cpi,
        "fy": float(fy), "gm0": gm0,
        "section_name": sec_name, "section_props": sp,
    }
    r = run_purlin_design(inp)
    st.session_state["purlin_result"] = r
    st.session_state["purlin_project"] = project_name
    st.session_state["purlin_section_name"] = sec_name

# ── Display Results ────────────────────────────────────────────────────────
if "purlin_result" in st.session_state:
    r = st.session_state["purlin_result"]
    cls = r.get("section_class", {})

    ok_all = r.get("overall_status") == "SAFE"
    status_icon = "✅" if ok_all else "❌"
    st.markdown(f"### {status_icon} Overall Status: **{r['overall_status']}**")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Governing Combo", r.get("governing_combo", "—").split(":", 1)[0])
    m2.metric("Biaxial Utilisation", f"{r['biaxial_ratio']*100:.1f}%")
    m3.metric("Shear Utilisation", f"{r.get('shear_ratio', 0)*100:.1f}%")
    m4.metric("Deflection Utilisation", f"{r.get('defl_ratio', 0)*100:.1f}%")

    if ok_all:
        st.success(f"Section **{r['section_name']}** is adequate for the selected design inputs.")
    else:
        st.error(f"Section **{r['section_name']}** is not adequate. Increase the section size or revise spacing/span/loading.")

    st.divider()

    # ── Step 1: Loads ──────────────────────────────────────────
    with st.expander("📌 Step 1 — Load Calculation  [IS 875]", expanded=True):
        st.markdown('<div class="step-header">1.1  Self Weight & Distributed Loads</div>', unsafe_allow_html=True)
        st.markdown(f"""
<div class="formula-box">
Self weight of purlin  =  {r['sw_kNm']:.4f} kN/m  [SP 6(1):1964]

Total DL on purlin  =  {dead_load:.2f} × {spacing:.2f} + {r['sw_kNm']:.4f}  =  {dead_load*spacing+r['sw_kNm']:.4f} kN/m

Resolved perpendicular to slope (→ Mz):
  w_z,DL  =  w_DL × cos θ  =  {r['wz_DL']:.4f} kN/m  [IS 875 Pt.1]
  w_z,LL  =  LL × s × cos θ  =  {r['wz_LL']:.4f} kN/m  [IS 875 Pt.2]

Resolved along slope (→ My):
  w_y,DL  =  w_DL × sin θ  =  {r['wy_DL']:.4f} kN/m
  w_y,LL  =  LL × s × sin θ  =  {r['wy_LL']:.4f} kN/m

Wind load:
  w_wind  =  qd × (Cpe − Cpi) × s  =  {wind_pres:.2f} × ({Cpe:.2f} − {Cpi:.2f}) × {spacing:.2f}  =  {r['w_wind']:.4f} kN/m  [IS 875 Pt.3]
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="step-header">1.2  Load Combinations  [IS 800:2007 Table 4]</div>', unsafe_allow_html=True)
        
        combo_df = pd.DataFrame({
            "Load Combo": ["LC1: 1.5(DL+LL)", "LC2: 1.2(DL+LL+Wind)", "LC3: 0.9DL+1.5Wind"],
            "wz,d (kN/m)": [r.get("wz_1", 0), r.get("wz_2", 0), r.get("wz_3", 0)],
            "wy,d (kN/m)": [r.get("wy_1", 0), r.get("wy_2", 0), r.get("wy_3", 0)],
        })
        st.dataframe(combo_df.set_index("Load Combo"), use_container_width=True)
        st.info(
            f"**Governing combo:** {r.get('governing_combo', '—')}  |  "
            f"design magnitudes: wz,d = {r['wz_d']:.4f} kN/m, wy,d = {r['wy_d']:.4f} kN/m"
        )

    # ── Step 2: Section Classification ────────────────────────
    with st.expander("📌 Step 2 — Section Classification  [IS 800:2007 Table 2]"):
        
        eps = cls.get('epsilon', (250/float(fy))**0.5)
        b_tf_val = cls.get('b_tf', 0.0)
        d_tw_val = cls.get('d_tw', 0.0)
        
        limits = cls.get('limits', {})
        f_lim = limits.get('flange', [0.0, 0.0, 0.0])
        w_lim = limits.get('web', [0.0, 0.0, 0.0])
        
        f_class = cls.get('flange_class', 'Unknown')
        w_class = cls.get('web_class', 'Unknown')
        overall_class = cls.get('overall', 'Unknown')

        st.markdown(f"""
<div class="formula-box">
ε  =  √(250 / fy)  =  √(250 / {r.get('fy', 250):.0f})  =  {eps:.4f}

Outstand flange ratio:
  b/tf  =  ({sp.get('bf',0)}/2 − {sp.get('tw',0)}/2) / {sp.get('tf',1)}  =  {b_tf_val:.2f}
  Plastic limit  9.4ε  =  {f_lim[0]:.2f}
  Compact  limit 13.6ε =  {f_lim[1]:.2f}
  Semi-compact  15.7ε  =  {f_lim[2]:.2f}
  → Flange: {f_class}

Web ratio:
  d/tw  =  ({sp.get('h',0)} − 2×{sp.get('tf',0)}) / {sp.get('tw',1)}  =  {d_tw_val:.2f}
  Plastic limit  84ε   =  {w_lim[0]:.2f}
  Compact  limit 105ε  =  {w_lim[1]:.2f}
  Semi-compact  126ε   =  {w_lim[2]:.2f}
  → Web: {w_class}

Overall Classification:  {overall_class}
</div>
""", unsafe_allow_html=True)

    # ── Step 3: BM & SF ────────────────────────────────────────
    with st.expander("📌 Step 3 — Design Bending Moments & Shear Force"):
        st.markdown(f"""
<div class="formula-box">
Simply supported purlin, UDL loading:

Mz  =  wz,d × L² / 8  =  {r['wz_d']:.4f} × {span:.2f}² / 8  =  {r['Mz_kNm']:.4f} kNm  (major axis)
My  =  wy,d × L² / 8  =  {r['wy_d']:.4f} × {span:.2f}² / 8  =  {r['My_kNm']:.4f} kNm  (minor axis)

Vz  =  wz,d × L / 2  =  {r['wz_d']:.4f} × {span:.2f} / 2  =  {r['Vz_kN']:.4f} kN
Vy  =  wy,d × L / 2  =  {r['wy_d']:.4f} × {span:.2f} / 2  =  {r['Vy_kN']:.4f} kN
</div>
""", unsafe_allow_html=True)

    # ── Step 4: Moment Capacity ────────────────────────────────
    with st.expander("📌 Step 4 — Design Moment Capacity  [IS 800:2007 Cl. 8.2.1]"):
        if overall_class in ("Plastic", "Compact"):
            st.markdown(f"""
<div class="formula-box">
{overall_class} section → use plastic section modulus

Mdz  =  βb × Zpx × fy / γm0  =  1.0 × {sp.get('Zpx', 0):.2f} cm³ × {r['fy']:.0f} / ({r['gm0']:.2f} × 1000)
     =  {r['Mdz_kNm']:.4f} kNm  [IS 800 Cl. 8.2.1.2]

Mdy  =  βb × Zpy × fy / γm0  =  1.0 × {sp.get('Zpy', 0):.2f} cm³ × {r['fy']:.0f} / ({r['gm0']:.2f} × 1000)
     =  {r['Mdy_kNm']:.4f} kNm
</div>
""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div class="formula-box">
Semi-compact section → use elastic section modulus

Mdz  =  Zxx × fy / γm0  =  {sp.get('Zxx', 0):.2f} × {r['fy']:.0f} / ({r['gm0']:.2f} × 1000)  =  {r['Mdz_kNm']:.4f} kNm
Mdy  =  Zyy × fy / γm0  =  {sp.get('Zyy', 0):.2f} × {r['fy']:.0f} / ({r['gm0']:.2f} × 1000)  =  {r['Mdy_kNm']:.4f} kNm
</div>
""", unsafe_allow_html=True)

    # ── Step 5: Biaxial Check ──────────────────────────────────
    with st.expander("📌 Step 5 — Biaxial Bending Check  [IS 800:2007 Cl. 9.3.1.1]", expanded=True):
        st.markdown(f"""
<div class="formula-box">
My / Mdy  +  Mz / Mdz  ≤  1.0

{r['My_kNm']:.4f} / {r['Mdy_kNm']:.4f}  +  {r['Mz_kNm']:.4f} / {r['Mdz_kNm']:.4f}  =  {r['biaxial_ratio']:.4f}
</div>
""", unsafe_allow_html=True)
        if r.get("biaxial_ok"):
            st.markdown(f'<div class="result-safe">✓ PASS — Biaxial ratio = <b>{r["biaxial_ratio"]:.4f}</b> ≤ 1.0</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="result-fail">✗ FAIL — Biaxial ratio = <b>{r["biaxial_ratio"]:.4f}</b> > 1.0</div>', unsafe_allow_html=True)

    # ── Step 6: Shear ──────────────────────────────────────────
    with st.expander("📌 Step 6 — Shear Capacity Check  [IS 800:2007 Cl. 8.4.1]"):
        st.markdown(f"""
<div class="formula-box">
Shear area:  Av  =  h × tw  =  {sp.get('h', 0)} × {sp.get('tw', 0)}  =  {r['Av_mm2']:.0f} mm²

Vd  =  Av × fy / (√3 × γm0)  =  {r['Av_mm2']:.0f} × {r['fy']:.0f} / (√3 × {r['gm0']:.2f} × 1000)
    =  {r['Vd_kN']:.4f} kN

Vz (applied)  =  {r['Vz_kN']:.4f} kN
</div>
""", unsafe_allow_html=True)
        if r.get("shear_ok"):
            st.markdown(f'<div class="result-safe">✓ PASS — Vz = {r["Vz_kN"]:.4f} kN ≤ Vd = {r["Vd_kN"]:.4f} kN  '
                        f'({r["Vz_kN"]/r["Vd_kN"]*100:.1f}% utilisation)</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="result-fail">✗ FAIL — Vz = {r["Vz_kN"]:.4f} kN > Vd = {r["Vd_kN"]:.4f} kN</div>', unsafe_allow_html=True)

    # ── Step 7: Deflection ─────────────────────────────────────
    with st.expander("📌 Step 7 — Deflection Check  [IS 800:2007 Table 6]"):
        st.markdown(f"""
<div class="formula-box">
Service load (unfactored):  wz,ser  =  {r['wz_DL']+r['wz_LL']:.4f} N/mm

δ_max  =  5 × wz,ser × L⁴ / (384 × E × Izz)
       =  5 × {r['wz_DL']+r['wz_LL']:.4f} × ({span*1000:.0f})⁴ / (384 × 2×10⁵ × {sp.get('Ixx', 0):.1f}×10⁴)
       =  {r['delta_max_mm']:.3f} mm

Permissible:  L / 180  =  {span*1000:.0f} / 180  =  {r['delta_limit_mm']:.3f} mm
</div>
""", unsafe_allow_html=True)
        if r.get("defl_ok"):
            st.markdown(f'<div class="result-safe">✓ PASS — δ = {r["delta_max_mm"]:.3f} mm ≤ L/180 = {r["delta_limit_mm"]:.3f} mm</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="result-fail">✗ FAIL — δ = {r["delta_max_mm"]:.3f} mm > L/180 = {r["delta_limit_mm"]:.3f} mm</div>', unsafe_allow_html=True)

    # ── Summary Table ──────────────────────────────────────────
    st.divider()
    st.markdown("### 📊 Design Summary")
    
    summary = pd.DataFrame({
        "Check": ["Biaxial Bending", "Shear Capacity", "Deflection"],
        "Applied": [f"{r['biaxial_ratio']:.4f}", f"Vz = {r['Vz_kN']:.4f} kN", f"δ = {r['delta_max_mm']:.3f} mm"],
        "Capacity": ["1.000", f"Vd = {r['Vd_kN']:.4f} kN", f"L/180 = {r['delta_limit_mm']:.3f} mm"],
        "Utilisation (%)": [
            f"{r['biaxial_ratio']*100:.1f}",
            f"{r.get('shear_ratio', 0)*100:.1f}",
            f"{r.get('defl_ratio', 0)*100:.1f}",
        ],
        "Status": [
            "✅ PASS" if r.get("biaxial_ok") else "❌ FAIL",
            "✅ PASS" if r.get("shear_ok")   else "❌ FAIL",
            "✅ PASS" if r.get("defl_ok")    else "❌ FAIL",
        ],
    })
    st.dataframe(summary.set_index("Check"), use_container_width=True)

    # ── PDF Download ───────────────────────────────────────────
    st.divider()
    st.markdown("### 📄 Download Design Report (PDF)")
    pdf_bytes = generate_purlin_pdf(r, project=st.session_state.get("purlin_project",""))
    download_name = st.session_state.get("purlin_section_name", r.get("section_name", "Purlin"))
    st.download_button(
        label="⬇️  Download PDF Report",
        data=pdf_bytes,
        file_name=f"Purlin_Design_{download_name.replace(' ','_')}.pdf",
        mime="application/pdf",
        use_container_width=True,
        type="primary",
    )
    st.caption("The PDF contains step-by-step calculations with all formulae, references, "
               "load combinations, and section classification per IS 800:2007.")
