"""
MedicSync - Dashboard Principal
Overview spital + secție proprie.
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import require_auth, get_user_role, handle_api_exception
from components.navigation import render_top_nav
from components.stats_cards import kpi_card
import cache
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Dashboard", page_icon="🏥", layout="wide", initial_sidebar_state="collapsed")
require_auth()
render_top_nav()

ROLE_LABELS = {
    "nurse": "Asistent Medical",
    "doctor": "Doctor",
    "manager": "Manager",
    "inventory_manager": "Manager Inventar",
}

STATUS_RO = {"admitted": "Internat", "critical": "Critic", "discharged": "Externat"}

api = st.session_state.api_client
user_role = get_user_role()
user = st.session_state.user
user_dept_id = user.get("department_id")

try:
    with st.spinner("Se încarcă datele..."):
        data = cache.fetch_parallel(
            departments    = (cache.get_departments,    api.token),
            hospital_stats = (cache.get_hospital_stats, api.token),
            my_patients    = (cache.get_patients,       api.token),
            inventory      = (cache.get_inventory,      api.token),
        )
    departments    = data["departments"]
    hospital_stats = data["hospital_stats"]
    my_patients    = data["my_patients"]
    inventory      = data["inventory"]

    dept_map = {d['id']: d['name'] for d in departments}

    # ── totale spital din hospital_stats ────────────────────────────────────
    total_admitted   = sum(s['admitted']   for s in hospital_stats)
    total_critical   = sum(s['critical']   for s in hospital_stats)
    total_discharged = sum(s['discharged'] for s in hospital_stats)
    total_patients   = total_admitted + total_critical + total_discharged
    low_stock        = [i for i in inventory if i['current_stock'] < i['min_stock_level']]

    # ============================================================
    # SECȚIUNEA 1 — Overview Spital
    # ============================================================
    st.title("Dashboard")

    if user_role in ("nurse", "doctor") and user_dept_id:
        dept_name = dept_map.get(user_dept_id, f"Secția {user_dept_id}")
        role_label = ROLE_LABELS.get(user_role, user_role)
        full_name = user.get("full_name", "")
        st.markdown(
            f'<div style="background:#EFF6FF;border-left:4px solid #2563EB;'
            f'border-radius:8px;padding:0.6rem 1.1rem;margin-bottom:1rem;font-size:0.9rem;">'
            f'Bună ziua, <b>{full_name}</b> &nbsp;·&nbsp; '
            f'<span style="color:#2563EB;font-weight:600;">{role_label}</span>'
            f' &nbsp;·&nbsp; <b>{dept_name}</b>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.subheader("Situație generală")

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Departamente",      str(len(departments)),  "secții active",            "blue")
    with c2: kpi_card("Pacienți internați", str(total_admitted),   f"{total_patients} total",  "green")
    with c3: kpi_card("Pacienți critici",   str(total_critical),   "necesită atenție urgentă", "red")
    with c4: kpi_card("Sub stoc minim",     str(len(low_stock)),   f"{len(inventory)} produse","orange" if low_stock else "green")

    st.markdown("---")

    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("##### Pacienți pe departament")
        if hospital_stats:
            df_h = pd.DataFrame(hospital_stats)
            df_h = df_h[df_h['total'] > 0]
            if not df_h.empty:
                fig = px.bar(
                    df_h, x='department_name', y='total',
                    color='total', color_continuous_scale='Blues',
                    labels={'total': 'Pacienți', 'department_name': 'Departament'},
                    text='total'
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(showlegend=False, height=350, xaxis_tickangle=-30,
                                  coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nu există pacienți înregistrați.")

    with col_r:
        st.markdown("##### Distribuție status")
        if total_patients > 0:
            fig2 = go.Figure(go.Pie(
                labels=["Internați", "Critici", "Externați"],
                values=[total_admitted, total_critical, total_discharged],
                hole=0.4,
                marker_colors=['#2ca02c', '#d62728', '#7f7f7f']
            ))
            fig2.update_traces(textposition='inside', textinfo='percent+label')
            fig2.update_layout(height=350, showlegend=True)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Nu există pacienți înregistrați.")

    # Tabel departamente
    st.markdown("##### Situație pe departamente")
    if hospital_stats:
        df_table = pd.DataFrame(hospital_stats)[
            ['department_name', 'admitted', 'critical', 'discharged', 'total']
        ]
        df_table.columns = ['Departament', 'Internați', 'Critici', 'Externați', 'Total']
        st.dataframe(df_table, use_container_width=True, hide_index=True)

    # ============================================================
    # SECȚIUNEA 2 — Secția Mea (doar pentru nurse/doctor)
    # ============================================================
    if user_role in ("nurse", "doctor") and user_dept_id:
        st.markdown("---")
        my_dept_name = dept_map.get(user_dept_id, f"Secția {user_dept_id}")
        st.subheader(f"Secția mea — {my_dept_name}")

        my_admitted   = [p for p in my_patients if p['status'] == 'admitted']
        my_critical   = [p for p in my_patients if p['status'] == 'critical']
        my_discharged = [p for p in my_patients if p['status'] == 'discharged']

        mc1, mc2, mc3 = st.columns(3)
        with mc1: kpi_card("Internați",  str(len(my_admitted)),   "", "green")
        with mc2: kpi_card("Critici",    str(len(my_critical)),   "", "red")
        with mc3: kpi_card("Externați",  str(len(my_discharged)), "", "blue")

        if my_patients:
            st.markdown("##### Pacienți activi")
            active = [p for p in my_patients if p['status'] != 'discharged']
            if active:
                df_my = pd.DataFrame(active)[['full_name', 'status', 'admission_date']]
                df_my['status'] = df_my['status'].map(STATUS_RO)
                df_my['admission_date'] = pd.to_datetime(df_my['admission_date']).dt.strftime('%d.%m.%Y')
                df_my.columns = ['Pacient', 'Status', 'Data Internare']
                st.dataframe(df_my, use_container_width=True, hide_index=True)
            else:
                st.info("Nu există pacienți activi în secția ta.")

    st.markdown("---")
    col_r1, col_r2 = st.columns([1, 3])
    with col_r1:
        if st.button("Reîmprospătare", use_container_width=True):
            cache.get_departments.clear()
            cache.get_hospital_stats.clear()
            cache.get_patients.clear()
            cache.get_inventory.clear()
            st.rerun()
    with col_r2:
        st.caption(f"Ultima actualizare: {datetime.now().strftime('%H:%M:%S')} · Date reîmprospătate automat la 30s")

except Exception as e:
    if not handle_api_exception(e):
        st.error(f"❌ Eroare la încărcarea datelor: {str(e)}")
        st.exception(e)
