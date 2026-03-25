"""
MedicSync Frontend - Reusable Stats Components
Componente pentru afișarea metrici și KPI-uri.
"""
import streamlit as st


def metric_card(label: str, value: str, delta: str = None, icon: str = "📊"):
    """
    Display a metric card with icon.

    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta/change indicator
        icon: Emoji icon to display
    """
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown(f"### {icon}")
    with col2:
        st.metric(label=label, value=value, delta=delta)


def stats_row(stats: list):
    """
    Display a row of stat cards.

    Args:
        stats: List of dicts with keys: label, value, icon, delta (optional)

    Example:
        stats_row([
            {"label": "Total Pacienți", "value": 125, "icon": "👤"},
            {"label": "Alerte Active", "value": 5, "icon": "🚨", "delta": "+2"}
        ])
    """
    cols = st.columns(len(stats))
    for col, stat in zip(cols, stats):
        with col:
            metric_card(**stat)


def kpi_card(title: str, value: str, subtitle: str = None, color: str = "blue"):
    """
    Display a styled KPI card.

    Args:
        title: KPI title
        value: KPI value (large number)
        subtitle: Optional subtitle/description
        color: Card color theme (blue, green, red, orange)
    """
    color_map = {
        "blue": "#1f77b4",
        "green": "#2ca02c",
        "red": "#d62728",
        "orange": "#ff7f0e"
    }

    bg_color = color_map.get(color, "#1f77b4")

    html = f"""
    <div style="
        background: linear-gradient(135deg, {bg_color} 0%, {bg_color}dd 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    ">
        <h4 style="margin: 0; opacity: 0.9; font-size: 0.9rem;">{title}</h4>
        <h1 style="margin: 0.5rem 0; font-size: 2.5rem;">{value}</h1>
        {f'<p style="margin: 0; opacity: 0.8; font-size: 0.85rem;">{subtitle}</p>' if subtitle else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
