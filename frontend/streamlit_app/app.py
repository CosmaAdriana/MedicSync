"""
MedicSync Frontend - Main Application Entry Point

Run with: streamlit run app.py
"""
import streamlit as st
import os
import base64
import time
from auth import init_session_state, login_page, register_page, logout, get_user_name, get_user_role
from config import APP_TITLE, APP_ICON, LAYOUT, INITIAL_SIDEBAR_STATE
from components.navigation import render_top_nav


@st.cache_data(show_spinner=False)
def _load_bg_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

ROLE_LABELS = {
    "nurse": "Asistent Medical",
    "doctor": "Doctor",
    "manager": "Manager",
    "inventory_manager": "Manager Inventar",
}

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout=LAYOUT,
    initial_sidebar_state=INITIAL_SIDEBAR_STATE
)

init_session_state()

if "show_register" not in st.session_state:
    st.session_state.show_register = False

# ============================================================================
# Authentication Flow
# ============================================================================
if not st.session_state.authenticated:
    if st.session_state.show_register:
        register_page()
    else:
        login_page()

else:
    render_top_nav()

    # ── Full-page background image ───────────────────────────────────────────
    img_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "poza4.png"
    )

    if os.path.exists(img_path):
        img_b64 = _load_bg_image(img_path)

        st.markdown(f"""
            <style>
            [data-testid="stAppViewContainer"] {{
                background-image: url("data:image/png;base64,{img_b64}");
                background-size: 100% 100%;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            [data-testid="stAppViewContainer"]::before {{
                content: "";
                position: fixed;
                inset: 0;
                background: rgba(0, 0, 0, 0.45);
                z-index: 0;
            }}
            [data-testid="stVerticalBlock"] {{
                position: relative;
                z-index: 1;
            }}
            </style>
        """, unsafe_allow_html=True)

    # ── Greeting & Stats overlay ─────────────────────────────────────────────
    user_role = get_user_role()
    role_label = ROLE_LABELS.get(user_role, user_role)

    st.markdown(f"""
        <div style="
            margin-top: 6vh;
            text-align: center;
            color: white;
            text-shadow: 0 2px 8px rgba(0,0,0,0.7);
        ">
            <h1 style="font-size: 3rem; margin-bottom: 0.2rem;">
                Bună, {get_user_name()}! 👋
            </h1>
            <p style="font-size: 1.2rem; opacity: 0.9; margin-bottom: 2.5rem;">
                {role_label} &nbsp;·&nbsp; MedicSync Health 4.0
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Stats cards — cached for 60s to avoid re-fetching on every interaction
    try:
        api = st.session_state.api_client
        _now = time.time()
        if "stats_cache_time" not in st.session_state or _now - st.session_state.stats_cache_time > 60:
            st.session_state.stats_departments = api.get_departments()
            st.session_state.stats_patients = api.get_patients()
            st.session_state.stats_cache_time = _now
        departments = st.session_state.stats_departments
        all_patients = st.session_state.stats_patients

        admitted = [p for p in all_patients if p.get('status') == 'admitted']
        critical = [p for p in all_patients if p.get('status') == 'critical']

        _, c1, c2, c3, _ = st.columns([1, 1, 1, 1, 1])

        for col, icon, label, value, color in [
            (c1, "🏛️", "Departamente",     len(departments), "#1f77b4"),
            (c2, "✅", "Pacienți Internați", len(admitted),    "#2ca02c"),
            (c3, "🚨", "Pacienți Critici",   len(critical),    "#d62728"),
        ]:
            col.markdown(f"""
                <div style="
                    background: rgba(255,255,255,0.15);
                    backdrop-filter: blur(8px);
                    border: 1px solid rgba(255,255,255,0.3);
                    border-radius: 16px;
                    padding: 1.4rem 1rem;
                    text-align: center;
                    color: white;
                    text-shadow: 0 1px 4px rgba(0,0,0,0.5);
                ">
                    <div style="font-size:2rem;">{icon}</div>
                    <div style="font-size:2.2rem; font-weight:700;">{value}</div>
                    <div style="font-size:0.85rem; opacity:0.85;">{label}</div>
                </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Eroare la încărcarea statisticilor: {str(e)}")

    st.markdown("""
        <p style="
            position: fixed; bottom: 12px; right: 16px;
            color: rgba(255,255,255,0.5); font-size: 0.75rem;
            z-index: 999;
        ">🏥 MedicSync © 2026</p>
    """, unsafe_allow_html=True)
