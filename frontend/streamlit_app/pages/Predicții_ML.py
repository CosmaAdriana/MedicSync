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

st.set_page_config(page_title="Predicții ML", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")
require_auth(allowed_roles=["manager"])
render_top_nav()

st.title("Predicții ML")

api = st.session_state.api_client

# ============================================================================
# Model Info (real, din bundle)
# ============================================================================
@st.cache_data(show_spinner=False, ttl=3600)
def _get_model_info(token: str):
    return api.get_model_info()

try:
    model_info = _get_model_info(api.token)
    r2_pct  = model_info["r2"] * 100
    mae_val = model_info["mae"]
    fi      = model_info["feature_importances"]

    FEAT_LABELS = {
        "department_id": "Departament",
        "is_epidemic":   "Epidemie",
        "weather_temp":  "Temperatură",
        "day_of_week":   "Zi săptămână",
        "month":         "Lună",
        "is_holiday":    "Sărbătoare",
    }

    fi_lines = "\n".join(
        f"- **{FEAT_LABELS.get(k, k)} ({v*100:.1f}%)**"
        for k, v in fi.items()
    )

    st.info(f"""
**Model: RandomForest Regressor** &nbsp;·&nbsp; {model_info['n_estimators']} arbori &nbsp;·&nbsp; adâncime max {model_info['max_depth']}

**Metrici reale:**
- **Acuratețe (R²):** {r2_pct:.2f}%
- **Eroare medie (MAE):** {mae_val} pacienți

**Feature importance:**
{fi_lines}
    """)
except Exception as e:
    handle_api_exception(e)
    st.warning("⚠️ Nu s-au putut încărca informațiile modelului.")
    model_info = None

st.markdown("---")

# ============================================================================
# Departamente
# ============================================================================
try:
    departments  = cache.get_departments(api.token)
    dept_options = {d["name"]: d["id"] for d in departments}
except Exception as e:
    handle_api_exception(e)
    st.error(f"Eroare la încărcarea departamentelor: {str(e)}")
    st.stop()

# ============================================================================
# Tabs
# ============================================================================
tab_zi, tab_trend = st.tabs(["Predicție Zi", "Trend"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Predicție pentru o singură zi, mai multe departamente
# ─────────────────────────────────────────────────────────────────────────────
with tab_zi:
    st.subheader("Configurare")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("##### Parametri temporali")
        target_date = st.date_input(
            "Data Predicție",
            value=date.today() + timedelta(days=1),
            min_value=date.today(),
            max_value=date.today() + timedelta(days=365),
            key="zi_date",
        )
        is_holiday = st.checkbox("Zi de sărbătoare", value=False, key="zi_holiday")

    with col2:
        st.markdown("##### Condiții meteo")
        weather_temp = st.slider(
            "Temperatură Estimată (°C)",
            min_value=-15, max_value=40, value=15, step=1,
            key="zi_temp",
        )
        month = target_date.month
        if month in (12, 1, 2):
            season = "❄️ Iarnă"
        elif month in (3, 4, 5):
            season = "🌸 Primăvară"
        elif month in (6, 7, 8):
            season = "☀️ Vară"
        else:
            season = "🍂 Toamnă"
        st.caption(f"📊 Sezon: {season}")

    with col3:
        st.markdown("##### Condiții epidemiologice")
        is_epidemic = st.checkbox("Perioadă de Epidemie", value=False, key="zi_epidemic")
        if is_epidemic:
            st.warning("⚠️ Modul epidemie activat")

    st.markdown("---")
    st.subheader("Departamente")

    # "Selectează Toate" funcțional prin session_state
    if "zi_depts" not in st.session_state:
        st.session_state["zi_depts"] = list(dept_options.keys())[:3]

    col_sel, col_btn = st.columns([3, 1])
    with col_btn:
        st.markdown("")
        st.markdown("")
        if st.button("Selectează toate", use_container_width=True, key="zi_sel_all"):
            st.session_state["zi_depts"] = list(dept_options.keys())
            st.rerun()

    with col_sel:
        selected_depts = st.multiselect(
            "Selectează departamentele pentru comparație",
            options=list(dept_options.keys()),
            key="zi_depts",
        )

    if not selected_depts:
        st.warning("⚠️ Selectează cel puțin un departament.")
        st.stop()

    st.markdown("---")

    if st.button("Generează predicții", use_container_width=True, type="primary", key="zi_run"):
        results = []
        errors  = []

        progress_bar = st.progress(0)
        status_text  = st.empty()
        status_text.text(f"Se generează {len(selected_depts)} predicții în paralel...")

        def _predict(dept_name: str):
            return api.predict_staff_needs(
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
                    results.append(future.result())
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
            st.subheader("Rezultate")

            df = pd.DataFrame(results)
            display_df = df[["department_name", "predicted_patients", "recommended_nurses"]].copy()
            display_df.columns = ["Departament", "Pacienți Prezis", "Asistente Necesare"]
            st.dataframe(
                display_df, use_container_width=True, hide_index=True,
                column_config={
                    "Departament":        st.column_config.TextColumn(width="medium"),
                    "Pacienți Prezis":    st.column_config.NumberColumn(width="small"),
                    "Asistente Necesare": st.column_config.NumberColumn(width="small"),
                }
            )

            col_s1, col_s2, col_s3 = st.columns(3)
            total_p = sum(r["predicted_patients"] for r in results)
            total_n = sum(r["recommended_nurses"] for r in results)
            col_s1.metric("Total Pacienți Prezis",    total_p)
            col_s2.metric("Total Asistente Necesare", total_n)
            col_s3.metric("Raport Pacienți/Asistent", f"{total_p/total_n:.1f}" if total_n else "—")

            st.markdown("---")
            col_c1, col_c2 = st.columns(2)

            with col_c1:
                fig = px.bar(
                    df, x="department_name", y="predicted_patients",
                    color="predicted_patients", color_continuous_scale="Reds",
                    title="Pacienți Prezis", text="predicted_patients",
                    labels={"predicted_patients": "Pacienți", "department_name": "Departament"},
                )
                fig.update_traces(textposition="outside")
                fig.update_layout(showlegend=False, height=400, xaxis_tickangle=-30,
                                  coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)

            with col_c2:
                fig2 = px.bar(
                    df, x="department_name", y="recommended_nurses",
                    color="recommended_nurses", color_continuous_scale="Blues",
                    title="Asistente Necesare", text="recommended_nurses",
                    labels={"recommended_nurses": "Asistente", "department_name": "Departament"},
                )
                fig2.update_traces(textposition="outside")
                fig2.update_layout(showlegend=False, height=400, xaxis_tickangle=-30,
                                   coloraxis_showscale=False)
                st.plotly_chart(fig2, use_container_width=True)

            st.markdown("---")
            st.download_button(
                label="Descarcă CSV",
                data=df.to_csv(index=False),
                file_name=f"predictii_{target_date}.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.info("Configurează parametrii și apasă **Generează predicții**.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Trend pe 7 sau 30 de zile pentru un departament
# ─────────────────────────────────────────────────────────────────────────────
with tab_trend:
    st.subheader("Predicție Trend")

    col_t1, col_t2, col_t3 = st.columns(3)

    with col_t1:
        trend_dept = st.selectbox(
            "Departament",
            options=list(dept_options.keys()),
            key="trend_dept",
        )
        trend_days = st.radio(
            "Interval",
            options=[7, 14, 30],
            format_func=lambda x: f"{x} zile",
            horizontal=True,
            key="trend_days",
        )

    with col_t2:
        trend_temp = st.slider(
            "Temperatură medie estimată (°C)",
            min_value=-15, max_value=40, value=15, step=1,
            key="trend_temp",
        )
        trend_holiday = st.checkbox("Incluzi sărbători legale", value=False, key="trend_holiday")

    with col_t3:
        trend_epidemic = st.checkbox("Perioadă de epidemie", value=False, key="trend_epidemic")
        if trend_epidemic:
            st.warning("⚠️ Modul epidemie activat")

    st.markdown("---")

    if st.button("Generează trend", use_container_width=True, type="primary", key="trend_run"):
        start = date.today() + timedelta(days=1)
        dates = [start + timedelta(days=i) for i in range(trend_days)]
        dept_id = dept_options[trend_dept]

        results_trend = []
        errors_trend  = []
        progress_bar2 = st.progress(0)

        def _predict_day(d: date):
            return api.predict_staff_needs(
                date=str(d),
                weather_temp=trend_temp,
                department_id=dept_id,
                is_holiday=trend_holiday,
                is_epidemic=trend_epidemic,
            )

        with ThreadPoolExecutor(max_workers=8) as ex:
            futures = {ex.submit(_predict_day, d): d for d in dates}
            done = 0
            for future in as_completed(futures):
                d = futures[future]
                try:
                    r = future.result()
                    r["date"] = str(d)
                    results_trend.append(r)
                except Exception as e:
                    errors_trend.append(f"{d}: {str(e)}")
                done += 1
                progress_bar2.progress(done / len(dates))

        progress_bar2.empty()
        for err in errors_trend:
            st.error(err)

        if results_trend:
            df_t = pd.DataFrame(results_trend).sort_values("date")
            df_t["date"] = pd.to_datetime(df_t["date"])

            st.success(f"✅ Trend generat pentru **{trend_dept}** — următoarele {trend_days} zile")

            fig_t = go.Figure()
            fig_t.add_trace(go.Scatter(
                x=df_t["date"], y=df_t["predicted_patients"],
                name="Pacienți Prezis", mode="lines+markers",
                line=dict(color="#d62728", width=2),
                marker=dict(size=6),
            ))
            fig_t.add_trace(go.Scatter(
                x=df_t["date"], y=df_t["recommended_nurses"],
                name="Asistente Necesare", mode="lines+markers",
                line=dict(color="#1f77b4", width=2, dash="dot"),
                marker=dict(size=6),
                yaxis="y2",
            ))
            fig_t.update_layout(
                title=f"Trend Predicție — {trend_dept}",
                xaxis_title="Dată",
                yaxis=dict(title="Pacienți Prezis", showgrid=True),
                yaxis2=dict(title="Asistente Necesare", overlaying="y", side="right", showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=450,
            )
            st.plotly_chart(fig_t, use_container_width=True)

            st.markdown("---")
            col_stats = st.columns(3)
            col_stats[0].metric("Max pacienți/zi",    int(df_t["predicted_patients"].max()))
            col_stats[1].metric("Min pacienți/zi",    int(df_t["predicted_patients"].min()))
            col_stats[2].metric("Medie asistente/zi", f"{df_t['recommended_nurses'].mean():.1f}")

            st.download_button(
                label="Descarcă CSV",
                data=df_t.to_csv(index=False),
                file_name=f"trend_{trend_dept}_{trend_days}zile.csv",
                mime="text/csv",
                use_container_width=True,
            )
    else:
        st.info("Configurează parametrii și apasă **Generează trend**.")
