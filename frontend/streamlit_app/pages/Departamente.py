"""
MedicSync - Management Departamente
Listare, creare și management departamente spitalicești.
"""
import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import require_auth, get_user_role
from components.navigation import render_top_nav
import pandas as pd

ROLE_LABELS = {
    "nurse": "Asistent Medical",
    "doctor": "Doctor",
    "manager": "Manager",
    "inventory_manager": "Manager Inventar",
}

st.set_page_config(page_title="Departamente", page_icon="🏛️", layout="wide")
require_auth()
render_top_nav()

st.title("🏛️ Management Departamente")
st.markdown("### Gestionare departamente și secții spitalicești")

api = st.session_state.api_client
user_role = get_user_role()

# ============================================================================
# Fetch Departments
# ============================================================================
try:
    with st.spinner("Se încarcă departamentele..."):
        departments    = api.get_departments()
        hospital_stats = api.get_hospital_stats()  # date reale pentru toate secțiile

    # ========================================================================
    # Departments Table with Statistics
    # ========================================================================
    st.markdown("---")
    st.subheader("📋 Departamente Existente")

    if departments:
        stats_map = {s['department_id']: s for s in hospital_stats}
        dept_stats = []
        df_patients = pd.DataFrame()  # păstrat pentru compatibilitate cu cardurile de mai jos

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

        # Display table with color coding
        st.dataframe(
            dept_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Nume Departament": st.column_config.TextColumn("Nume Departament", width="medium"),
                "Descriere": st.column_config.TextColumn("Descriere", width="large"),
                "Total Pacienți": st.column_config.NumberColumn("Total Pacienți", width="small"),
                "Internați": st.column_config.NumberColumn("Internați", width="small"),
                "Critici": st.column_config.NumberColumn(
                    "Critici",
                    width="small",
                    help="Număr pacienți în stare critică"
                )
            }
        )

        # Show total
        st.caption(f"**Total: {len(departments)} departamente**")

    else:
        st.info("Nu există departamente înregistrate în sistem.")

    st.markdown("---")

    # ========================================================================
    # Department Details Cards
    # ========================================================================
    st.subheader("📊 Detalii Departamente")

    if departments:
        # Create cards for each department
        cols_per_row = 3
        for i in range(0, len(departments), cols_per_row):
            cols = st.columns(cols_per_row)

            for j, dept in enumerate(departments[i:i+cols_per_row]):
                with cols[j]:
                    s = stats_map.get(dept['id'], {})
                    total    = s.get('total', 0)
                    admitted = s.get('admitted', 0)
                    critical = s.get('critical', 0)

                    # Color based on critical patients
                    if critical > 0:
                        border_color = "#d62728"  # red
                    elif admitted > 0:
                        border_color = "#2ca02c"  # green
                    else:
                        border_color = "#7f7f7f"  # gray

                    # Card HTML
                    card_html = f"""
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
                            <span>👥 Total: <b>{total}</b></span>
                            <span>✅ Internați: <b>{admitted}</b></span>
                            <span>🚨 Critici: <b>{critical}</b></span>
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("---")

    # ========================================================================
    # Create New Department (Manager Only)
    # ========================================================================
    st.subheader("➕ Adaugă Departament Nou")

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
            col_submit, col_cancel = st.columns([1, 4])

            with col_submit:
                submit = st.form_submit_button(
                    "✅ Creează Departament",
                    use_container_width=True,
                    type="primary"
                )

            if submit:
                if not name or name.strip() == "":
                    st.error("⚠️ Numele departamentului este obligatoriu!")
                else:
                    try:
                        result = api.create_department(
                            name=name.strip(),
                            description=description.strip() if description else None
                        )

                        st.success(f"✅ Departament **{result['name']}** creat cu succes!")
                        st.balloons()

                        # Refresh page after 2 seconds
                        import time
                        time.sleep(2)
                        st.rerun()

                    except Exception as e:
                        if "409" in str(e) or "există deja" in str(e).lower():
                            st.error(f"❌ Departamentul '{name}' există deja în sistem!")
                        else:
                            st.error(f"❌ Eroare la crearea departamentului: {str(e)}")

    else:
        st.info(f"ℹ️ Doar managerii pot crea departamente noi. Rolul tău actual: **{ROLE_LABELS.get(user_role, user_role)}**")

    # ========================================================================
    # Department Statistics Summary
    # ========================================================================
    if departments and hospital_stats:
        st.markdown("---")
        st.subheader("📈 Statistici Rezumat")

        total_p   = sum(s['total']    for s in hospital_stats)
        total_crit = sum(s['critical'] for s in hospital_stats)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Departamente",    len(departments))
        col2.metric("Total Pacienți",        total_p)
        col3.metric("Medie Pacienți/Dept",   f"{total_p/len(departments):.1f}" if departments else "0")
        col4.metric("Total Pacienți Critici", total_crit)

except Exception as e:
    st.error(f"❌ Eroare la încărcarea datelor: {str(e)}")
    st.exception(e)
