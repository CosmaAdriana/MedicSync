"""
MedicSync - Management Departamente
Listare, creare și management departamente spitalicești.
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import require_auth, get_user_role, handle_api_exception
from components.navigation import render_top_nav
import cache
import pandas as pd

ROLE_LABELS = {
    "nurse": "Asistent Medical",
    "doctor": "Doctor",
    "manager": "Manager",
    "inventory_manager": "Manager Inventar",
}

st.set_page_config(page_title="Departamente", page_icon="🏛️", layout="wide", initial_sidebar_state="auto")
require_auth()
render_top_nav()

st.title("Departamente")

api = st.session_state.api_client
user_role = get_user_role()

try:
    with st.spinner("Se încarcă departamentele..."):
        departments    = cache.get_departments(api.token)
        hospital_stats = cache.get_hospital_stats(api.token)

    # ========================================================================
    # Departments Table with Statistics
    # ========================================================================
    st.markdown("---")
    st.subheader("Departamente existente")

    if departments:
        stats_map  = {s['department_id']: s for s in hospital_stats}
        dept_stats = []

        for dept in departments:
            s = stats_map.get(dept['id'], {})
            dept_stats.append({
                'ID': dept['id'],
                'Nume Departament': dept['name'],
                'Descriere': dept['description'] or '-',
                'Total Pacienți': s.get('total', 0),
                'Internați': s.get('admitted', 0),
                'Critici': s.get('critical', 0),
            })

        dept_df = pd.DataFrame(dept_stats)

        st.dataframe(
            dept_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID":               st.column_config.NumberColumn("ID",               width="small"),
                "Nume Departament": st.column_config.TextColumn("Nume Departament",   width="medium"),
                "Descriere":        st.column_config.TextColumn("Descriere",          width="large"),
                "Total Pacienți":   st.column_config.NumberColumn("Total Pacienți",   width="small"),
                "Internați":        st.column_config.NumberColumn("Internați",        width="small"),
                "Critici":          st.column_config.NumberColumn("Critici",          width="small",
                                        help="Număr pacienți în stare critică")
            }
        )

        st.caption(f"**Total: {len(departments)} departamente**")

    else:
        st.info("Nu există departamente înregistrate în sistem.")

    st.markdown("---")

    # ========================================================================
    # Department Details Cards
    # ========================================================================
    st.subheader("Detalii")

    if departments:
        cols_per_row = 3
        for i in range(0, len(departments), cols_per_row):
            cols = st.columns(cols_per_row)

            for j, dept in enumerate(departments[i:i+cols_per_row]):
                with cols[j]:
                    s        = stats_map.get(dept['id'], {})
                    total    = s.get('total', 0)
                    admitted = s.get('admitted', 0)
                    critical = s.get('critical', 0)

                    if critical > 0:
                        border_color = "#d62728"
                    elif admitted > 0:
                        border_color = "#2ca02c"
                    else:
                        border_color = "#7f7f7f"

                    _ico_users = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>'
                    _ico_check = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#2ca02c" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'
                    _ico_alert = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#d62728" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:-1px"><polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>'
                    st.markdown(f"""
                    <div style="
                        border-left: 5px solid {border_color};
                        padding: 1rem;
                        background: #f8f9fa;
                        border-radius: 5px;
                        margin-bottom: 1rem;
                    ">
                        <h4 style="margin: 0 0 0.5rem 0;">{dept['name']}</h4>
                        <p style="margin: 0 0 0.5rem 0; font-size: 0.85rem; color: #666;">
                            {dept['description'] or 'Fără descriere'}
                        </p>
                        <hr style="margin: 0.5rem 0;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.9rem;">
                            <span>{_ico_users} Total: <b>{total}</b></span>
                            <span>{_ico_check} Internați: <b>{admitted}</b></span>
                            <span>{_ico_alert} Critici: <b>{critical}</b></span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")

    # ========================================================================
    # Create New Department (Manager Only)
    # ========================================================================
    st.subheader("Adaugă departament")

    if user_role == "manager":
        with st.form("new_department", clear_on_submit=True):
            col1, col2 = st.columns([1, 2])

            with col1:
                name = st.text_input(
                    "Nume Departament *",
                    placeholder="ex: Neurologie",
                    help="Numele departamentului (obligatoriu)"
                )

            with col2:
                description = st.text_area(
                    "Descriere",
                    placeholder="Descriere scurtă a departamentului...",
                    help="Descriere opțională",
                    height=100
                )

            st.markdown("")
            col_submit, _ = st.columns([1, 4])

            with col_submit:
                submit = st.form_submit_button(
                    "Creează",
                    use_container_width=True,
                    type="primary"
                )

            if submit:
                if not name or name.strip() == "":
                    st.error("Numele departamentului este obligatoriu!")
                else:
                    try:
                        result = api.create_department(
                            name=name.strip(),
                            description=description.strip() if description else None
                        )
                        st.success(f"Departament **{result['name']}** creat cu succes!")
                        st.balloons()
                        cache.get_departments.clear()
                        cache.get_hospital_stats.clear()
                        import time; time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        if "409" in str(e) or "există deja" in str(e).lower():
                            st.error(f"Departamentul '{name}' există deja în sistem!")
                        else:
                            st.error(f"Eroare la crearea departamentului: {str(e)}")
    else:
        st.info(f"Doar managerii pot crea departamente noi. Rolul tău actual: **{ROLE_LABELS.get(user_role, user_role)}**")

    # ========================================================================
    # Statistics Summary
    # ========================================================================
    if departments and hospital_stats:
        st.markdown("---")
        st.subheader("Statistici")

        total_p    = sum(s['total']    for s in hospital_stats)
        total_crit = sum(s['critical'] for s in hospital_stats)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Departamente",     len(departments))
        col2.metric("Total Pacienți",         total_p)
        col3.metric("Medie Pacienți/Dept",    f"{total_p/len(departments):.1f}" if departments else "0")
        col4.metric("Total Pacienți Critici", total_crit)

except Exception as e:
    if not handle_api_exception(e):
        st.error(f"Eroare la încărcarea datelor: {str(e)}")
        st.exception(e)
