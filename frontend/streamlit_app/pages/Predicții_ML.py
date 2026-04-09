"""
MedicSync - Predicții ML (Health 4.0)
Machine Learning pentru predicția nevoilor de personal medical.
"""
import streamlit as st
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import require_auth, handle_api_exception
from components.navigation import render_top_nav
import cache
from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Predicții ML", page_icon="🤖", layout="wide")
require_auth(allowed_roles=["manager"])
render_top_nav()

st.title("🤖 Predicții ML - Health 4.0")
st.markdown("### Optimizare Personal Medical bazată pe Inteligență Artificială")

api = st.session_state.api_client

# ============================================================================
# Info Section
# ============================================================================
st.info("""
🧠 **Model Machine Learning: RandomForest Regressor**

Modelul este antrenat pe **3 ani de date istorice** (5,480 înregistrări) și prezice numărul de pacienți și personalul necesar pentru fiecare departament.

📊 **Metrici Model:**
- **Accuracy (R²):** 93.37% - model foarte precis
- **Eroare Medie (MAE):** 6.09 pacienți
- **Feature-uri:** departament, sezonalitate, vreme, sărbători, epidemii
""")

st.markdown("---")

# ============================================================================
# Prediction Configuration
# ============================================================================
st.subheader("📊 Configurare Predicție")

try:
    departments  = cache.get_departments(api.token)
    dept_options = {d['name']: d['id'] for d in departments}
except Exception as e:
    handle_api_exception(e)
    st.error(f"Eroare la încărcarea departamentelor: {str(e)}")
    st.stop()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("##### 📅 Parametri Temporali")

    target_date = st.date_input(
        "Data Predicție",
        value=date.today() + timedelta(days=1),
        min_value=date.today(),
        max_value=date.today() + timedelta(days=365),
        help="Selectează data pentru care vrei predicția"
    )

    is_holiday = st.checkbox(
        "Zi de sărbătoare",
        value=False,
        help="Marchează dacă data selectată este sărbătoare legală"
    )

with col2:
    st.markdown("##### 🌡️ Condiții Meteo")

    weather_temp = st.slider(
        "Temperatură Estimată (°C)",
        min_value=-15,
        max_value=40,
        value=15,
        step=1,
        help="Temperatura estimată pentru data selectată"
    )

    st.caption(f"📊 Sezon: {'❄️ Iarnă' if weather_temp < 5 else '🌸 Primăvară' if weather_temp < 15 else '☀️ Vară' if weather_temp < 25 else '🍂 Toamnă'}")

with col3:
    st.markdown("##### 🦠 Condiții Epidemiologice")

    is_epidemic = st.checkbox(
        "Perioadă de Epidemie",
        value=False,
        help="Marchează dacă există epidemie activă (gripă, COVID, etc.)"
    )

    if is_epidemic:
        st.warning("⚠️ Modul epidemie activat - predicțiile vor fi majorate!")

st.markdown("---")

# ============================================================================
# Department Selection
# ============================================================================
st.subheader("🏛️ Selectare Departamente")

col_select1, col_select2 = st.columns([3, 1])

with col_select1:
    selected_depts = st.multiselect(
        "Selectează departamentele pentru comparație",
        options=list(dept_options.keys()),
        default=list(dept_options.keys())[:3],
        help="Poți selecta unul sau mai multe departamente"
    )

with col_select2:
    st.markdown("")
    st.markdown("")
    if st.button("✅ Selectează Toate", use_container_width=True):
        selected_depts = list(dept_options.keys())
        st.rerun()

if not selected_depts:
    st.warning("⚠️ Selectează cel puțin un departament pentru predicție.")
    st.stop()

st.markdown("---")

# ============================================================================
# Generate Predictions Button
# ============================================================================
if st.button("🚀 Generează Predicții", use_container_width=True, type="primary"):
    results = []
    errors  = []

    progress_bar = st.progress(0)
    status_text  = st.empty()
    status_text.text(f"Se generează {len(selected_depts)} predicții în paralel...")

    def _predict(dept_name: str):
        return dept_name, api.predict_staff_needs(
            date=str(target_date),
            weather_temp=weather_temp,
            department_id=dept_options[dept_name],
            is_holiday=is_holiday,
            is_epidemic=is_epidemic,
        )

    n = len(selected_depts)
    with ThreadPoolExecutor(max_workers=min(n, 8)) as ex:
        futures = {ex.submit(_predict, name): name for name in selected_depts}
        done = 0
        for future in as_completed(futures):
            dept_name = futures[future]
            try:
                _, result = future.result()
                results.append(result)
            except Exception as e:
                errors.append(f"Eroare la {dept_name}: {str(e)}")
            done += 1
            progress_bar.progress(done / n)

    for err in errors:
        st.error(err)

    status_text.empty()
    progress_bar.empty()

    if results:
        st.success(f"✅ {len(results)} predicții generate cu succes!")

        st.markdown("---")
        st.subheader("📊 Rezultate Predicții")

        df = pd.DataFrame(results)
        display_df = df[['department_name', 'predicted_patients', 'recommended_nurses']]
        display_df.columns = ['Departament', 'Pacienți Prezis', 'Asistente Necesare']

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Departament":        st.column_config.TextColumn("Departament",      width="medium"),
                "Pacienți Prezis":    st.column_config.NumberColumn("Pacienți Prezis", width="small"),
                "Asistente Necesare": st.column_config.NumberColumn("Asistente Necesare", width="small"),
            }
        )

        col_sum1, col_sum2, col_sum3 = st.columns(3)
        total_patients = sum([r['predicted_patients'] for r in results])
        total_nurses   = sum([r['recommended_nurses'] for r in results])
        avg_ratio      = total_patients / total_nurses if total_nurses > 0 else 0

        col_sum1.metric("Total Pacienți Prezis",    total_patients)
        col_sum2.metric("Total Asistente Necesare", total_nurses)
        col_sum3.metric("Raport Pacienți/Asistent", f"{avg_ratio:.1f}")

        st.markdown("---")
        st.subheader("📈 Comparație Vizuală Departamente")

        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            fig_patients = px.bar(
                df, x='department_name', y='predicted_patients',
                color='predicted_patients', color_continuous_scale='Reds',
                title='Pacienți Prezis pe Departament',
                labels={'predicted_patients': 'Pacienți', 'department_name': 'Departament'},
                text='predicted_patients'
            )
            fig_patients.update_traces(textposition='outside')
            fig_patients.update_layout(showlegend=False, height=450, xaxis_tickangle=-45)
            st.plotly_chart(fig_patients, use_container_width=True)

        with col_chart2:
            fig_nurses = px.bar(
                df, x='department_name', y='recommended_nurses',
                color='recommended_nurses', color_continuous_scale='Blues',
                title='Asistente Necesare pe Departament',
                labels={'recommended_nurses': 'Asistente', 'department_name': 'Departament'},
                text='recommended_nurses'
            )
            fig_nurses.update_traces(textposition='outside')
            fig_nurses.update_layout(showlegend=False, height=450, xaxis_tickangle=-45)
            st.plotly_chart(fig_nurses, use_container_width=True)

        st.markdown("#### 📊 Comparație Directă")
        fig_comparison = go.Figure()
        fig_comparison.add_trace(go.Bar(
            x=df['department_name'], y=df['predicted_patients'],
            name='Pacienți Prezis', marker_color='#d62728',
            text=df['predicted_patients'], textposition='outside'
        ))
        fig_comparison.add_trace(go.Bar(
            x=df['department_name'], y=df['recommended_nurses'],
            name='Asistente Necesare', marker_color='#1f77b4',
            text=df['recommended_nurses'], textposition='outside'
        ))
        fig_comparison.update_layout(
            title='Comparație Pacienți vs. Personal Necesar',
            xaxis_title='Departament', yaxis_title='Număr',
            barmode='group', height=500, xaxis_tickangle=-45,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_comparison, use_container_width=True)

        st.markdown("---")
        st.subheader("🎯 Metrici Model Machine Learning")

        col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
        col_metric1.metric("Accuracy (R²)",      f"{results[0]['model_r2']:.2%}")
        col_metric2.metric("Eroare Medie (MAE)", f"{results[0]['model_mae']} pacienți")
        col_metric3.metric("Dataset Training",   "5,480 înregistrări")
        col_metric4.metric("Feature-uri",        "6 variabile")

        with st.expander("ℹ️ Detalii despre Model", expanded=False):
            st.markdown("""
            ### 🧠 Arhitectura Modelului

            **Algoritm:** RandomForest Regressor
            - **Estimatori:** 100 arbori de decizie
            - **Adâncime maximă:** 12 nivele
            - **Split:** 80% training / 20% testing

            **Feature Importance:**
            1. **Department ID (45.74%)** - Cel mai important factor
            2. **Is Epidemic (30.86%)** - Impact major asupra fluxului
            3. **Weather Temp (21.55%)** - Sezonalitate
            4. **Day of Week (0.96%)** - Variații zilnice minore
            5. **Month (0.84%)** - Tendințe lunare
            6. **Is Holiday (0.05%)** - Impact redus
            """)

        st.markdown("---")
        st.subheader("💾 Export Rezultate")

        col_export1, col_export2 = st.columns(2)
        with col_export1:
            st.download_button(
                label="📥 Descarcă CSV",
                data=df.to_csv(index=False),
                file_name=f"predictii_ml_{target_date}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_export2:
            st.button(
                "📊 Generează Raport Excel",
                use_container_width=True,
                disabled=True,
                help="În curând"
            )

else:
    st.info("👆 Configurează parametrii și apasă butonul 'Generează Predicții' pentru a obține rezultatele.")
