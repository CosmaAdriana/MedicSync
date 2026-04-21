"""
MedicSync Frontend - Main Application Entry Point

Run with: streamlit run app.py
"""
import streamlit as st
import os
import base64
from auth import (
    init_session_state, landing_page, login_page, register_page,
    logout, get_user_name, get_user_role, handle_api_exception
)
from config import APP_TITLE, APP_ICON, LAYOUT, INITIAL_SIDEBAR_STATE
from components.navigation import render_top_nav
import cache


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

# ============================================================================
# Authentication Flow
# ============================================================================
if not st.session_state.authenticated:
    auth_view = st.session_state.get("auth_view", "landing")
    if auth_view == "login":
        login_page()
    elif auth_view == "register":
        register_page()
    else:
        landing_page()

else:
    # Încălzește cache-ul în background la prima vizită după login
    if not st.session_state.get("cache_warmed"):
        cache.prefetch_all_async(st.session_state.api_client.token)
        st.session_state.cache_warmed = True

    render_top_nav()

    # ── Ascunde header Streamlit pe pagina principală ────────────────────────
    st.markdown("""
        <style>
        [data-testid="stHeader"] { background: transparent !important; }
        </style>
    """, unsafe_allow_html=True)

    # ── Full-page background image ───────────────────────────────────────────
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    img_path = None
    for ext in ("poza4.jpg", "poza4.png"):
        p = os.path.join(root, ext)
        if os.path.exists(p):
            img_path = p
            break

    if img_path:
        img_b64 = _load_bg_image(img_path)
        mime = "image/jpeg" if img_path.endswith(".jpg") else "image/png"

        st.markdown(f"""
            <style>
            [data-testid="stAppViewContainer"] {{
                background-image: url("data:{mime};base64,{img_b64}");
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
    user_role  = get_user_role()
    role_label = ROLE_LABELS.get(user_role, user_role)
    user_obj   = st.session_state.user or {}

    dept_label = ""
    if user_role in ("nurse", "doctor") and user_obj.get("department_id"):
        try:
            depts = cache.get_departments(st.session_state.api_client.token)
            dept_map = {d["id"]: d["name"] for d in depts}
            dept_name = dept_map.get(user_obj["department_id"], "")
            if dept_name:
                dept_label = f" &nbsp;·&nbsp; 🏥 {dept_name}"
        except Exception:
            pass

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
                {role_label}{dept_label} &nbsp;·&nbsp; MedicSync Health 4.0
            </p>
        </div>
    """, unsafe_allow_html=True)

    try:
        api = st.session_state.api_client
        departments  = cache.get_departments(api.token)
        all_patients = cache.get_patients(api.token)

        admitted = [p for p in all_patients if p.get('status') == 'admitted']
        critical = [p for p in all_patients if p.get('status') == 'critical']

        _, c1, c2, c3, _ = st.columns([1, 1, 1, 1, 1])

        for col, icon, label, value, color in [
            (c1, "🏛️", "Departamente",      len(departments), "#1f77b4"),
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
        if not handle_api_exception(e):
            st.error(f"Eroare la încărcarea statisticilor: {str(e)}")

    st.markdown("""
        <p style="
            position: fixed; bottom: 12px; right: 16px;
            color: rgba(255,255,255,0.5); font-size: 0.75rem;
            z-index: 999;
        ">🏥 MedicSync © 2026</p>
    """, unsafe_allow_html=True)
