"""
MedicSync - Vertical Sidebar Navigation
Renders a collapsible sidebar menu using the native Streamlit sidebar control.
"""
import streamlit as st
import json


# Mapare pagină → (cheie_notificare, culoare_badge)
_BADGE_MAP = {
    "pages/Semne_Vitale.py": ("critical_alerts", "#dc2626"),
    "pages/Pacienți.py":     ("critical_alerts", "#dc2626"),
    "pages/Comenzi.py":      ("pending_orders", "#d97706"),
    "pages/Grafic.py":       ("pending_vacation_requests", "#1d4ed8"),
}

_SVG_ATTR = 'xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"'

def _icon(paths: str) -> str:
    return f'<svg {_SVG_ATTR}>{paths}</svg>'

_NAV_ICONS = {
    "Acasă":          _icon('<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>'),
    "Dashboard":      _icon('<line x1="18" x2="18" y1="20" y2="10"/><line x1="12" x2="12" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/>'),
    "Departamente":   _icon('<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/>'),
    "Pacienți":       _icon('<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'),
    "Semne Vitale":   _icon('<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>'),
    "Inventar":       _icon('<path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>'),
    "Comenzi":        _icon('<circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/>'),
    "Predicții Stoc": _icon('<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/>'),
    "Predicții ML":   _icon('<path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/>'),
    "Grafic Lunar":   _icon('<rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/>'),
}


def _inject_badge_js(badge_data: dict):
    """Injectează JS printr-un iframe invizibil pentru icoane + badge-uri."""
    import streamlit.components.v1 as components

    badge_entries = [
        f'[{json.dumps(kw)}, {cnt}, {json.dumps(col)}]'
        for kw, (cnt, col) in badge_data.items()
        if cnt > 0
    ]
    js_badge_array = ",\n".join(badge_entries) if badge_entries else ""

    icon_entries = [
        f'[{json.dumps(label)}, {json.dumps(svg)}]'
        for label, svg in _NAV_ICONS.items()
    ]
    js_icon_array = ",\n".join(icon_entries)

    components.html(f"""<!DOCTYPE html><html><body><script>
    (function() {{
      try {{
        const doc = window.parent.document;
        window.parent._msBadges = [{js_badge_array}];
        const navIcons = [{js_icon_array}];

        function apply() {{
          doc.querySelectorAll('[data-testid="stPageLink"] a').forEach(function(link) {{
            const text = link.textContent.trim();

            // --- Icon injection (once per link) ---
            if (!link.querySelector('.ms-nav-icon')) {{
              for (let i = 0; i < navIcons.length; i++) {{
                if (text.indexOf(navIcons[i][0]) !== -1) {{
                  const span = doc.createElement('span');
                  span.className = 'ms-nav-icon';
                  span.innerHTML = navIcons[i][1];
                  link.insertBefore(span, link.firstChild);
                  break;
                }}
              }}
            }}

            // --- Badge injection ---
            const badges = window.parent._msBadges || [];
            const existing = link.querySelector('.ms-notif-badge');
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
            from cache import get_notifications_summary
            counts.update(get_notifications_summary(api_client.token))
        except Exception:
            pass

    for page in visible_pages:
        st.page_link(page["path"], label=page["label"], use_container_width=True)

    badge_data = {}
    for path, (key, color) in _BADGE_MAP.items():
        count = counts.get(key, 0)
        page_entry = next((p for p in visible_pages if p["path"] == path), None)
        if page_entry and count > 0:
            keyword = page_entry["label"].strip()
            badge_data[keyword] = (count, color)

    _inject_badge_js(badge_data)


PAGES = [
    {"path": "app.py",                   "label": "Acasă",          "roles": None},
    {"path": "pages/Dashboard.py",       "label": "Dashboard",      "roles": None},
    {"path": "pages/Departamente.py",    "label": "Departamente",   "roles": ["manager", "doctor", "inventory_manager"]},
    {"path": "pages/Pacienți.py",        "label": "Pacienți",       "roles": ["doctor", "nurse", "manager"]},
    {"path": "pages/Semne_Vitale.py",    "label": "Semne Vitale",   "roles": ["nurse", "doctor"]},
    {"path": "pages/Inventar.py",        "label": "Inventar",       "roles": ["manager", "inventory_manager", "nurse"]},
    {"path": "pages/Comenzi.py",         "label": "Comenzi",        "roles": ["manager", "inventory_manager"]},
    {"path": "pages/Predicții_Stoc.py",  "label": "Predicții Stoc", "roles": ["manager", "inventory_manager"]},
    {"path": "pages/Predicții_ML.py",    "label": "Predicții ML",   "roles": ["manager"]},
    {"path": "pages/Grafic.py",          "label": "Grafic Lunar",   "roles": ["nurse", "manager"]},
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
            background: #ffffff !important;
            border-right: 1px solid #e2e8f0 !important;
        }

        /* Conținut principal */
        section.main > div.block-container {
            max-width: 100% !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }

        /* Logo */
        .sidebar-logo-wrap {
            padding: 0.3rem 0 1rem;
            display: block;
        }

        .sidebar-subtitle {
            font-size: 0.63rem;
            color: #94a3b8;
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-top: 5px;
            font-weight: 500;
        }

        /* User badge */
        .sidebar-user-badge {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 0.55rem 0.8rem;
            margin-bottom: 0.9rem;
        }

        .sidebar-user-name {
            color: #0f172a;
            font-size: 0.85rem;
            font-weight: 600;
            line-height: 1.3;
        }

        .sidebar-user-role {
            color: #94a3b8;
            font-size: 0.72rem;
            margin-top: 2px;
            font-weight: 500;
        }

        /* Nav links */
        [data-testid="stSidebar"] [data-testid="stPageLink"] a {
            color: #475569 !important;
            font-size: 0.875rem !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
            padding: 0.42rem 0.7rem !important;
            transition: background 0.12s, color 0.12s !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            gap: 8px !important;
        }

        [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
            background: #f1f5f9 !important;
            color: #0f172a !important;
        }

        [data-testid="stSidebar"] a[aria-current="page"] {
            background: oklch(96% 0.025 195) !important;
            color: oklch(55% 0.09 195) !important;
            border-left: 3px solid oklch(55% 0.09 195) !important;
            border-radius: 0 8px 8px 0 !important;
            font-weight: 600 !important;
            padding-left: calc(0.7rem - 0px) !important;
        }

        /* Nav icon */
        .ms-nav-icon {
            display: inline-flex;
            align-items: center;
            flex-shrink: 0;
            opacity: 0.55;
        }

        [data-testid="stSidebar"] a[aria-current="page"] .ms-nav-icon {
            opacity: 0.85;
        }

        /* Logout */
        [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
            background: #fff5f5 !important;
            border: 1px solid #fecaca !important;
            color: #dc2626 !important;
            border-radius: 8px !important;
            font-size: 0.83rem !important;
            font-weight: 500 !important;
        }

        [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
            background: #fee2e2 !important;
            border-color: #fca5a5 !important;
        }

        /* Separator */
        [data-testid="stSidebar"] hr {
            border-color: #e2e8f0 !important;
            margin: 0.6rem 0 !important;
        }

        /* Badge notificări */
        .ms-notif-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 99px;
            font-size: 0.65rem;
            font-weight: 700;
            min-width: 1.2rem;
            height: 1.2rem;
            padding: 0 0.28rem;
            color: #fff;
            line-height: 1;
            flex-shrink: 0;
            margin-left: auto;
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
            pointer-events: none;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
            <div class="sidebar-logo-wrap">
                <svg width="152" height="36" viewBox="0 0 152 36" xmlns="http://www.w3.org/2000/svg">
                    <!-- Icon mark: teal rounded square + ECG pulse -->
                    <rect width="36" height="36" rx="9" fill="#4a9db3"/>
                    <polyline points="5,18 10,18 13,9 18,27 21,13 25,18 31,18"
                        fill="none" stroke="white" stroke-width="2.2"
                        stroke-linecap="round" stroke-linejoin="round"/>
                    <!-- Wordmark -->
                    <text y="25" font-family="'Inter',system-ui,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif" font-size="20">
                        <tspan x="45" font-weight="800" fill="#0f172a" letter-spacing="-0.4">Medic</tspan><tspan font-weight="400" fill="#4a9db3" letter-spacing="-0.2">Sync</tspan>
                    </text>
                </svg>
                <div class="sidebar-subtitle">Health 4.0</div>
            </div>
        """, unsafe_allow_html=True)

        if user_name and user_role:
            role_label = ROLE_LABELS.get(user_role, user_role)
            st.markdown(f"""
                <div class="sidebar-user-badge">
                    <div class="sidebar-user-name"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-2px;margin-right:5px"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>{user_name}</div>
                    <div class="sidebar-user-role">{role_label}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        _nav_links(visible_pages)

        st.markdown("<hr>", unsafe_allow_html=True)

        if st.button("Deconectare", use_container_width=True, key="sidebar_logout"):
            from auth import logout
            logout()
