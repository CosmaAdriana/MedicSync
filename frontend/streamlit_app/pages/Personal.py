"""
MedicSync — Personal
Manager: aprobă conturi noi, gestionează asistenți/doctori, creează manageri.
"""

import sys
import os

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import require_auth, handle_api_exception
from components.navigation import render_top_nav
import cache

st.set_page_config(page_title="Personal", page_icon="👥", layout="wide",
                   initial_sidebar_state="auto")
require_auth(allowed_roles=["manager"])
render_top_nav()

api = st.session_state.api_client

if "confirm_delete_id" not in st.session_state:
    st.session_state.confirm_delete_id = None

# Departamente — necesare pentru filtru și afișare nume
try:
    departments = cache.get_departments(api.token)
    dept_map = {d["id"]: d["name"] for d in departments}
    dept_name_list = ["Toate"] + sorted(d["name"] for d in departments)
except Exception:
    dept_map = {}
    dept_name_list = ["Toate"]

st.markdown("## Personal")

tab_pending, tab_nurses, tab_doctors, tab_manager = st.tabs([
    "Conturi în așteptare",
    "Asistenți",
    "Doctori",
    "Adaugă manager",
])


# ============================================================================
# Componentă reutilizabilă — card utilizator
# ============================================================================
def _user_card(u: dict, tab_prefix: str):
    is_active   = u.get("is_active", False)
    status_bg   = "#d1fae5" if is_active else "#fef3c7"
    status_fg   = "#065f46" if is_active else "#92400e"
    status_text = "Activ"   if is_active else "Inactiv"
    dept_name   = dept_map.get(u.get("department_id"), "—")

    col_info, col_act, col_del = st.columns([5, 1, 1])

    col_info.markdown(
        f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;'
        f'padding:0.6rem 1rem;line-height:1.75;">'
        f'<b>{u["full_name"]}</b>'
        f'<span style="background:{status_bg};color:{status_fg};font-size:0.70rem;'
        f'font-weight:600;border-radius:99px;padding:1px 8px;margin-left:8px;">'
        f'{status_text}</span><br>'
        f'<span style="color:#64748b;font-size:0.80rem;">{u["email"]}</span>'
        f'<span style="color:#94a3b8;font-size:0.78rem;margin-left:10px;">· {dept_name}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if is_active:
        if col_act.button("Dezactivează", key=f"{tab_prefix}_deact_{u['id']}",
                          use_container_width=True):
            try:
                api.deactivate_user(u["id"])
                st.rerun()
            except Exception as e:
                if not handle_api_exception(e):
                    try:
                        msg = e.response.json().get("detail", str(e))
                    except Exception:
                        msg = str(e)
                    st.error(msg)
    else:
        if col_act.button("Activează", key=f"{tab_prefix}_act_{u['id']}",
                          type="primary", use_container_width=True):
            try:
                api.activate_user(u["id"])
                st.rerun()
            except Exception as e:
                handle_api_exception(e)

    confirm_key = f"{tab_prefix}_{u['id']}"
    if st.session_state.confirm_delete_id == confirm_key:
        col_del.markdown(
            '<div style="font-size:0.70rem;color:#dc2626;text-align:center;padding-top:4px;">'
            'Ești sigur?</div>',
            unsafe_allow_html=True,
        )
        c1, c2 = col_del.columns(2)
        if c1.button("Da", key=f"{tab_prefix}_del_yes_{u['id']}", type="primary"):
            try:
                api.delete_user(u["id"])
                st.session_state.confirm_delete_id = None
                st.success(f"Contul {u['full_name']} a fost șters.")
                st.rerun()
            except Exception as e:
                if not handle_api_exception(e):
                    try:
                        msg = e.response.json().get("detail", str(e))
                    except Exception:
                        msg = str(e)
                    st.error(msg)
        if c2.button("Nu", key=f"{tab_prefix}_del_no_{u['id']}"):
            st.session_state.confirm_delete_id = None
            st.rerun()
    else:
        if col_del.button("Șterge", key=f"{tab_prefix}_del_{u['id']}",
                          use_container_width=True):
            st.session_state.confirm_delete_id = confirm_key
            st.rerun()

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)


# ============================================================================
# Secțiune reutilizabilă — filtre + listă
# ============================================================================
def _staff_section(users: list, tab_prefix: str, role_label: str):
    if not users:
        st.info(f"Nu există {role_label.lower()} înregistrați.")
        return

    # ── Filtre ───────────────────────────────────────────────────────────────
    col_search, col_dept, col_status, col_sort = st.columns([3, 2, 1.5, 1.5])

    search = col_search.text_input(
        "Caută",
        placeholder="Nume sau email...",
        key=f"{tab_prefix}_search",
        label_visibility="collapsed",
    )
    col_search.caption("Caută după nume sau email")

    dept_filter = col_dept.selectbox(
        "Departament",
        options=dept_name_list,
        key=f"{tab_prefix}_dept",
    )

    status_filter = col_status.selectbox(
        "Status",
        options=["Toți", "Activi", "Inactivi"],
        key=f"{tab_prefix}_status",
    )

    sort_by = col_sort.selectbox(
        "Sortare",
        options=["Nume A→Z", "Nume Z→A", "Departament", "Status"],
        key=f"{tab_prefix}_sort",
    )

    # ── Aplicare filtre ───────────────────────────────────────────────────────
    filtered = users

    if search.strip():
        q = search.strip().lower()
        filtered = [
            u for u in filtered
            if q in u["full_name"].lower() or q in u["email"].lower()
        ]

    if dept_filter != "Toate":
        filtered = [
            u for u in filtered
            if dept_map.get(u.get("department_id")) == dept_filter
        ]

    if status_filter == "Activi":
        filtered = [u for u in filtered if u.get("is_active")]
    elif status_filter == "Inactivi":
        filtered = [u for u in filtered if not u.get("is_active")]

    if sort_by == "Nume A→Z":
        filtered = sorted(filtered, key=lambda u: u["full_name"].lower())
    elif sort_by == "Nume Z→A":
        filtered = sorted(filtered, key=lambda u: u["full_name"].lower(), reverse=True)
    elif sort_by == "Departament":
        filtered = sorted(filtered, key=lambda u: dept_map.get(u.get("department_id"), ""))
    elif sort_by == "Status":
        filtered = sorted(filtered, key=lambda u: (not u.get("is_active"), u["full_name"].lower()))

    # ── Statistici ────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    total_active   = sum(1 for u in users if u.get("is_active"))
    total_inactive = len(users) - total_active

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", len(users))
    c2.metric("Activi", total_active)
    c3.metric("Inactivi", total_inactive)
    c4.metric("Afișați", len(filtered))

    st.markdown("<br>", unsafe_allow_html=True)

    if not filtered:
        st.info("Niciun rezultat pentru filtrele selectate.")
        return

    for u in filtered:
        _user_card(u, tab_prefix)


# ============================================================================
# TAB 1 — Conturi în așteptare
# ============================================================================
with tab_pending:
    st.markdown("### Conturi care așteaptă aprobare")
    st.caption("Utilizatorii de mai jos s-au înregistrat și așteaptă să fie activați.")

    pending = []
    try:
        pending = api.get_pending_users()
    except Exception as e:
        if not handle_api_exception(e):
            try:
                msg = e.response.json().get("detail", str(e))
            except Exception:
                msg = str(e)
            st.error(f"Eroare: {msg}")

    ROLE_LABELS = {
        "nurse": "Asistent Medical", "doctor": "Doctor",
        "manager": "Manager", "inventory_manager": "Manager Inventar",
    }
    ROLE_COLORS = {
        "nurse": "#4a9db3", "doctor": "#2563eb",
        "manager": "#7c3aed", "inventory_manager": "#d97706",
    }

    if not pending:
        st.info("Nu există conturi în așteptare.")
    else:
        st.caption(f"{len(pending)} cont{'uri' if len(pending) != 1 else ''} în așteptare")
        st.markdown("<br>", unsafe_allow_html=True)

        for u in pending:
            role_label = ROLE_LABELS.get(u["role"], u["role"])
            role_color = ROLE_COLORS.get(u["role"], "#64748b")
            dept_name  = dept_map.get(u.get("department_id"), "—")

            col_info, col_app, col_rej = st.columns([5, 1, 1])
            col_info.markdown(
                f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;'
                f'padding:0.6rem 1rem;line-height:1.75;">'
                f'<b>{u["full_name"]}</b> &nbsp;·&nbsp; '
                f'<span style="color:{role_color};font-size:0.85rem;">{role_label}</span><br>'
                f'<span style="color:#64748b;font-size:0.80rem;">{u["email"]}</span>'
                f'<span style="color:#94a3b8;font-size:0.78rem;margin-left:10px;">· {dept_name}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if col_app.button("Aprobă", key=f"pend_act_{u['id']}", type="primary",
                              use_container_width=True):
                try:
                    api.activate_user(u["id"])
                    st.success(f"{u['full_name']} a fost activat.")
                    st.rerun()
                except Exception as e:
                    handle_api_exception(e)

            if col_rej.button("Respinge", key=f"pend_rej_{u['id']}",
                              use_container_width=True):
                try:
                    api.delete_user(u["id"])
                    st.warning(f"Contul {u['full_name']} a fost șters.")
                    st.rerun()
                except Exception as e:
                    handle_api_exception(e)

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)


# ============================================================================
# TAB 2 — Asistenți
# ============================================================================
with tab_nurses:
    st.markdown("### Asistenți Medicali")

    nurses = []
    try:
        nurses = api.get_staff_users(role="nurse")
    except Exception as e:
        if not handle_api_exception(e):
            try:
                msg = e.response.json().get("detail", str(e))
            except Exception:
                msg = str(e)
            st.error(f"Eroare la încărcare asistenți: {msg}")

    _staff_section(nurses, "nurse", "Asistenți")


# ============================================================================
# TAB 3 — Doctori
# ============================================================================
with tab_doctors:
    st.markdown("### Doctori")

    doctors = []
    try:
        doctors = api.get_staff_users(role="doctor")
    except Exception as e:
        if not handle_api_exception(e):
            try:
                msg = e.response.json().get("detail", str(e))
            except Exception:
                msg = str(e)
            st.error(f"Eroare la încărcare doctori: {msg}")

    _staff_section(doctors, "doctor", "Doctori")


# ============================================================================
# TAB 4 — Adaugă manager
# ============================================================================
with tab_manager:
    st.markdown("### Adaugă un manager nou")
    st.caption("Contul creat aici este activ imediat — nu necesită aprobare.")

    with st.form("form_create_manager", clear_on_submit=True):
        full_name = st.text_input("Nume complet", placeholder="Ana Ionescu")
        email     = st.text_input("Email", placeholder="ana.ionescu@spital.ro")
        col_p1, col_p2 = st.columns(2)
        password         = col_p1.text_input("Parolă", type="password",
                                              placeholder="••••••••", help="Minim 6 caractere")
        password_confirm = col_p2.text_input("Confirmă parola", type="password",
                                              placeholder="••••••••")

        submitted = st.form_submit_button("Creează cont manager", type="primary",
                                          use_container_width=True)
        if submitted:
            if not all([full_name, email, password, password_confirm]):
                st.error("Completează toate câmpurile.")
            elif password != password_confirm:
                st.error("Parolele nu se potrivesc.")
            elif len(password) < 6:
                st.error("Parola trebuie să aibă minim 6 caractere.")
            else:
                try:
                    result = api.create_manager(full_name.strip(), email.strip(), password)
                    st.success(
                        f"Cont de manager creat pentru **{result['full_name']}**. "
                        "Se poate autentifica imediat."
                    )
                except Exception as e:
                    if not handle_api_exception(e):
                        try:
                            msg = e.response.json().get("detail", str(e))
                        except Exception:
                            msg = str(e)
                        st.error(msg)
