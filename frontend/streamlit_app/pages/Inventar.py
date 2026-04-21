"""
MedicSync - Management Inventar
Stocuri medicale per departament, alerte FEFO și adăugare produse.
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

st.set_page_config(page_title="Inventar", page_icon="📦", layout="wide", initial_sidebar_state="collapsed")
require_auth(allowed_roles=["manager", "inventory_manager", "nurse"])
render_top_nav()

st.title("Inventar")

api = st.session_state.api_client
user_role = get_user_role()
user = st.session_state.user
user_dept_id = user.get("department_id")

try:
    data = cache.fetch_parallel(
        departments  = (cache.get_departments, api.token),
        inventory    = (cache.get_inventory,   api.token),
        fefo_alerts  = (cache.get_fefo_alerts, api.token),
    )
    departments  = data["departments"]
    dept_map     = {d['id']: d['name'] for d in departments}
    dept_id_map  = {d['name']: d['id'] for d in departments}
    _inv_prefetch  = data["inventory"]    # deja în cache, tab-urile îl citesc instant
    _fefo_prefetch = data["fefo_alerts"]  # idem
except Exception:
    departments  = []
    dept_map     = {}
    dept_id_map  = {}

if user_role == "nurse":
    tab_stoc = None
    tab_alerte = None
    tab_adauga = None
    tab_foloseste = True
else:
    tab_stoc, tab_alerte, tab_adauga = st.tabs([
        "Stoc curent",
        "Alerte FEFO",
        "Adaugă produs",
    ])
    tab_foloseste = None

# ============================================================================
# TAB 1 — Stoc Curent
# ============================================================================
if tab_stoc is not None:
    with tab_stoc:
        try:
            inventory = cache.get_inventory(api.token)

            if not inventory:
                st.info("Nu există produse în inventar pentru secția ta.")
            else:
                sub_stoc = [i for i in inventory if i['current_stock'] < i['min_stock_level']]
                ok_stoc  = [i for i in inventory if i['current_stock'] >= i['min_stock_level']]

                c1, c2, c3 = st.columns(3)
                c1.metric("📦 Total Produse",  len(inventory))
                c2.metric("✅ Stoc OK",        len(ok_stoc))
                c3.metric("🔴 Sub Stoc Minim", len(sub_stoc))

                st.markdown("---")

                col_filter, col_dept, _ = st.columns([1, 1, 2])
                with col_filter:
                    filtru = st.selectbox("Filtrează stoc", ["Toate", "Sub stoc minim", "Stoc OK"],
                                          label_visibility="collapsed")
                with col_dept:
                    if user_role == "manager" and departments:
                        dept_filter_opts = {"Toate departamentele": None}
                        dept_filter_opts.update({d['name']: d['id'] for d in departments})
                        dept_filtru = st.selectbox("Departament", list(dept_filter_opts.keys()),
                                                   label_visibility="collapsed")
                    else:
                        dept_filtru = None
                        dept_filter_opts = {}

                df = pd.DataFrame(inventory)
                df['Departament'] = df['department_id'].map(dept_map).fillna('—')
                df['Status'] = df.apply(
                    lambda r: "🔴 Sub stoc minim" if r['current_stock'] < r['min_stock_level'] else "✅ Stoc OK",
                    axis=1
                )
                df['expiration_date'] = pd.to_datetime(df['expiration_date']).dt.strftime('%d.%m.%Y')

                if filtru == "Sub stoc minim":
                    df = df[df['current_stock'] < df['min_stock_level']]
                elif filtru == "Stoc OK":
                    df = df[df['current_stock'] >= df['min_stock_level']]

                if user_role == "manager" and dept_filtru and dept_filtru != "Toate departamentele":
                    df = df[df['department_id'] == dept_filter_opts[dept_filtru]]

                display = df[['product_name', 'Departament', 'current_stock', 'min_stock_level', 'expiration_date', 'Status']]
                display.columns = ['Produs', 'Departament', 'Stoc Curent', 'Stoc Minim', 'Dată Expirare', 'Status']
                st.dataframe(display, use_container_width=True, hide_index=True)

                st.markdown("---")
                st.markdown("##### Actualizează stoc")
                prod_map = {
                    f"{i['product_name']} — {dept_map.get(i['department_id'], '?')} (ID: {i['id']})": i
                    for i in inventory
                }
                with st.form("update_stock"):
                    selected = st.selectbox("Produs", options=list(prod_map.keys()))
                    new_stock = st.number_input("Stoc nou", min_value=0,
                                                value=int(prod_map[selected]['current_stock']))
                    if st.form_submit_button("Salvează", type="primary"):
                        try:
                            api.update_inventory_stock(prod_map[selected]['id'], new_stock)
                            st.success("✅ Stoc actualizat!")
                            cache.get_inventory.clear()
                            cache.get_fefo_alerts.clear()
                            import time; time.sleep(1); st.rerun()
                        except Exception as e:
                            if not handle_api_exception(e):
                                st.error(f"❌ Eroare: {str(e)}")

        except Exception as e:
            if not handle_api_exception(e):
                st.error(f"❌ Eroare: {str(e)}")

# ============================================================================
# TAB — Folosește produs (nurse only)
# ============================================================================
if tab_foloseste is not None:
    try:
        inventory = cache.get_inventory(api.token)
        if not inventory:
            st.info("Nu există produse în inventarul secției tale.")
        else:
            prod_map = {
                f"{i['product_name']} (stoc: {i['current_stock']})": i
                for i in inventory
            }
            selected = st.selectbox("Produs", options=list(prod_map.keys()), key="use_prod_sel")
            item = prod_map[selected]
            st.caption(f"Stoc disponibil: **{item['current_stock']}**")

            qty = st.number_input("Cantitate folosită", min_value=1, step=1, key="use_qty")
            col_btn, _ = st.columns([1, 3])
            with col_btn:
                if st.button("Confirmă utilizarea", type="primary", use_container_width=True):
                    try:
                        api.use_inventory_item(item['id'], int(st.session_state["use_qty"]))
                        st.success(f"✅ {int(st.session_state['use_qty'])} × **{item['product_name']}** scăzut din stoc.")
                        cache.get_inventory.clear()
                        cache.get_fefo_alerts.clear()
                        import time; time.sleep(1); st.rerun()
                    except Exception as e:
                        if not handle_api_exception(e):
                            st.error(f"❌ {str(e)}")
    except Exception as e:
        if not handle_api_exception(e):
            st.error(f"❌ {str(e)}")

# ============================================================================
# TAB 2 — Alerte FEFO
# ============================================================================
if tab_alerte is not None:
    with tab_alerte:
        try:
            fefo_alerts = cache.get_fefo_alerts(api.token)

            if not fefo_alerts:
                st.success("✅ Nu există produse expirate sau aproape de expirare!")
            else:
                sev_color = {"expired": "🔴", "critical": "🟠", "warning": "🟡"}
                sev_label = {"expired": "Expirat", "critical": "Critic (≤7 zile)", "warning": "Avertisment (≤30 zile)"}

                c1, c2, c3 = st.columns(3)
                c1.metric("🔴 Expirate",          len([a for a in fefo_alerts if a['severity'] == 'expired']))
                c2.metric("🟠 Critice (≤7 zile)",  len([a for a in fefo_alerts if a['severity'] == 'critical']))
                c3.metric("🟡 Avertisment",        len([a for a in fefo_alerts if a['severity'] == 'warning']))

                st.markdown("---")
                for alert in fefo_alerts:
                    icon  = sev_color.get(alert['severity'], '⚪')
                    days  = alert['days_until_expiry']
                    exp_d = pd.to_datetime(alert['expiration_date']).strftime('%d.%m.%Y')
                    days_text = f"Expirat de **{abs(days)} zile**" if days < 0 else f"Expiră în **{days} zile**"

                    msg = f"{icon} **{alert['product_name']}** — {days_text} | Expirare: {exp_d} | Stoc: {alert['current_stock']}"
                    if alert['severity'] == 'expired':    st.error(msg)
                    elif alert['severity'] == 'critical': st.warning(msg)
                    else:                                 st.info(msg)

        except Exception as e:
            if not handle_api_exception(e):
                st.error(f"❌ Eroare: {str(e)}")

# ============================================================================
# TAB 3 — Adaugă Produs
# ============================================================================
if tab_adauga is not None:
    with tab_adauga:
        st.subheader("Adaugă produs nou")

        with st.form("new_product", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                product_name  = st.text_input("Nume Produs *", placeholder="ex: Ser fiziologic 500ml")
                current_stock = st.number_input("Stoc Inițial *", min_value=0, value=0)
                min_stock     = st.number_input("Stoc Minim *", min_value=0, value=10,
                                                 help="Alertă când stocul scade sub această valoare")
                unit_price    = st.number_input("Preț Unitar (RON) *", min_value=0.01, value=1.0,
                                                 step=0.5, format="%.2f",
                                                 help="Prețul per unitate folosit la comenzi")

            with col2:
                exp_date = st.date_input("Dată Expirare *", value=date.today(), min_value=date.today())

                if user_role in ("manager", "inventory_manager") and departments:
                    dept_select = st.selectbox("Departament *", options=list(dept_id_map.keys()))
                    selected_dept_id = dept_id_map[dept_select]
                elif user_dept_id:
                    dept_name = dept_map.get(user_dept_id, f"Secția {user_dept_id}")
                    st.info(f"Departament: **{dept_name}**")
                    selected_dept_id = user_dept_id
                else:
                    st.warning("⚠️ Nu ai o secție asociată contului tău.")
                    selected_dept_id = None

            st.markdown("")
            col_btn, _ = st.columns([1, 3])
            with col_btn:
                submit = st.form_submit_button("Adaugă produs", type="primary", use_container_width=True)

            if submit:
                if not product_name.strip():
                    st.error("⚠️ Numele produsului este obligatoriu!")
                elif not selected_dept_id:
                    st.error("⚠️ Selectează un departament!")
                else:
                    try:
                        api.create_inventory_item(
                            product_name=product_name.strip(),
                            current_stock=current_stock,
                            min_stock_level=min_stock,
                            expiration_date=str(exp_date),
                            unit_price=unit_price,
                            department_id=selected_dept_id
                        )
                        dept_name = dept_map.get(selected_dept_id, '')
                        st.success(f"✅ **{product_name}** adăugat în **{dept_name}**!")
                        cache.get_inventory.clear()
                        cache.get_fefo_alerts.clear()
                        import time; time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"❌ Eroare: {str(e)}")
