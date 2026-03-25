"""
MedicSync - Management Inventar
Stocuri medicale per departament, alerte FEFO și adăugare produse.
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import require_auth, get_user_role
from components.navigation import render_top_nav
import pandas as pd
from datetime import date

st.set_page_config(page_title="Inventar", page_icon="📦", layout="wide")
require_auth(allowed_roles=["manager", "inventory_manager"])
render_top_nav()

st.title("📦 Management Inventar")
st.markdown("### Stocuri medicale per departament, alerte FEFO și predicții")

api = st.session_state.api_client
user_role = get_user_role()
user = st.session_state.user
user_dept_id = user.get("department_id")

try:
    departments   = api.get_departments()
    dept_map      = {d['id']: d['name'] for d in departments}
    dept_id_map   = {d['name']: d['id'] for d in departments}
except Exception:
    departments = []
    dept_map = {}
    dept_id_map = {}

tab_stoc, tab_alerte, tab_adauga = st.tabs([
    "📋 Stoc Curent",
    "⚠️ Alerte FEFO",
    "➕ Adaugă Produs",
])

# ============================================================================
# TAB 1 — Stoc Curent
# ============================================================================
with tab_stoc:
    try:
        with st.spinner("Se încarcă inventarul..."):
            inventory = api.get_inventory()

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
                # Manager poate filtra pe departament
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

            # Actualizare stoc
            st.markdown("---")
            st.markdown("##### ✏️ Actualizează Stoc")
            inventory_full = api.get_inventory()
            with st.form("update_stock"):
                prod_map = {f"{i['product_name']} — {dept_map.get(i['department_id'], '?')} (ID: {i['id']})": i
                            for i in inventory_full}
                selected = st.selectbox("Produs", options=list(prod_map.keys()))
                new_stock = st.number_input("Stoc nou", min_value=0,
                                            value=int(prod_map[selected]['current_stock']))
                if st.form_submit_button("💾 Salvează", type="primary"):
                    try:
                        api.update_inventory_stock(prod_map[selected]['id'], new_stock)
                        st.success("✅ Stoc actualizat!")
                        import time; time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"❌ Eroare: {str(e)}")

    except Exception as e:
        st.error(f"❌ Eroare: {str(e)}")

# ============================================================================
# TAB 2 — Alerte FEFO
# ============================================================================
with tab_alerte:
    try:
        with st.spinner("Se verifică datele de expirare..."):
            fefo_alerts = api.get_fefo_alerts()

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
                if alert['severity'] == 'expired':   st.error(msg)
                elif alert['severity'] == 'critical': st.warning(msg)
                else:                                 st.info(msg)

    except Exception as e:
        st.error(f"❌ Eroare: {str(e)}")

# ============================================================================
# TAB 3 — Adaugă Produs
# ============================================================================
with tab_adauga:
    st.subheader("➕ Adaugă Produs Nou în Inventar")

    with st.form("new_product", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            product_name  = st.text_input("Nume Produs *", placeholder="ex: Ser fiziologic 500ml")
            current_stock = st.number_input("Stoc Inițial *", min_value=0, value=0)
            min_stock     = st.number_input("Stoc Minim *", min_value=0, value=10,
                                             help="Alertă când stocul scade sub această valoare")

        with col2:
            exp_date = st.date_input("Dată Expirare *", value=date.today(), min_value=date.today())

            # Selectare departament
            if user_role == "manager" and departments:
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
            submit = st.form_submit_button("💾 Adaugă Produs", type="primary", use_container_width=True)

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
                        department_id=selected_dept_id
                    )
                    dept_name = dept_map.get(selected_dept_id, '')
                    st.success(f"✅ **{product_name}** adăugat în **{dept_name}**!")
                    import time; time.sleep(1); st.rerun()
                except Exception as e:
                    st.error(f"❌ Eroare: {str(e)}")
