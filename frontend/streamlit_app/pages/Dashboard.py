"""
MedicSync - Dashboard personalizat per rol
- nurse / doctor    → secția proprie: pacienți activi, alerte
- manager          → overview spital complet
- inventory_manager → stocuri, FEFO, comenzi
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

st.set_page_config(page_title="Dashboard", page_icon="🏥", layout="wide",
                   initial_sidebar_state="collapsed")
require_auth()
render_top_nav()

ROLE_LABELS = {
    "nurse":             "Asistent Medical",
    "doctor":            "Doctor",
    "manager":           "Manager",
    "inventory_manager": "Manager Inventar",
}
STATUS_RO = {"admitted": "Internat", "critical": "Critic", "discharged": "Externat"}
STATUS_COLOR = {"Internat": "#2ca02c", "Critic": "#d62728", "Externat": "#6b7280"}

api       = st.session_state.api_client
user_role = get_user_role()
user      = st.session_state.user
user_dept_id = user.get("department_id")

st.title("Dashboard")


def _banner(full_name, role_label, dept_name=None):
    extra = f" &nbsp;·&nbsp; <b>{dept_name}</b>" if dept_name else ""
    st.markdown(
        f'<div style="background:#EFF6FF;border-left:4px solid #2563EB;'
        f'border-radius:8px;padding:0.6rem 1.1rem;margin-bottom:1.2rem;font-size:0.9rem;">'
        f'Bună ziua, <b>{full_name}</b> &nbsp;·&nbsp; '
        f'<span style="color:#2563EB;font-weight:600;">{role_label}</span>{extra}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ============================================================================
# NURSE / DOCTOR — secția proprie
# ============================================================================
def _dashboard_nurse_doctor():
    try:
        data = cache.fetch_parallel(
            my_patients = (cache.get_patients,    api.token),
            departments = (cache.get_departments, api.token),
        )
        my_patients = data["my_patients"]
        dept_map    = {d["id"]: d["name"] for d in data["departments"]}
    except Exception as e:
        handle_api_exception(e)
        return

    dept_name = dept_map.get(user_dept_id, "") if user_dept_id else ""
    _banner(user.get("full_name", ""), ROLE_LABELS[user_role], dept_name)

    # Alerte critice nerezolvate (din notifications summary)
    critical_alerts = 0
    try:
        notif = api.get_notifications_summary()
        critical_alerts = notif.get("critical_alerts", 0)
    except Exception:
        pass

    admitted   = [p for p in my_patients if p["status"] == "admitted"]
    critical_p = [p for p in my_patients if p["status"] == "critical"]
    active     = admitted + critical_p

    # ── KPI-uri ──────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1: kpi_card("Pacienți activi",        str(len(active)),      f"în {dept_name}", "green")
    with c2: kpi_card("Critici",                str(len(critical_p)),  "necesită atenție", "red")
    with c3: kpi_card("Alerte clinice critice", str(critical_alerts),  "nerezolvate",
                      "red" if critical_alerts else "green")

    st.markdown("---")

    # ── Tabel pacienți activi ─────────────────────────────────────────────────
    if active:
        st.markdown("##### Pacienți activi în secție")
        df = pd.DataFrame(active)[["full_name", "status", "admission_date"]]
        df["status"] = df["status"].map(STATUS_RO)
        df["admission_date"] = pd.to_datetime(df["admission_date"]).dt.strftime("%d.%m.%Y")
        df.columns = ["Pacient", "Status", "Data Internare"]

        # Colorare status
        def _color_status(row):
            color = STATUS_COLOR.get(row["Status"], "#000")
            return [
                "", f"color:{color};font-weight:600;", ""
            ]

        st.dataframe(
            df.style.apply(_color_status, axis=1),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nu există pacienți activi în secția ta.")

    # ── Pie distribuție status secție ────────────────────────────────────────
    if my_patients:
        discharged = [p for p in my_patients if p["status"] == "discharged"]
        if len(my_patients) > 0:
            st.markdown("---")
            col_chart, col_empty = st.columns([1, 1])
            with col_chart:
                st.markdown("##### Distribuție status — secția mea")
                fig = go.Figure(go.Pie(
                    labels=["Internați", "Critici", "Externați"],
                    values=[len(admitted), len(critical_p), len(discharged)],
                    hole=0.45,
                    marker_colors=["#2ca02c", "#d62728", "#9ca3af"],
                ))
                fig.update_traces(textposition="inside", textinfo="percent+label")
                fig.update_layout(height=280, showlegend=False, margin=dict(t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# MANAGER — overview complet spital
# ============================================================================
def _dashboard_manager():
    try:
        with st.spinner("Se încarcă datele..."):
            data = cache.fetch_parallel(
                departments    = (cache.get_departments,    api.token),
                hospital_stats = (cache.get_hospital_stats, api.token),
                my_patients    = (cache.get_patients,       api.token),
                inventory      = (cache.get_inventory,      api.token),
                orders         = (cache.get_orders,         api.token),
            )
        departments    = data["departments"]
        hospital_stats = data["hospital_stats"]
        inventory      = data["inventory"]
        orders         = data["orders"]
    except Exception as e:
        handle_api_exception(e)
        return

    _banner(user.get("full_name", ""), ROLE_LABELS["manager"])

    total_admitted   = sum(s["admitted"]   for s in hospital_stats)
    total_critical   = sum(s["critical"]   for s in hospital_stats)
    total_discharged = sum(s["discharged"] for s in hospital_stats)
    total_patients   = total_admitted + total_critical + total_discharged
    low_stock        = [i for i in inventory if i["current_stock"] < i["min_stock_level"]]
    pending_orders   = [o for o in orders if o["status"] == "placed"]

    # ── KPI-uri ──────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi_card("Departamente",      str(len(departments)),     "secții active",            "blue")
    with c2: kpi_card("Pacienți internați", str(total_admitted),      f"{total_patients} total",  "green")
    with c3: kpi_card("Pacienți critici",   str(total_critical),      "necesită atenție urgentă", "red")
    with c4: kpi_card("Sub stoc minim",     str(len(low_stock)),      f"{len(inventory)} produse",
                      "orange" if low_stock else "green")
    with c5: kpi_card("Comenzi în așteptare", str(len(pending_orders)), "de aprobat",
                      "orange" if pending_orders else "green")

    st.markdown("---")

    # ── Grafice ──────────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("##### Pacienți pe departament")
        df_h = pd.DataFrame(hospital_stats)
        df_h = df_h[df_h["total"] > 0]
        if not df_h.empty:
            fig = px.bar(
                df_h, x="department_name", y="total",
                color="total", color_continuous_scale="Blues",
                labels={"total": "Pacienți", "department_name": "Departament"},
                text="total",
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(showlegend=False, height=320, xaxis_tickangle=-30,
                              coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nu există pacienți înregistrați.")

    with col_r:
        st.markdown("##### Distribuție status spital")
        if total_patients > 0:
            fig2 = go.Figure(go.Pie(
                labels=["Internați", "Critici", "Externați"],
                values=[total_admitted, total_critical, total_discharged],
                hole=0.4,
                marker_colors=["#2ca02c", "#d62728", "#7f7f7f"],
            ))
            fig2.update_traces(textposition="inside", textinfo="percent+label")
            fig2.update_layout(height=320, showlegend=True)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Nu există pacienți înregistrați.")

    # ── Tabel departamente ────────────────────────────────────────────────────
    st.markdown("##### Situație pe departamente")
    df_table = pd.DataFrame(hospital_stats)[
        ["department_name", "admitted", "critical", "discharged", "total"]
    ]
    df_table.columns = ["Departament", "Internați", "Critici", "Externați", "Total"]
    st.dataframe(df_table, use_container_width=True, hide_index=True)

    # ── Stoc sub minim ────────────────────────────────────────────────────────
    if low_stock:
        st.markdown("---")
        st.markdown("##### ⚠️ Produse sub stoc minim")
        df_stock = pd.DataFrame(low_stock)[["product_name", "current_stock", "min_stock_level"]]
        df_stock.columns = ["Produs", "Stoc curent", "Stoc minim"]
        st.dataframe(df_stock, use_container_width=True, hide_index=True)


# ============================================================================
# INVENTORY MANAGER — stocuri, FEFO, comenzi
# ============================================================================
def _dashboard_inventory():
    try:
        with st.spinner("Se încarcă datele..."):
            data = cache.fetch_parallel(
                inventory   = (cache.get_inventory,   api.token),
                fefo_alerts = (cache.get_fefo_alerts, api.token),
                orders      = (cache.get_orders,      api.token),
                departments = (cache.get_departments, api.token),
            )
        inventory   = data["inventory"]
        fefo_alerts = data["fefo_alerts"]
        orders      = data["orders"]
    except Exception as e:
        handle_api_exception(e)
        return

    _banner(user.get("full_name", ""), ROLE_LABELS["inventory_manager"])

    low_stock      = [i for i in inventory if i["current_stock"] < i["min_stock_level"]]
    pending_orders = [o for o in orders if o["status"] == "placed"]
    placed_orders  = [o for o in orders if o["status"] in ("draft", "placed")]

    # ── KPI-uri ──────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Total produse",        str(len(inventory)),       "în inventar",       "blue")
    with c2: kpi_card("Sub stoc minim",        str(len(low_stock)),       "necesită reaprovizionare",
                      "red" if low_stock else "green")
    with c3: kpi_card("Alerte FEFO",           str(len(fefo_alerts)),     "expirare apropiată",
                      "orange" if fefo_alerts else "green")
    with c4: kpi_card("Comenzi în așteptare",  str(len(pending_orders)),  "de procesat",
                      "orange" if pending_orders else "green")

    st.markdown("---")

    col_l, col_r = st.columns(2)

    # ── Produse sub stoc minim ────────────────────────────────────────────────
    with col_l:
        st.markdown("##### ⚠️ Produse sub stoc minim")
        if low_stock:
            df_low = pd.DataFrame(low_stock)[["product_name", "current_stock", "min_stock_level"]]
            df_low["deficit"] = df_low["min_stock_level"] - df_low["current_stock"]
            df_low.columns = ["Produs", "Stoc curent", "Stoc minim", "Deficit"]
            st.dataframe(df_low, use_container_width=True, hide_index=True)
        else:
            st.success("Toate produsele au stoc suficient.")

    # ── Alerte FEFO ───────────────────────────────────────────────────────────
    with col_r:
        st.markdown("##### 🗓️ Alerte expirare (FEFO)")
        if fefo_alerts:
            df_fefo = pd.DataFrame(fefo_alerts)
            cols = [c for c in ["product_name", "expiration_date", "current_stock"] if c in df_fefo.columns]
            if cols:
                df_fefo = df_fefo[cols]
                df_fefo.columns = ["Produs", "Expiră la", "Stoc"][: len(cols)]
            st.dataframe(df_fefo, use_container_width=True, hide_index=True)
        else:
            st.success("Nu există produse cu expirare apropiată.")

    # ── Grafic stoc per categorie ─────────────────────────────────────────────
    if inventory:
        st.markdown("---")
        st.markdown("##### Stoc curent vs. stoc minim — top 10 produse")
        df_inv = pd.DataFrame(inventory).sort_values("current_stock").head(10)
        fig = go.Figure()
        fig.add_bar(name="Stoc curent", x=df_inv["product_name"],
                    y=df_inv["current_stock"], marker_color="#3b82f6")
        fig.add_bar(name="Stoc minim",  x=df_inv["product_name"],
                    y=df_inv["min_stock_level"], marker_color="#ef4444", opacity=0.6)
        fig.update_layout(barmode="group", height=320, xaxis_tickangle=-30,
                          legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# Refresh + dispatch
# ============================================================================
try:
    if user_role in ("nurse", "doctor"):
        _dashboard_nurse_doctor()
    elif user_role == "manager":
        _dashboard_manager()
    elif user_role == "inventory_manager":
        _dashboard_inventory()
    else:
        st.info("Rol necunoscut.")

except Exception as e:
    if not handle_api_exception(e):
        st.error(f"❌ Eroare la încărcarea datelor: {str(e)}")

st.markdown("---")
col_r1, col_r2 = st.columns([1, 3])
with col_r1:
    if st.button("Reîmprospătare", use_container_width=True):
        cache.get_departments.clear()
        cache.get_hospital_stats.clear()
        cache.get_patients.clear()
        cache.get_inventory.clear()
        cache.get_fefo_alerts.clear()
        cache.get_orders.clear()
        st.rerun()
with col_r2:
    st.caption(f"Ultima actualizare: {datetime.now().strftime('%H:%M:%S')}")
