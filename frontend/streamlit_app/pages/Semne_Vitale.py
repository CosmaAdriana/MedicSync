"""
MedicSync - Semne Vitale & Monitorizare
Înregistrare și vizualizare semne vitale cu sistem de alertare automată.
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import require_auth, get_user_role, handle_api_exception
from components.navigation import render_top_nav
from components.chart_theme import apply as ct, lines as ct_lines, TEAL, TEAL_MID, SLATE_400, RED, AMBER
import cache
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Semne Vitale", page_icon="💓", layout="wide", initial_sidebar_state="auto")
require_auth(allowed_roles=["nurse", "doctor"])
render_top_nav()

RISK_LABELS = {
    "critical": ("", "Critic"),
    "high":     ("", "Ridicat"),
    "medium":   ("", "Mediu"),
    "low":      ("", "Scăzut"),
}

STATUS_RO = {
    "admitted":  "Internat",
    "critical":  "Critic",
    "discharged":"Externat",
}

st.title("Semne Vitale")

api = st.session_state.api_client
user_role = get_user_role()

# ============================================================================
# Patient Selection
# ============================================================================
st.subheader("Selectare pacient")

try:
    pts = cache.fetch_parallel(
        admitted = (cache.get_patients, api.token, "admitted"),
        critical = (cache.get_patients, api.token, "critical"),
    )
    patients = pts["admitted"] + pts["critical"]

    if not patients:
        st.warning("Nu există pacienți internați în secția ta în acest moment.")
        st.stop()

    patient_options = {
        f"{p['full_name']} (ID: {p['id']}) — {STATUS_RO.get(p['status'], p['status'])}": p['id']
        for p in patients
    }

    selected_patient_key = st.selectbox(
        "Selectează pacient pentru monitorizare",
        options=list(patient_options.keys()),
    )

    patient_id       = patient_options[selected_patient_key]
    selected_patient = next(p for p in patients if p['id'] == patient_id)

    st.success(f"Pacient selectat: **{selected_patient['full_name']}**")
    st.markdown("---")

    # ========================================================================
    # Fetch Vitals and Alerts — cached per patient
    # ========================================================================
    _vit_alrt = cache.fetch_parallel(
        vitals = (cache.get_patient_vitals, api.token, patient_id),
        alerts = (cache.get_patient_alerts, api.token, patient_id),
    )
    vitals = _vit_alrt["vitals"]
    alerts = _vit_alrt["alerts"]

    # ========================================================================
    # Clinical Alerts Section
    # ========================================================================
    st.subheader("Alerte clinice active")

    unresolved_alerts = [a for a in alerts if not a['is_resolved']]

    if unresolved_alerts:
        st.error(f"**{len(unresolved_alerts)} ALERTE ACTIVE** pentru acest pacient!")

        for alert in unresolved_alerts[:5]:
            icon, label = RISK_LABELS.get(alert['risk_level'], ("", alert['risk_level']))
            alert_time  = datetime.fromisoformat(alert['created_at'].replace('Z', ''))

            _risk_colors = {"Critic": "#dc2626", "Ridicat": "#ea580c", "Mediu": "#ca8a04", "Scăzut": "#16a34a"}
            _dot = f'<span style="color:{_risk_colors.get(label, "#64748b")};font-size:1.1em">●</span>'
            col_msg, col_btn = st.columns([4, 1])
            with col_msg:
                st.markdown(f"""
                <div style="background:#fefce8;border:1px solid #fde68a;border-radius:8px;padding:0.75rem 1rem;font-size:0.875rem;">
                {_dot} <b>[{label.upper()}]</b> {alert['message']}<br>
                <span style="color:#64748b;font-size:0.8rem;">{alert_time.strftime('%d.%m.%Y %H:%M')} · ID Alertă: {alert['id']}</span>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                st.markdown("")
                st.markdown("")
                if st.button(
                    "Rezolvată",
                    key=f"resolve_{alert['id']}",
                    use_container_width=True,
                    help="Marchează alerta ca rezolvată"
                ):
                    try:
                        api.resolve_alert(patient_id, alert['id'])
                        st.success("Alertă marcată ca rezolvată!")
                        cache.get_patient_alerts.clear()
                        cache.get_patients.clear()
                        cache.get_hospital_stats.clear()
                        cache.get_notifications_summary.clear()
                        st.rerun()
                    except Exception as e:
                        if not handle_api_exception(e):
                            st.error(f"Eroare: {str(e)}")

        if len(unresolved_alerts) > 5:
            st.info(f"+{len(unresolved_alerts) - 5} alerte suplimentare")

    else:
        st.success("Nu există alerte active pentru acest pacient!")

    st.markdown("---")

    # ========================================================================
    # Vitals History Chart
    # ========================================================================
    st.subheader("Istoric semne vitale")

    if vitals and len(vitals) > 0:
        times     = [datetime.fromisoformat(v['recorded_at'].replace('Z', '')) for v in vitals]
        pulse     = [v['pulse'] for v in vitals]
        o2_sat    = [v['oxygen_saturation'] for v in vitals]
        resp_rate = [v['respiratory_rate'] for v in vitals]

        bp_systolic, bp_diastolic = [], []
        for v in vitals:
            try:
                sys_val, dia_val = v['blood_pressure'].split('/')
                bp_systolic.append(int(sys_val))
                bp_diastolic.append(int(dia_val))
            except Exception:
                bp_systolic.append(None)
                bp_diastolic.append(None)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=times, y=pulse,     name='Puls (bpm)',
                                  line=dict(color=TEAL, width=2), mode='lines+markers'))
        fig.add_trace(go.Scatter(x=times, y=o2_sat,    name='SpO₂ (%)',
                                  line=dict(color=SLATE_400, width=2), mode='lines+markers'))
        fig.add_trace(go.Scatter(x=times, y=resp_rate, name='Frecv. Respiratorie (rpm)',
                                  line=dict(color=TEAL_MID, width=2), mode='lines+markers'))
        fig.add_hline(y=92,  line_dash="dot", line_color=RED,  line_width=1,
                      annotation_text="SpO₂ critic <92%",
                      annotation_font=dict(size=12, color=RED))
        fig.add_hline(y=150, line_dash="dot", line_color=AMBER, line_width=1,
                      annotation_text="Puls critic >150 bpm",
                      annotation_font=dict(size=12, color=AMBER))
        ct_lines(fig)
        ct(fig, title="Evoluție Semne Vitale", height=460)
        fig.update_layout(xaxis_title="Data/Ora", yaxis_title="Valoare")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Tensiune arterială")
        fig_bp = go.Figure()
        fig_bp.add_trace(go.Scatter(x=times, y=bp_systolic,  name='Sistolică (mmHg)',
                                     line=dict(color=RED, width=2), mode='lines+markers'))
        fig_bp.add_trace(go.Scatter(x=times, y=bp_diastolic, name='Diastolică (mmHg)',
                                     line=dict(color=AMBER, width=2), mode='lines+markers'))
        fig_bp.add_hline(y=180, line_dash="dot", line_color=RED,  line_width=1,
                         annotation_text="Hipertensiune critică >180",
                         annotation_font=dict(size=12, color=RED))
        fig_bp.add_hline(y=90,  line_dash="dot", line_color=AMBER, line_width=1,
                         annotation_text="Hipotensiune <90",
                         annotation_font=dict(size=12, color=AMBER))
        ct_lines(fig_bp)
        ct(fig_bp, title="Evoluție Tensiune Arterială", height=380)
        fig_bp.update_layout(xaxis_title="Data/Ora", yaxis_title="mmHg")
        st.plotly_chart(fig_bp, use_container_width=True)

        st.markdown("#### Înregistrări")
        vitals_df = pd.DataFrame(vitals)
        vitals_df['recorded_at'] = pd.to_datetime(vitals_df['recorded_at']).dt.strftime('%d.%m.%Y %H:%M')
        display_vitals = vitals_df[['recorded_at', 'blood_pressure', 'pulse', 'respiratory_rate', 'oxygen_saturation']]
        display_vitals.columns = ['Data/Ora', 'TA (mmHg)', 'Puls (bpm)', 'Respirație (rpm)', 'SpO₂ (%)']
        st.dataframe(display_vitals.head(10), use_container_width=True, hide_index=True)
        st.caption(f"Ultimele 10 din {len(vitals)} înregistrări")

    else:
        st.info("Nu există înregistrări de semne vitale pentru acest pacient.")

    st.markdown("---")

    # ========================================================================
    # Record New Vitals (Nurse Only)
    # ========================================================================
    st.subheader("Înregistrează semne vitale")

    if user_role == "nurse":
        with st.form("new_vitals", clear_on_submit=False):
            st.markdown("##### Semne vitale noi")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Tensiune Arterială**")
                col_sys, col_dia = st.columns(2)
                with col_sys:
                    bp_sys = st.number_input("Sistolică (mmHg)", min_value=60, max_value=250, value=120, step=1)
                with col_dia:
                    bp_dia = st.number_input("Diastolică (mmHg)", min_value=40, max_value=150, value=80, step=1)
                pulse_input = st.number_input("Puls (bpm)", min_value=30, max_value=220, value=75, step=1,
                                               help="Normal: 60-100 bpm")

            with col2:
                resp_input = st.number_input("Frecvență Respiratorie (rpm)", min_value=5, max_value=60,
                                              value=16, step=1, help="Normal: 12-20 rpm")
                o2_input   = st.number_input("Saturație Oxigen — SpO₂ (%)", min_value=50.0, max_value=100.0,
                                              value=98.0, step=0.1, help="Normal: >95%")

            st.markdown("")
            col_btn, col_info = st.columns([1, 2])
            with col_btn:
                submit = st.form_submit_button("Salvează", use_container_width=True, type="primary")
            with col_info:
                st.caption("Sistemul analizează automat valorile și generează alerte dacă depășesc pragurile clinice.")

            if submit:
                try:
                    result = api.record_vitals(
                        patient_id=patient_id,
                        blood_pressure=f"{bp_sys}/{bp_dia}",
                        pulse=pulse_input,
                        respiratory_rate=resp_input,
                        oxygen_saturation=o2_input
                    )
                    st.success("Semne vitale înregistrate cu succes!")
                    if result.get('alert'):
                        alert = result['alert']
                        icon, label = RISK_LABELS.get(alert['risk_level'], ("", alert['risk_level']))
                        st.error(f"ALERTĂ CLINICĂ! [{label.upper()}] {alert['message']}")
                    else:
                        st.info("Valorile sunt în limite normale.")
                    cache.get_patient_vitals.clear()
                    cache.get_patient_alerts.clear()
                    cache.get_patients.clear()
                    cache.get_hospital_stats.clear()
                    cache.get_notifications_summary.clear()
                    st.rerun()
                except Exception as e:
                    if not handle_api_exception(e):
                        st.error(f"Eroare la salvare: {str(e)}")
    else:
        st.info("Doar asistenții medicali pot înregistra semne vitale noi.")

except Exception as e:
    if not handle_api_exception(e):
        st.error(f"Eroare la încărcarea datelor: {str(e)}")
        st.exception(e)
