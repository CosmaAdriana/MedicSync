"""
MedicSync - Analiză Predictivă (Health 4.0)
Machine Learning pentru predicția nevoilor de personal medical.
"""
import streamlit as st
import sys
import os
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import require_auth, handle_api_exception
from components.navigation import render_top_nav
import cache
from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from components.chart_theme import apply as ct, bars as ct_bars, TEAL, TEAL_MID, SLATE_400, AMBER

st.set_page_config(page_title="Analiză Predictivă", page_icon="📊", layout="wide", initial_sidebar_state="auto")
require_auth(allowed_roles=["manager"])
render_top_nav()

api = st.session_state.api_client


# ── Cached functions ──────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def _get_model_info(token: str):
    from api_client import APIClient
    from config import API_BASE_URL
    c = APIClient(API_BASE_URL)
    c.set_token(token)
    return c.get_model_info()


@st.cache_data(show_spinner=False, ttl=1800)
def _predict_all(token: str, pred_date: str, temp: int, holiday: bool, epidemic: bool) -> list:
    from api_client import APIClient
    from config import API_BASE_URL
    c = APIClient(API_BASE_URL)
    c.set_token(token)
    depts = c.get_departments()

    def _pred(d):
        try:
            return c.predict_staff_needs(
                date=pred_date, weather_temp=temp,
                department_id=d["id"], is_holiday=holiday, is_epidemic=epidemic,
            )
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=8) as ex:
        return [r for r in ex.map(_pred, depts) if r]


# ── Header ────────────────────────────────────────────────────────────────────
st.title("Analiză Predictivă")
st.caption("Model RandomForest antrenat pe istoricul spitalului — estimează necesarul de personal pe departamente")

# ── Model KPIs + Feature Importance ──────────────────────────────────────────
FEAT_LABELS = {
    "department_id": "Departament",
    "is_epidemic":   "Epidemie",
    "weather_temp":  "Temperatură",
    "day_of_week":   "Zi săptămână",
    "month":         "Lună",
    "is_holiday":    "Sărbătoare",
}

try:
    model_info = _get_model_info(api.token)
    r2_pct  = model_info["r2"] * 100
    mae_val = model_info["mae"]
    fi      = model_info["feature_importances"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Acuratețe model (R²)", f"{r2_pct:.1f}%", help="Procentul din variație explicat de model")
    c2.metric("Eroare medie (MAE)", f"{mae_val} pac.", help="Diferența medie față de valoarea reală")
    c3.metric("Arbori de decizie", model_info["n_estimators"])
    c4.metric("Adâncime maximă", model_info["max_depth"])

    st.markdown("")

    fi_df = pd.DataFrame([
        {"Factor": FEAT_LABELS.get(k, k), "Importanță (%)": round(v * 100, 1)}
        for k, v in sorted(fi.items(), key=lambda x: x[1], reverse=True)
    ])

    col_fi, col_desc = st.columns([3, 2])
    with col_fi:
        fig_fi = px.bar(
            fi_df, x="Importanță (%)", y="Factor", orientation="h",
            color_discrete_sequence=[TEAL],
            text=fi_df["Importanță (%)"].map(lambda x: f"{x:.1f}%"),
        )
        ct_bars(fig_fi)
        ct(fig_fi, title="Factori de influență asupra predicțiilor", height=260, legend=False)
        fig_fi.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_fi, use_container_width=True)

    with col_desc:
        st.markdown("#### Cum funcționează modelul?")
        st.markdown(
            "Modelul analizează **6 factori** istorici pentru a estima "
            "câți pacienți vor fi internați și câte asistente sunt necesare zilnic, "
            "per departament."
        )
        st.markdown("")
        if r2_pct >= 85:
            st.success(f"Acuratețe **{r2_pct:.1f}%** — predicții fiabile")
        elif r2_pct >= 70:
            st.info(f"Acuratețe **{r2_pct:.1f}%** — predicții orientative")
        else:
            st.warning(f"Acuratețe **{r2_pct:.1f}%** — interpretați cu precauție")
        st.markdown(
            "**Departamentul** și **ziua săptămânii** sunt cel mai puternici predictori, "
            "urmate de contextul epidemiologic și sezon."
        )

except Exception as e:
    handle_api_exception(e)
    st.warning("Informațiile modelului nu sunt disponibile.")

st.markdown("---")

# ── Departments ───────────────────────────────────────────────────────────────
try:
    departments  = cache.get_departments(api.token)
    dept_options = {d["name"]: d["id"] for d in departments}
except Exception as e:
    handle_api_exception(e)
    st.error(f"Eroare la încărcarea departamentelor: {str(e)}")
    st.stop()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_azi, tab_trend = st.tabs(["Predicție Personal", "Trend"])

# ────────────────────────────────────────────────────────────────────────────
# TAB 1 — Predicție automată pentru mâine (toate departamentele)
# ────────────────────────────────────────────────────────────────────────────
with tab_azi:
    tomorrow = date.today() + timedelta(days=1)

    with st.expander("Personalizează predicția", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            target_date = st.date_input(
                "Data predicției", value=tomorrow,
                min_value=date.today(), max_value=date.today() + timedelta(days=365),
                key="zi_date",
            )
            is_holiday = st.checkbox("Zi de sărbătoare", value=False, key="zi_holiday")
        with col2:
            weather_temp = st.slider("Temperatură estimată (°C)", -15, 40, 15, key="zi_temp")
            is_epidemic  = st.checkbox("Perioadă de epidemie", value=False, key="zi_epidemic")
        with col3:
            filter_depts = st.multiselect(
                "Afișează departamente",
                options=list(dept_options.keys()),
                default=list(dept_options.keys()),
                key="zi_depts",
            )

    try:
        all_results = _predict_all(
            api.token,
            str(target_date),
            weather_temp,
            is_holiday,
            is_epidemic,
        )

        if all_results:
            df = pd.DataFrame(all_results)
            if filter_depts:
                df = df[df["department_name"].isin(filter_depts)]

            date_label = target_date.strftime("%d.%m.%Y") if hasattr(target_date, "strftime") else str(target_date)
            st.markdown(f"#### Estimare pentru **{date_label}**")

            total_p  = int(df["predicted_patients"].sum())
            total_n  = int(df["recommended_nurses"].sum())
            max_dept = df.loc[df["predicted_patients"].idxmax(), "department_name"] if not df.empty else "—"

            cm1, cm2, cm3 = st.columns(3)
            cm1.metric("Total pacienți estimați", total_p)
            cm2.metric("Total asistente necesare", total_n)
            cm3.metric("Cel mai aglomerat", max_dept)

            st.markdown("")

            col_c1, col_c2 = st.columns(2)
            with col_c1:
                fig1 = px.bar(
                    df.sort_values("predicted_patients", ascending=False),
                    x="department_name", y="predicted_patients",
                    color_discrete_sequence=[TEAL],
                    text="predicted_patients",
                    labels={"predicted_patients": "Pacienți", "department_name": "Departament"},
                )
                ct_bars(fig1)
                ct(fig1, title="Pacienți estimați per departament", height=380, legend=False, xangle=-20)
                st.plotly_chart(fig1, use_container_width=True)

            with col_c2:
                fig2 = px.bar(
                    df.sort_values("recommended_nurses", ascending=False),
                    x="department_name", y="recommended_nurses",
                    color_discrete_sequence=[TEAL_MID],
                    text="recommended_nurses",
                    labels={"recommended_nurses": "Asistente", "department_name": "Departament"},
                )
                ct_bars(fig2, color=TEAL_MID)
                ct(fig2, title="Asistente necesare per departament", height=380, legend=False, xangle=-20)
                st.plotly_chart(fig2, use_container_width=True)

            with st.expander("Tabel detaliat", expanded=False):
                disp = df[["department_name", "predicted_patients", "recommended_nurses"]].copy()
                disp.columns = ["Departament", "Pacienți Estimați", "Asistente Necesare"]
                disp["Raport P/A"] = (disp["Pacienți Estimați"] / disp["Asistente Necesare"]).round(1)
                st.dataframe(disp, use_container_width=True, hide_index=True)
                st.download_button(
                    "Descarcă CSV",
                    data=df.to_csv(index=False),
                    file_name=f"predictii_{target_date}.csv",
                    mime="text/csv",
                )
        else:
            st.warning("Nu s-au putut genera predicții pentru data selectată.")

    except Exception as e:
        if not handle_api_exception(e):
            st.error(f"Eroare la generarea predicțiilor: {str(e)}")

# ────────────────────────────────────────────────────────────────────────────
# TAB 2 — Trend pe mai multe zile pentru un departament
# ────────────────────────────────────────────────────────────────────────────
with tab_trend:
    col_ctrl, col_chart = st.columns([1, 3])

    with col_ctrl:
        st.markdown("#### Configurare")
        trend_dept = st.selectbox("Departament", options=list(dept_options.keys()), key="trend_dept")
        trend_days = st.radio(
            "Orizont de predicție",
            options=[7, 14, 30],
            format_func=lambda x: f"{x} zile",
            index=2,
            key="trend_days",
        )
        with st.expander("Parametri avansați"):
            trend_temp     = st.slider("Temperatură medie (°C)", -15, 40, 15, key="trend_temp")
            trend_holiday  = st.checkbox("Include sărbători legale", False, key="trend_holiday")
            trend_epidemic = st.checkbox("Perioadă de epidemie", False, key="trend_epidemic")

        st.markdown("")
        run_trend = st.button("Generează trend", type="primary", use_container_width=True, key="trend_run")

    with col_chart:
        if run_trend:
            start = date.today() + timedelta(days=1)
            dates = [start + timedelta(days=i) for i in range(trend_days)]
            dept_id = dept_options[trend_dept]

            progress = st.progress(0)

            results_trend = []

            def _predict_day(d: date):
                return api.predict_staff_needs(
                    date=str(d), weather_temp=trend_temp,
                    department_id=dept_id, is_holiday=trend_holiday, is_epidemic=trend_epidemic,
                )

            with ThreadPoolExecutor(max_workers=8) as ex:
                futures = {ex.submit(_predict_day, d): d for d in dates}
                from concurrent.futures import as_completed
                done = 0
                for future in as_completed(futures):
                    d = futures[future]
                    try:
                        r = future.result()
                        r["date"] = str(d)
                        results_trend.append(r)
                    except Exception:
                        pass
                    done += 1
                    progress.progress(done / len(dates))

            progress.empty()

            if results_trend:
                df_t = pd.DataFrame(results_trend).sort_values("date")
                df_t["date"] = pd.to_datetime(df_t["date"])

                cs1, cs2, cs3 = st.columns(3)
                cs1.metric("Max pacienți/zi",    int(df_t["predicted_patients"].max()))
                cs2.metric("Min pacienți/zi",    int(df_t["predicted_patients"].min()))
                cs3.metric("Medie asistente/zi", f"{df_t['recommended_nurses'].mean():.1f}")

                st.markdown("")

                fig_t = go.Figure()
                fig_t.add_trace(go.Scatter(
                    x=df_t["date"], y=df_t["predicted_patients"],
                    name="Pacienți estimați", mode="lines+markers",
                    line=dict(color=TEAL, width=2),
                    fill="tozeroy", fillcolor="rgba(74,157,179,0.12)",
                    marker=dict(size=5),
                ))
                fig_t.add_trace(go.Scatter(
                    x=df_t["date"], y=df_t["recommended_nurses"],
                    name="Asistente necesare", mode="lines+markers",
                    line=dict(color=AMBER, width=2, dash="dot"),
                    marker=dict(size=5),
                    yaxis="y2",
                ))
                ct(fig_t, title=f"Trend predicție — {trend_dept}", height=420, dual_y=True)
                fig_t.update_layout(
                    xaxis_title="Dată",
                    yaxis_title="Pacienți estimați",
                    yaxis2_title="Asistente necesare",
                )
                st.plotly_chart(fig_t, use_container_width=True)

                st.download_button(
                    "Descarcă CSV",
                    data=df_t.to_csv(index=False),
                    file_name=f"trend_{trend_dept}_{trend_days}zile.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.error("Nu s-au putut genera predicțiile pentru trending.")
        else:
            st.markdown("")
            st.markdown("")
            st.info("Selectează departamentul și apasă **Generează trend** pentru a vizualiza evoluția pe mai multe zile.")
