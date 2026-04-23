"""
MedicSync - Vertical Sidebar Navigation
Renders a collapsible sidebar menu using the native Streamlit sidebar control.
"""
import streamlit as st


# Mapare pagină → (cheie_notificare, culoare_badge)
_BADGE_MAP = {
    "pages/Semne_Vitale.py": ("critical_alerts", "#dc2626"),
    "pages/Pacienți.py":     ("critical_alerts", "#dc2626"),
    "pages/Comenzi.py":      ("pending_orders", "#d97706"),
    "pages/Grafic.py":       ("pending_vacation_requests", "#1d4ed8"),
}


def _inject_badge_js(badge_data: dict):
    """Injectează JS printr-un iframe invizibil pentru badge-uri."""
    import streamlit.components.v1 as components

    entries = [
        f'["{kw}", {cnt}, "{col}"]'
        for kw, (cnt, col) in badge_data.items()
        if cnt > 0
    ]
    js_array = ",\n".join(entries) if entries else ""

    components.html(f"""<!DOCTYPE html><html><body><script>
    (function() {{
      try {{
        const doc = window.parent.document;
        window.parent._msBadges = [{js_array}];

        function apply() {{
          const badges = window.parent._msBadges || [];
          doc.querySelectorAll('[data-testid="stPageLink"] a').forEach(function(link) {{
            const existing = link.querySelector('.ms-notif-badge');
            const text = link.textContent.trim();
            let matched = null;

            for (let i = 0; i < badges.length; i++) {{
              if (text.indexOf(badges[i][0]) !== -1) {{
                matched = {{ count: badges[i][1], color: badges[i][2] }};
                break;
              }}
            }}

            if (matched) {{
              if (existing) {{
                existing.textContent = matched.count;
                existing.style.background = matched.color;
              }} else {{
                const b = doc.createElement('span');
                b.className = 'ms-notif-badge';
                b.style.background = matched.color;
                b.textContent = matched.count;
                link.appendChild(b);
              }}
            }} else if (existing) {{
              existing.remove();
            }}
          }});
        }}

        if (window.parent._msInterval) clearInterval(window.parent._msInterval);

        apply();
        window.parent._msInterval = setInterval(apply, 500);

      }} catch(e) {{}}
    }})();
    </script></body></html>""", height=0)


@st.fragment(run_every=30)
def _nav_links(visible_pages):
    """Re-randează link-urile de navigație la fiecare 30s cu badge-uri actualizate."""
    api_client = st.session_state.get("api_client")
    counts = {
        "critical_alerts": 0,
        "pending_orders": 0,
        "pending_vacation_requests": 0
    }

    if api_client and getattr(api_client, "token", None):
        try:
            counts.update(api_client.get_notifications_summary())
        except Exception:
            pass

    for page in visible_pages:
        st.page_link(page["path"], label=page["label"], use_container_width=True)

    badge_data = {}
    for path, (key, color) in _BADGE_MAP.items():
        count = counts.get(key, 0)
        page_entry = next((p for p in visible_pages if p["path"] == path), None)
        if page_entry and count > 0:
            keyword = page_entry["label"].split(" ", 1)[-1].strip()
            badge_data[keyword] = (count, color)

    _inject_badge_js(badge_data)


PAGES = [
    {"path": "app.py",                   "label": "🏠 Acasă",          "roles": None},
    {"path": "pages/Dashboard.py",       "label": "🏥 Dashboard",      "roles": None},
    {"path": "pages/Departamente.py",    "label": "🏛️ Departamente",   "roles": None},
    {"path": "pages/Pacienți.py",        "label": "👤 Pacienți",       "roles": ["doctor", "nurse", "manager"]},
    {"path": "pages/Semne_Vitale.py",    "label": "💓 Semne Vitale",   "roles": ["nurse", "doctor", "manager"]},
    {"path": "pages/Inventar.py",        "label": "📦 Inventar",       "roles": ["manager", "inventory_manager", "nurse"]},
    {"path": "pages/Comenzi.py",         "label": "🛒 Comenzi",        "roles": ["manager", "inventory_manager"]},
    {"path": "pages/Predicții_Stoc.py",  "label": "📊 Predicții Stoc", "roles": ["manager", "inventory_manager"]},
    {"path": "pages/Predicții_ML.py",    "label": "🤖 Predicții ML",   "roles": ["manager"]},
    {"path": "pages/Grafic.py",          "label": "📅 Grafic Lunar",   "roles": ["nurse", "manager"]},
]

ROLE_LABELS = {
    "nurse": "Asistent Medical",
    "doctor": "Doctor",
    "manager": "Manager",
    "inventory_manager": "Manager Inventar",
}


def _get_current_page_hash():
    """Returnează hash-ul paginii curente din contextul Streamlit."""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        ctx = get_script_run_ctx()
        return ctx.page_script_hash if ctx else None
    except Exception:
        return None


def render_top_nav():
    from components.styles import inject_global_css
    inject_global_css()

    current_page = _get_current_page_hash()
    if current_page and current_page != st.session_state.get("_current_page"):
        st.session_state._current_page = current_page

    user_role = None
    user_name = None
    if st.session_state.get("authenticated") and st.session_state.get("user"):
        user_role = st.session_state.user.get("role")
        user_name = st.session_state.user.get("full_name", "")

    visible_pages = [
        p for p in PAGES
        if p["roles"] is None or (user_role and user_role in p["roles"])
    ]

    st.markdown("""
    <style>
        /* Ascunde lista automată de pagini Streamlit */
        [data-testid="stSidebarNav"] { display: none !important; }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: #f8f9fa !important;
            border-right: 1px solid #dee2e6 !important;
        }

        /* Conținut principal */
        section.main > div.block-container {
            max-width: 100% !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }

        /* Logo */
        .sidebar-logo {
            font-size: 1.35rem;
            font-weight: 800;
            color: #1a1a2e;
            letter-spacing: -0.5px;
            padding: 0.2rem 0 0;
        }

        .sidebar-subtitle {
            font-size: 0.68rem;
            color: #6c757d;
            letter-spacing: 2px;
            text-transform: uppercase;
            margin-top: -2px;
            margin-bottom: 1rem;
        }

        /* User badge */
        .sidebar-user-badge {
            background: #ffffff;
            border: 1px solid #dee2e6;
            border-radius: 10px;
            padding: 0.6rem 0.8rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        }

        .sidebar-user-name {
            color: #212529;
            font-size: 0.87rem;
            font-weight: 600;
        }

        .sidebar-user-role {
            color: #6c757d;
            font-size: 0.74rem;
            margin-top: 2px;
        }

        /* Nav links */
        [data-testid="stSidebar"] [data-testid="stPageLink"] a {
            color: #495057 !important;
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
            padding: 0.45rem 0.75rem !important;
            transition: background 0.15s, color 0.15s !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            gap: 0.4rem !important;
        }

        [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
            background: #e9ecef !important;
            color: #1a1a2e !important;
        }

        [data-testid="stSidebar"] a[aria-current="page"] {
            background: #dbeafe !important;
            color: #1d4ed8 !important;
            border-left: 3px solid #1d4ed8 !important;
            font-weight: 600 !important;
        }

        /* Logout */
        [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
            background: #fff5f5 !important;
            border: 1px solid #fca5a5 !important;
            color: #dc2626 !important;
            border-radius: 8px !important;
            font-size: 0.85rem !important;
        }

        [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
            background: #fee2e2 !important;
        }

        /* Separator */
        [data-testid="stSidebar"] hr {
            border-color: #dee2e6 !important;
            margin: 0.7rem 0 !important;
        }

        /* Badge notificări */
        .ms-notif-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 99px;
            font-size: 0.68rem;
            font-weight: 700;
            min-width: 1.25rem;
            height: 1.25rem;
            padding: 0 0.3rem;
            color: #fff;
            line-height: 1;
            flex-shrink: 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.25);
            pointer-events: none;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
            <div class="sidebar-logo">🏥 MedicSync</div>
            <div class="sidebar-subtitle">Health 4.0</div>
        """, unsafe_allow_html=True)

        if user_name and user_role:
            role_label = ROLE_LABELS.get(user_role, user_role)
            st.markdown(f"""
                <div class="sidebar-user-badge">
                    <div class="sidebar-user-name">👤 {user_name}</div>
                    <div class="sidebar-user-role">{role_label}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        _nav_links(visible_pages)

        st.markdown("<hr>", unsafe_allow_html=True)

        if st.button("🚪 Deconectare", use_container_width=True, key="sidebar_logout"):
            from auth import logout
            logout()

