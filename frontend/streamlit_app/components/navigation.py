"""
MedicSync - Top Navigation Bar
Renders a horizontal navigation bar, hides sidebar completely,
and shows a logout button on the right.
"""
import streamlit as st


PAGES = [
    {"path": "app.py",                    "label": "🏠 Acasă",        "roles": None},
    {"path": "pages/Dashboard.py",        "label": "🏥 Dashboard",    "roles": None},
    {"path": "pages/Departamente.py",     "label": "🏛️ Departamente", "roles": None},
    {"path": "pages/Pacienți.py",         "label": "👤 Pacienți",     "roles": ["doctor", "nurse", "manager"]},
    {"path": "pages/Semne_Vitale.py",     "label": "💓 Semne Vitale", "roles": ["nurse", "doctor", "manager"]},
    {"path": "pages/Inventar.py",         "label": "📦 Inventar",     "roles": ["manager", "inventory_manager"]},
    {"path": "pages/Comenzi.py",          "label": "🛒 Comenzi",      "roles": ["manager", "inventory_manager"]},
    {"path": "pages/Predicții_ML.py",     "label": "🤖 Predicții ML", "roles": ["manager"]},
]

ROLE_LABELS = {
    "nurse": "Asistent Medical",
    "doctor": "Doctor",
    "manager": "Manager",
    "inventory_manager": "Manager Inventar",
}


def render_top_nav():
    """
    Renders a horizontal top navigation bar with logout button.
    Hides the sidebar completely.
    """
    # ── Hide sidebar entirely ────────────────────────────────────────────────
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarNav"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        .st-emotion-cache-1cypcdb { display: none !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    # ── Determine visible pages ──────────────────────────────────────────────
    user_role = None
    user_name = None
    if st.session_state.get("authenticated") and st.session_state.get("user"):
        user_role = st.session_state.user.get("role")
        user_name = st.session_state.user.get("full_name", "")

    visible_pages = [
        p for p in PAGES
        if p["roles"] is None or (user_role and user_role in p["roles"])
    ]

    # ── Layout: nav links + user info + logout ──────────────────────────────
    n = len(visible_pages)
    col_widths = [1] * n + [0.01, 1.4, 0.8]
    cols = st.columns(col_widths)

    for i, page in enumerate(visible_pages):
        with cols[i]:
            st.page_link(page["path"], label=page["label"], use_container_width=True)

    # User badge
    with cols[n + 1]:
        if user_name and user_role:
            role_label = ROLE_LABELS.get(user_role, user_role)
            st.markdown(
                f"<div style='text-align:right; padding-top:6px; font-size:0.85rem; color:#6c757d;'>"
                f"👤 <b>{user_name}</b> · {role_label}</div>",
                unsafe_allow_html=True
            )

    # Logout button
    with cols[n + 2]:
        if st.button("🚪 Ieșire", use_container_width=True, key="top_nav_logout"):
            from auth import logout
            logout()

    st.markdown("<hr style='margin: 6px 0 16px 0; border-color: #e9ecef;'>", unsafe_allow_html=True)
