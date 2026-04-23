"""
MedicSync — Predicții Stoc Inventar
Consum istoric, trend și recomandări de comandă pentru inventory_manager.
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import require_auth, handle_api_exception
from components.navigation import render_top_nav
import pandas as pd
import plotly.express as px
from components.chart_theme import apply as ct, bars as ct_bars, TEAL, SLATE_400, AMBER

st.set_page_config(page_title="Predicții Stoc", page_icon="📊", layout="wide",
                   initial_sidebar_state="auto")
require_auth(allowed_roles=["inventory_manager", "manager"])
render_top_nav()

st.title("Predicții Stoc")
st.caption("Recomandări de comandă bazate pe consumul real din ultimele 30 de zile.")

api = st.session_state.api_client

try:
    stats = api.get_consumption_stats()
except Exception as e:
    if not handle_api_exception(e):
        st.error(f"Eroare la încărcarea datelor: {str(e)}")
    st.stop()

if not stats:
    st.info("Nu există date de consum înregistrate încă. Datele se acumulează pe măsură ce asistenții scad stocuri.")
    st.stop()

df = pd.DataFrame(stats)

# ── Metrici sumar ────────────────────────────────────────────────────────────
urgent   = df[df['days_until_stockout'].notna() & (df['days_until_stockout'] < 7)]
warning  = df[df['days_until_stockout'].notna() & (df['days_until_stockout'].between(7, 30))]
no_data  = df[df['total_used_30d'] == 0]
to_order = df[df['recommended_order_qty'] > 0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Produse analizate",      len(df))
c2.metric("Epuizare < 7 zile",      len(urgent),  delta=None)
c3.metric("Epuizare 7–30 zile",     len(warning))
c4.metric("Necesită comandă",       len(to_order))

st.markdown("---")

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_rec, tab_consum, tab_urgente = st.tabs([
    "Recomandări comandă", "Consum per produs", "Urgente"
])

# ── TAB 1 — Recomandări ──────────────────────────────────────────────────────
with tab_rec:
    st.subheader("Cantități recomandate pentru următoarea comandă")
    st.caption("Calculat pentru a acoperi 30 de zile de consum pornind de la stocul curent.")

    rec_df = df[df['recommended_order_qty'] > 0].copy()

    if rec_df.empty:
        st.success("Stocurile sunt suficiente pentru următoarele 30 de zile.")
    else:
        rec_df['valoare_estimata'] = rec_df['recommended_order_qty'] * rec_df['unit_price']

        display = rec_df[[
            'product_name', 'department_name', 'current_stock',
            'min_stock_level', 'avg_daily_7d', 'recommended_order_qty', 'valoare_estimata'
        ]].copy()
        display.columns = [
            'Produs', 'Departament', 'Stoc Curent',
            'Stoc Minim', 'Consum Mediu/Zi (7z)', 'Cantitate Recomandată', 'Valoare Est. (RON)'
        ]
        display['Valoare Est. (RON)'] = display['Valoare Est. (RON)'].apply(lambda x: f"{x:,.2f}")
        display['Consum Mediu/Zi (7z)'] = display['Consum Mediu/Zi (7z)'].apply(lambda x: f"{x:.2f}")

        st.dataframe(display, use_container_width=True, hide_index=True)

        total_val = rec_df['valoare_estimata'].sum()
        st.markdown(f"**Valoare totală estimată comandă: {total_val:,.2f} RON**")

        st.markdown("---")
        fig = px.bar(
            rec_df.sort_values('recommended_order_qty', ascending=False),
            x='product_name', y='recommended_order_qty',
            color_discrete_sequence=[TEAL],
            labels={'product_name': 'Produs', 'recommended_order_qty': 'Cantitate'},
            text='recommended_order_qty',
        )
        ct_bars(fig)
        ct(fig, title="Cantitate recomandată per produs", height=380, legend=False, xangle=-30)
        st.plotly_chart(fig, use_container_width=True)

# ── TAB 2 — Consum per produs ────────────────────────────────────────────────
with tab_consum:
    st.subheader("Consum înregistrat")

    has_data = df[df['total_used_30d'] > 0].copy()

    if has_data.empty:
        st.info("Nu există consum înregistrat încă.")
    else:
        display2 = has_data[[
            'product_name', 'department_name', 'total_used_7d',
            'total_used_30d', 'avg_daily_7d', 'avg_daily_30d',
            'current_stock', 'days_until_stockout'
        ]].copy()
        display2.columns = [
            'Produs', 'Departament', 'Folosit (7z)', 'Folosit (30z)',
            'Medie/Zi (7z)', 'Medie/Zi (30z)', 'Stoc Curent', 'Zile Până Epuizare'
        ]
        display2['Zile Până Epuizare'] = display2['Zile Până Epuizare'].apply(
            lambda x: f"{x:.0f}" if pd.notna(x) else "—"
        )

        st.dataframe(
            display2, use_container_width=True, hide_index=True,
            column_config={
                "Medie/Zi (7z)":  st.column_config.NumberColumn(format="%.2f"),
                "Medie/Zi (30z)": st.column_config.NumberColumn(format="%.2f"),
            }
        )

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fig2 = px.bar(
                has_data.sort_values('total_used_30d', ascending=False).head(10),
                x='product_name', y='total_used_30d',
                color_discrete_sequence=[TEAL],
                labels={'product_name': 'Produs', 'total_used_30d': 'Cantitate'},
                text='total_used_30d',
            )
            ct_bars(fig2)
            ct(fig2, title="Top 10 produse după consum (30 zile)", height=350, legend=False, xangle=-30)
            st.plotly_chart(fig2, use_container_width=True)

        with col_c2:
            fig3 = px.bar(
                has_data.sort_values('avg_daily_7d', ascending=False).head(10),
                x='product_name', y='avg_daily_7d',
                color_discrete_sequence=[AMBER],
                labels={'product_name': 'Produs', 'avg_daily_7d': 'Unități/zi'},
                text='avg_daily_7d',
            )
            ct_bars(fig3, color=AMBER)
            fig3.update_traces(texttemplate='%{text:.1f}')
            ct(fig3, title="Consum mediu zilnic (ultimele 7 zile)", height=350, legend=False, xangle=-30)
            st.plotly_chart(fig3, use_container_width=True)

        if len(no_data) > 0:
            with st.expander(f"Produse fără consum înregistrat ({len(no_data)})"):
                st.dataframe(
                    no_data[['product_name', 'department_name', 'current_stock', 'min_stock_level']],
                    use_container_width=True, hide_index=True,
                    column_config={
                        'product_name':    st.column_config.TextColumn('Produs'),
                        'department_name': st.column_config.TextColumn('Departament'),
                        'current_stock':   st.column_config.NumberColumn('Stoc Curent'),
                        'min_stock_level': st.column_config.NumberColumn('Stoc Minim'),
                    }
                )

# ── TAB 3 — Urgente ──────────────────────────────────────────────────────────
with tab_urgente:
    st.subheader("Produse care necesită atenție imediată")

    if urgent.empty and warning.empty:
        st.success("Niciun produs nu este în pericol de epuizare în următoarele 30 de zile.")
    else:
        if not urgent.empty:
            st.error(f"**{len(urgent)} produse se epuizează în mai puțin de 7 zile:**")
            for _, row in urgent.iterrows():
                st.error(
                    f"**{row['product_name']}** — stoc: {row['current_stock']} | "
                    f"consum/zi: {row['avg_daily_7d']:.1f} | "
                    f"epuizare în ~**{row['days_until_stockout']:.0f} zile** | "
                    f"comandă recomandată: **{row['recommended_order_qty']} buc**"
                )

        if not warning.empty:
            st.warning(f"**{len(warning)} produse se epuizează în 7–30 de zile:**")
            for _, row in warning.iterrows():
                st.warning(
                    f"**{row['product_name']}** — stoc: {row['current_stock']} | "
                    f"consum/zi: {row['avg_daily_7d']:.1f} | "
                    f"epuizare în ~**{row['days_until_stockout']:.0f} zile** | "
                    f"comandă recomandată: **{row['recommended_order_qty']} buc**"
                )
