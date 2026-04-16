"""
MedicSync - Comenzi Aprovizionare
Flux complet: inventory_manager creează/plasează/livrează, manager aprobă/respinge.
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import require_auth, get_user_role, handle_api_exception
from components.navigation import render_top_nav
import cache
import pandas as pd

st.set_page_config(page_title="Comenzi", page_icon="🛒", layout="wide", initial_sidebar_state="collapsed")
require_auth(allowed_roles=["inventory_manager", "manager"])
render_top_nav()

st.title("🛒 Comenzi Aprovizionare")

api       = st.session_state.api_client
user_role = get_user_role()

STATUS_LABELS = {
    "draft":     ("📝", "Ciornă",    "#6c757d"),
    "placed":    ("📬", "Plasată",   "#0d6efd"),
    "processed": ("⚙️",  "Aprobată",  "#fd7e14"),
    "delivered": ("✅", "Livrată",   "#198754"),
    "rejected":  ("❌", "Respinsă",  "#dc3545"),
}

def fmt_status(s):
    icon, label, _ = STATUS_LABELS.get(s, ("❓", s, "#000"))
    return f"{icon} {label}"

def refresh_orders():
    cache.get_orders.clear()
    cache.get_inventory.clear()
    cache.get_fefo_alerts.clear()

# ── Tabs ─────────────────────────────────────────────────────────────────────
if user_role == "inventory_manager":
    tab_active, tab_new, tab_history = st.tabs([
        "📋 Comenzi Active", "➕ Comandă Nouă", "📜 Istoric"
    ])
else:
    tab_active, tab_history = st.tabs(["📋 Comenzi Active", "📜 Istoric"])
    tab_new = None

# ============================================================================
# TAB — Comenzi Active
# ============================================================================
with tab_active:
    col_ref, _ = st.columns([1, 5])
    with col_ref:
        if st.button("🔄 Refresh", use_container_width=True, key="refresh_active"):
            refresh_orders()
            st.rerun()

    try:
        orders = cache.get_orders(api.token)
        active = [o for o in orders if o["status"] not in ("delivered", "rejected")]

        # Alerte pentru manager — comenzi în așteptare
        if user_role == "manager":
            pending = [o for o in active if o["status"] == "placed"]
            if pending:
                st.error(f"🔔 **{len(pending)} {'comandă necesită' if len(pending)==1 else 'comenzi necesită'} aprobare!**")
            else:
                st.success("✅ Nu există comenzi în așteptarea aprobării.")

        if not active:
            st.info("Nu există comenzi active în sistem.")
        else:
            for order in active:
                icon, label, color = STATUS_LABELS.get(order["status"], ("❓", order["status"], "#000"))
                created = pd.to_datetime(order["created_at"]).strftime("%d.%m.%Y %H:%M")

                with st.container():
                    # Header comandă
                    col_info, col_actions = st.columns([3, 2])

                    with col_info:
                        st.markdown(f"""
                        <div style="
                            border-left: 4px solid {color};
                            padding: 0.6rem 1rem;
                            background: #f8f9fa;
                            border-radius: 0 8px 8px 0;
                            margin-bottom: 0.3rem;
                        ">
                            <b>Comanda #{order['id']}</b> &nbsp;·&nbsp;
                            {icon} <b>{label}</b> &nbsp;·&nbsp;
                            💰 {order['total_amount']:,.2f} RON &nbsp;·&nbsp;
                            📅 {created}
                        </div>
                        """, unsafe_allow_html=True)

                    with col_actions:
                        s = order["status"]

                        # inventory_manager: plasează draft-ul
                        if user_role == "inventory_manager" and s == "draft":
                            if st.button("📬 Plasează Comanda", key=f"place_{order['id']}",
                                         use_container_width=True, type="primary"):
                                try:
                                    api.update_order_status(order["id"], "placed")
                                    st.success("✅ Comanda a fost plasată și trimisă spre aprobare!")
                                    refresh_orders()
                                    st.rerun()
                                except Exception as e:
                                    if not handle_api_exception(e):
                                        st.error(f"❌ {str(e)}")

                        # inventory_manager: confirmă livrarea
                        elif user_role == "inventory_manager" and s == "processed":
                            if st.button("✅ Confirmă Livrarea", key=f"deliver_{order['id']}",
                                         use_container_width=True, type="primary"):
                                try:
                                    api.update_order_status(order["id"], "delivered")
                                    st.success("✅ Livrare confirmată!")
                                    refresh_orders()
                                    st.rerun()
                                except Exception as e:
                                    if not handle_api_exception(e):
                                        st.error(f"❌ {str(e)}")

                        # manager: aprobă sau respinge
                        elif user_role == "manager" and s == "placed":
                            c1, c2 = st.columns(2)
                            with c1:
                                if st.button("✅ Aprobă", key=f"approve_{order['id']}",
                                             use_container_width=True, type="primary"):
                                    try:
                                        api.update_order_status(order["id"], "processed")
                                        st.success("✅ Comandă aprobată!")
                                        refresh_orders()
                                        st.rerun()
                                    except Exception as e:
                                        if not handle_api_exception(e):
                                            st.error(f"❌ {str(e)}")
                            with c2:
                                if st.button("❌ Respinge", key=f"reject_{order['id']}",
                                             use_container_width=True):
                                    try:
                                        api.update_order_status(order["id"], "rejected")
                                        st.warning("Comanda a fost respinsă.")
                                        refresh_orders()
                                        st.rerun()
                                    except Exception as e:
                                        if not handle_api_exception(e):
                                            st.error(f"❌ {str(e)}")
                        else:
                            st.caption(f"Status: {icon} {label}")

                    # Detalii produse
                    if order.get("items"):
                        with st.expander(f"📦 Produse comandate ({len(order['items'])} articole)"):
                            items_df = pd.DataFrame(order["items"])
                            items_df["subtotal"]   = items_df["quantity"] * items_df["unit_price"]
                            items_df["unit_price"] = items_df["unit_price"].apply(lambda x: f"{x:,.2f} RON")
                            items_df["subtotal"]   = items_df["subtotal"].apply(lambda x: f"{x:,.2f} RON")
                            disp = items_df[["inventory_item_id", "quantity", "unit_price", "subtotal"]]
                            disp.columns = ["ID Produs", "Cantitate", "Preț/Unitate", "Subtotal"]
                            st.dataframe(disp, use_container_width=True, hide_index=True)

                    st.markdown("<hr style='margin:6px 0;border-color:#e9ecef'>", unsafe_allow_html=True)

    except Exception as e:
        if not handle_api_exception(e):
            st.error(f"❌ Eroare: {str(e)}")

# ============================================================================
# TAB — Comandă Nouă (inventory_manager only)
# ============================================================================
if tab_new is not None:
    with tab_new:
        st.subheader("➕ Creează Comandă Nouă")
        st.info("ℹ️ Adaugă produsele dorite, apoi plasează comanda spre aprobare.")

        # Inițializare sesiune pentru rânduri de produse
        if "order_rows" not in st.session_state:
            st.session_state.order_rows = [{"inv_id": None, "qty": 1, "price": 0.0}]

        try:
            inventory = cache.get_inventory(api.token)
            prod_options = {
                f"{i['product_name']} (ID:{i['id']}, Stoc:{i['current_stock']})": i
                for i in inventory
            }
            inv_price_map = {i["id"]: i.get("unit_price", 0.0) for i in inventory}

            if not inventory:
                st.warning("⚠️ Nu există produse în inventar.")
            else:
                # ── Generare automată comenzi sub stoc minim ─────────────────
                sub_stoc = [i for i in inventory if i['current_stock'] < i['min_stock_level']]

                if sub_stoc:
                    col_auto, col_info = st.columns([1, 3])
                    with col_auto:
                        if st.button("🤖 Generează Automat", use_container_width=True, type="secondary",
                                     help="Pre-completează comanda cu toate produsele sub stocul minim"):
                            new_rows = [
                                {
                                    "inv_id": item["id"],
                                    "qty":    max(1, item["min_stock_level"] - item["current_stock"]),
                                    "price":  item.get("unit_price", 0.0),
                                }
                                for item in sub_stoc
                            ]
                            st.session_state.order_rows = new_rows
                            # Clear cached widget states so selectboxes use new defaults
                            for i in range(max(len(new_rows), 20)):
                                for pfx in ["prod_", "qty_", "price_", "del_"]:
                                    st.session_state.pop(f"{pfx}{i}", None)
                            st.rerun()
                    with col_info:
                        st.info(f"⚠️ **{len(sub_stoc)} produse** sunt sub stocul minim și pot fi comandate automat.")
                else:
                    st.success("✅ Toate produsele au stoc suficient.")

                st.markdown("#### 📦 Produse")

                rows_to_delete = []
                total_val = 0.0

                prod_keys     = list(prod_options.keys())
                inv_id_to_key = {v["id"]: k for k, v in prod_options.items()}

                for idx, row in enumerate(st.session_state.order_rows):
                    c1, c2, c3, c4 = st.columns([3, 1, 1.2, 0.4])

                    with c1:
                        default_key = inv_id_to_key.get(row.get("inv_id"))
                        default_idx = prod_keys.index(default_key) if default_key in prod_keys else 0

                        prod_key = st.selectbox(
                            "Produs",
                            options=prod_keys,
                            index=default_idx,
                            key=f"prod_{idx}",
                            label_visibility="collapsed"
                        )
                        selected_item = prod_options[prod_key]
                        st.session_state.order_rows[idx]["inv_id"] = selected_item["id"]
                        # Prețul vine din inventar — sursa de adevăr
                        st.session_state.order_rows[idx]["price"] = selected_item.get("unit_price", 0.0)

                    with c2:
                        qty = st.number_input(
                            "Cant.", min_value=1, value=max(1, row["qty"]),
                            key=f"qty_{idx}", label_visibility="collapsed"
                        )
                        st.session_state.order_rows[idx]["qty"] = qty

                    with c3:
                        current_inv_id = st.session_state.order_rows[idx]["inv_id"]
                        item_price = inv_price_map.get(current_inv_id, st.session_state.order_rows[idx]["price"])
                        st.session_state.order_rows[idx]["price"] = item_price
                        st.number_input(
                            "Preț/buc (RON)",
                            value=item_price,
                            key=f"price_{idx}",
                            label_visibility="collapsed",
                            format="%.2f",
                            disabled=True,
                        )
                        total_val += qty * item_price

                    with c4:
                        if len(st.session_state.order_rows) > 1:
                            if st.button("🗑️", key=f"del_{idx}", help="Șterge rând"):
                                rows_to_delete.append(idx)

                for idx in reversed(rows_to_delete):
                    st.session_state.order_rows.pop(idx)
                    st.rerun()

                # Legendă coloane
                lc1, lc2, lc3, _ = st.columns([3, 1, 1.2, 0.4])
                lc1.caption("Produs")
                lc2.caption("Cantitate")
                lc3.caption("Preț/buc (RON)")

                st.markdown("")
                ba, bb, _, bc = st.columns([1, 1, 2, 1.5])

                with ba:
                    if st.button("➕ Adaugă produs", use_container_width=True):
                        st.session_state.order_rows.append({"inv_id": None, "qty": 1, "price": 0.0})
                        st.rerun()

                with bb:
                    st.markdown(f"**Total: {total_val:,.2f} RON**")

                with bc:
                    if st.button("🚀 Creează & Plasează", use_container_width=True,
                                 type="primary", key="create_order"):
                        rows = st.session_state.order_rows
                        if not rows or any(r["inv_id"] is None for r in rows):
                            st.error("⚠️ Completează toate produsele!")
                        elif any(inv_price_map.get(r["inv_id"], r["price"]) <= 0 for r in rows):
                            st.error("⚠️ Prețul trebuie să fie mai mare ca 0!")
                        else:
                            try:
                                items = [
                                    {"inventory_item_id": r["inv_id"],
                                     "quantity": r["qty"],
                                     "unit_price": inv_price_map.get(r["inv_id"], r["price"])}
                                    for r in rows
                                ]
                                order = api.create_order(items)
                                api.update_order_status(order["id"], "placed")
                                st.success(f"✅ Comanda #{order['id']} a fost creată și plasată spre aprobare!")
                                st.session_state.order_rows = [{"inv_id": None, "qty": 1, "price": 0.0}]
                                refresh_orders()
                                import time; time.sleep(1); st.rerun()
                            except Exception as e:
                                if not handle_api_exception(e):
                                    st.error(f"❌ Eroare: {str(e)}")

        except Exception as e:
            if not handle_api_exception(e):
                st.error(f"❌ Eroare la încărcarea inventarului: {str(e)}")

# ============================================================================
# TAB — Istoric
# ============================================================================
with tab_history:
    try:
        orders = cache.get_orders(api.token)
        history = [o for o in orders if o["status"] in ("delivered", "rejected")]

        if not history:
            st.info("Nu există comenzi finalizate.")
        else:
            total_delivered = len([o for o in history if o["status"] == "delivered"])
            total_rejected  = len([o for o in history if o["status"] == "rejected"])
            total_value     = sum(o["total_amount"] for o in history if o["status"] == "delivered")

            c1, c2, c3 = st.columns(3)
            c1.metric("✅ Livrate",    total_delivered)
            c2.metric("❌ Respinse",   total_rejected)
            c3.metric("💰 Val. Livrată", f"{total_value:,.2f} RON")

            st.markdown("---")

            df = pd.DataFrame(history)
            df["created_at"]   = pd.to_datetime(df["created_at"]).dt.strftime("%d.%m.%Y %H:%M")
            df["total_amount"] = df["total_amount"].apply(lambda x: f"{x:,.2f} RON")
            df["status_fmt"]   = df["status"].apply(fmt_status)

            disp = df[["id", "status_fmt", "total_amount", "created_at"]]
            disp.columns = ["ID", "Status", "Valoare", "Data Creării"]
            st.dataframe(disp, use_container_width=True, hide_index=True)

    except Exception as e:
        if not handle_api_exception(e):
            st.error(f"❌ Eroare: {str(e)}")
