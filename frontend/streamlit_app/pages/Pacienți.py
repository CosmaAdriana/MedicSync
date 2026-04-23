"""
MedicSync - Management Pacienți
Evidență pacienți internați cu filtrare, adăugare și externare.
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import require_auth, get_user_role, handle_api_exception
from components.navigation import render_top_nav
import cache
import pandas as pd
from datetime import date

st.set_page_config(page_title="Pacienți", page_icon="👤", layout="wide", initial_sidebar_state="auto")
require_auth(allowed_roles=["doctor", "nurse", "manager"])
render_top_nav()

st.title("Pacienți")

api = st.session_state.api_client
user_role = get_user_role()

# ============================================================================
# Top-level Tabs
# ============================================================================
tab_lista, tab_interneaza, tab_externeaza = st.tabs([
    "Listă pacienți",
    "Internează",
    "Externează / Status",
])

# ============================================================================
# Shared data — cached
# ============================================================================
try:
    departments = cache.get_departments(api.token)
    dept_map    = {d['id']: d['name'] for d in departments}
    dept_id_map = {d['name']: d['id'] for d in departments}
except Exception:
    departments = []
    dept_map    = {}
    dept_id_map = {}

# ============================================================================
# TAB 1 — Listă Pacienți
# ============================================================================
with tab_lista:
    col1, col2 = st.columns([3, 1])

    with col1:
        status_filter = st.selectbox(
            "Status",
            options=["Toate", "admitted", "critical", "discharged"],
            format_func=lambda x: {
                "Toate": "Toate statusurile",
                "admitted": "Internați",
                "critical": "Critici",
                "discharged": "Externați"
            }[x]
        )

    with col2:
        st.markdown("")
        st.markdown("")
        if st.button("Refresh", use_container_width=True):
            cache.get_patients.clear()
            st.rerun()

    st.markdown("---")

    try:
        status_val = status_filter if status_filter != "Toate" else None
        patients = cache.get_patients(api.token, status=status_val)

        st.subheader(f"Pacienți ({len(patients)} rezultate)")

        if patients:
            df = pd.DataFrame(patients)
            df['department_name'] = df['department_id'].map(dept_map).fillna('N/A')
            df['admission_date']  = pd.to_datetime(df['admission_date']).dt.strftime('%d.%m.%Y')

            status_ro = {'admitted': 'Internat', 'critical': 'Critic', 'discharged': 'Externat'}
            df['status_ro'] = df['status'].map(status_ro)

            display_df = df[['id', 'full_name', 'department_name', 'admission_date', 'status_ro']]
            display_df.columns = ['ID', 'Nume Pacient', 'Departament', 'Data Internare', 'Status']

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ID":            st.column_config.NumberColumn("ID",            width="small"),
                    "Nume Pacient":  st.column_config.TextColumn("Nume Pacient",    width="medium"),
                    "Departament":   st.column_config.TextColumn("Departament",     width="medium"),
                    "Data Internare":st.column_config.TextColumn("Data Internare",  width="small"),
                    "Status":        st.column_config.TextColumn("Status",          width="small")
                }
            )

            st.caption(
                f"**Total:** {len(patients)} | "
                f"**Internați:** {len([p for p in patients if p['status'] == 'admitted'])} | "
                f"**Critici:** {len([p for p in patients if p['status'] == 'critical'])} | "
                f"**Externați:** {len([p for p in patients if p['status'] == 'discharged'])}"
            )
        else:
            st.info("Nu există pacienți cu filtrele selectate.")

    except Exception as e:
        if not handle_api_exception(e):
            st.error(f"Eroare la încărcarea datelor: {str(e)}")
            st.exception(e)

# ============================================================================
# TAB 2 — Internează Pacient
# ============================================================================
with tab_interneaza:
    st.subheader("Internează pacient nou")

    with st.form("new_patient", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            full_name = st.text_input(
                "Nume Complet *",
                placeholder="Ion Popescu",
                help="Numele complet al pacientului (obligatoriu)"
            )

            if departments:
                dept_select = st.selectbox(
                    "Departament *",
                    options=list(dept_id_map.keys()),
                    help="Selectează departamentul de internare"
                )
            else:
                st.error("Nu există departamente disponibile!")
                dept_select = None

        with col2:
            admission_date = st.date_input(
                "Data Internare *",
                value=date.today(),
                max_value=date.today()
            )

            new_status = st.selectbox(
                "Status Inițial",
                options=["admitted", "critical"],
                format_func=lambda x: {
                    "admitted": "Internat (stabil)",
                    "critical": "Critic (necesită atenție urgentă)"
                }[x]
            )

        st.markdown("")
        col_btn, _ = st.columns([1, 3])
        with col_btn:
            submit = st.form_submit_button(
                "Internează",
                use_container_width=True,
                type="primary"
            )

        if submit:
            if not full_name or full_name.strip() == "":
                st.error("Numele pacientului este obligatoriu!")
            elif not dept_select:
                st.error("Selectează un departament!")
            else:
                try:
                    result = api.create_patient(
                        full_name=full_name.strip(),
                        department_id=dept_id_map[dept_select],
                        admission_date=str(admission_date),
                        status=new_status
                    )
                    st.success(f"Pacient **{result['full_name']}** internat cu succes în {dept_select}!")
                    st.info(f"ID Pacient: {result['id']}")
                    st.balloons()
                    cache.get_patients.clear()
                    cache.get_hospital_stats.clear()
                    import time; time.sleep(2)
                    st.rerun()
                except Exception as e:
                    if not handle_api_exception(e):
                        st.error(f"Eroare la internarea pacientului: {str(e)}")

# ============================================================================
# TAB 3 — Externează Pacient
# ============================================================================
with tab_externeaza:
    if user_role not in ["doctor", "manager"]:
        st.markdown("""
            <div style="
                text-align: center;
                padding: 3rem 2rem;
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                border-radius: 16px;
                border: 1px solid #dee2e6;
                margin: 2rem auto;
                max-width: 600px;
            ">
                <div style="margin-bottom: 1rem;"><svg xmlns="http://www.w3.org/2000/svg" width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="#6c757d" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></div>
                <h2 style="color: #495057; margin-bottom: 0.5rem;">Secțiune restricționată</h2>
                <p style="color: #6c757d; font-size: 1.1rem;">
                    Doar medicii și managerii pot externa pacienți.
                </p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.subheader("Actualizează status pacient")
        st.info("Externarea este ireversibilă fără intervenția unui manager.")

        try:
            admitted  = cache.get_patients(api.token, status="admitted")
            critical  = cache.get_patients(api.token, status="critical")
            active_patients = admitted + critical

            if not active_patients:
                st.warning("Nu există pacienți activi (internați sau critici) în sistem.")
            else:
                patient_options = {
                    f"{p['full_name']} (ID: {p['id']}) — {p['status'].upper()}": p
                    for p in active_patients
                }

                selected_key = st.selectbox(
                    "Selectează pacientul",
                    options=list(patient_options.keys()),
                    help="Alege pacientul pe care dorești să îl externezi"
                )

                selected = patient_options[selected_key]

                col_info, col_action = st.columns([2, 1])

                with col_info:
                    dept_name = dept_map.get(selected['department_id'], 'N/A')
                    adm_date  = pd.to_datetime(selected['admission_date']).strftime('%d.%m.%Y')
                    st.markdown(f"""
                    | Câmp | Valoare |
                    |------|---------|
                    | **ID** | {selected['id']} |
                    | **Nume** | {selected['full_name']} |
                    | **Departament** | {dept_name} |
                    | **Data Internare** | {adm_date} |
                    | **Status Curent** | {selected['status'].upper()} |
                    """)

                with col_action:
                    st.markdown("#### Nou Status")
                    new_status = st.selectbox(
                        "Alege statusul",
                        options=["discharged", "admitted", "critical"],
                        format_func=lambda x: {
                            "discharged": "Externat",
                            "admitted":   "Internat (stabil)",
                            "critical":   "Critic"
                        }[x],
                        label_visibility="collapsed"
                    )

                st.markdown("")

                if new_status == "discharged":
                    st.warning(f"Ești pe cale să externezi pacientul **{selected['full_name']}**.")

                col_btn, _ = st.columns([1, 3])
                with col_btn:
                    confirm = st.button(
                        "Confirmă" if new_status != "discharged" else "Externează pacient",
                        type="primary",
                        use_container_width=True
                    )

                if confirm:
                    try:
                        result = api.update_patient_status(selected['id'], new_status)
                        if new_status == "discharged":
                            st.success(f"Pacientul **{result['full_name']}** a fost externat cu succes!")
                            st.balloons()
                        else:
                            st.success(f"Statusul pacientului **{result['full_name']}** a fost actualizat la **{new_status}**!")
                        cache.get_patients.clear()
                        cache.get_hospital_stats.clear()
                        import time; time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        if not handle_api_exception(e):
                            st.error(f"Eroare la actualizarea statusului: {str(e)}")

        except Exception as e:
            if not handle_api_exception(e):
                st.error(f"Eroare la încărcarea datelor: {str(e)}")
                st.exception(e)
