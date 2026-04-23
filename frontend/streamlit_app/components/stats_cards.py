"""
MedicSync Frontend - Reusable Stats Components
KPI cards for dashboards.
"""
import streamlit as st

# Teal accent hex (matches oklch(55% 0.09 195))
_TEAL = "#4a9db3"

_PALETTE = {
    "teal":   (_TEAL,    "#e8f4f7"),
    "blue":   (_TEAL,    "#e8f4f7"),
    "green":  ("#059669", "#ecfdf5"),
    "red":    ("#dc2626", "#fef2f2"),
    "orange": ("#d97706", "#fffbeb"),
}


def kpi_card(title: str, value: str, subtitle: str = None, color: str = "teal"):
    border_color, _ = _PALETTE.get(color, _PALETTE["teal"])

    subtitle_html = (
        f'<p style="margin:0.45rem 0 0;font-size:0.78rem;'
        f'color:#94a3b8;font-weight:400;line-height:1.4;">{subtitle}</p>'
        if subtitle else ""
    )

    st.markdown(f"""
    <div style="
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 3px solid {border_color};
        border-radius: 0 12px 12px 0;
        padding: 1.25rem 1.4rem;
        box-shadow: 0 1px 3px rgba(15,23,42,0.05);
        height: 100%;
        font-family: 'Inter', system-ui, sans-serif;
    ">
        <p style="margin:0 0 0.5rem;font-size:0.7rem;font-weight:600;
                  letter-spacing:0.09em;text-transform:uppercase;color:#94a3b8;">{title}</p>
        <p style="margin:0;font-size:2.6rem;font-weight:800;line-height:1;
                  color:#0f172a;letter-spacing:-2px;font-variant-numeric:tabular-nums;">{value}</p>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def metric_card(label: str, value: str, delta: str = None, icon: str = None):
    st.metric(label=label, value=value, delta=delta)


def stats_row(stats: list):
    cols = st.columns(len(stats))
    for col, stat in zip(cols, stats):
        with col:
            metric_card(**stat)
