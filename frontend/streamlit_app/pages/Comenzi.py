"""
MedicSync - Comenzi Aprovizionare
Vizualizare comenzi de aprovizionare (read-only pentru manager).
"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import require_auth, get_user_role
from components.navigation import render_top_nav
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Comenzi", page_icon="🛒", layout="wide")
require_auth(allowed_roles=["inventory_manager", "manager"])
render_top_nav()

st.title("🛒 Comenzi Aprovizionare")
st.markdown("### Monitorizare comenzi de materiale sanitare")

api = st.session_state.api_client
user_role = get_user_role()

STATUS_LABELS = {
    "draft":     ("📝", "Ciornă",     "#6c757d"),
    "placed":    ("📬", "Plasată",    "#0d6efd"),
    "processed": ("⚙️",  "Procesată",  "#fd7e14"),
    "delivered": ("✅", "Livrată",    "#198754"),
    "rejected":  ("❌", "Respinsă",   "#dc3545"),
}

col_refresh, _ = st.columns([1, 5])
with col_refresh:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

st.markdown("---")

try:
    with st.spinner("Se încarcă comenzile..."):
        orders = api.get_orders()

    if not orders:
        st.info("Nu există comenzi înregistrate în sistem.")
        st.stop()

    # Summary metrics
    total = len(orders)
    delivered = len([o for o in orders if o['status'] == 'delivered'])
    pending = len([o for o in orders if o['status'] in ('draft', 'placed', 'processed')])
    rejected = len([o for o in orders if o['status'] == 'rejected'])
    total_value = sum(o.get('total_amount', 0) for o in orders)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Comenzi", total)
    c2.metric("În Așteptare", pending)
    c3.metric("Livrate", delivered)
    c4.metric("Valoare Totală", f"{total_value:,.2f} RON")

    st.markdown("---")

    # Orders table
    st.subheader(f"📋 Lista Comenzi ({total})")

    df = pd.DataFrame(orders)
    df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%d.%m.%Y %H:%M')
    df['total_amount'] = df['total_amount'].apply(lambda x: f"{x:,.2f} RON")

    def fmt_status(s):
        icon, label, _ = STATUS_LABELS.get(s, ("❓", s, "#000"))
        return f"{icon} {label}"

    df['status_fmt'] = df['status'].apply(fmt_status)

    display_df = df[['id', 'status_fmt', 'total_amount', 'created_at']]
    display_df.columns = ['ID', 'Status', 'Valoare', 'Data Creării']

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Status": st.column_config.TextColumn("Status", width="medium"),
            "Valoare": st.column_config.TextColumn("Valoare", width="medium"),
            "Data Creării": st.column_config.TextColumn("Data Creării", width="medium"),
        }
    )

    if user_role == "manager":
        st.info("ℹ️ Managerul are acces de vizualizare. Crearea și modificarea comenzilor se face de către Managerul de Inventar.")

    # Order detail expander
    st.markdown("---")
    st.subheader("🔍 Detalii Comandă")

    order_options = {f"Comanda #{o['id']} — {fmt_status(o['status'])} — {o['total_amount']:,.2f} RON": o for o in orders}
    selected_key = st.selectbox("Selectează comanda", options=list(order_options.keys()))
    selected_order = order_options[selected_key]

    icon, label, color = STATUS_LABELS.get(selected_order['status'], ("❓", selected_order['status'], "#000"))
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Status", f"{icon} {label}")
    col_b.metric("Valoare Totală", f"{selected_order['total_amount']:,.2f} RON")
    col_c.metric("Data Creării", pd.to_datetime(selected_order['created_at']).strftime('%d.%m.%Y %H:%M'))

    if selected_order.get('items'):
        st.markdown("#### Produse comandate")
        items_df = pd.DataFrame(selected_order['items'])
        items_df['subtotal'] = items_df['quantity'] * items_df['unit_price']
        items_df['subtotal'] = items_df['subtotal'].apply(lambda x: f"{x:,.2f} RON")
        items_df['unit_price'] = items_df['unit_price'].apply(lambda x: f"{x:,.2f} RON")
        display_items = items_df[['inventory_item_id', 'quantity', 'unit_price', 'subtotal']]
        display_items.columns = ['ID Produs', 'Cantitate', 'Preț/Unitate', 'Subtotal']
        st.dataframe(display_items, use_container_width=True, hide_index=True)
    else:
        st.info("Comanda nu are produse detaliate disponibile.")

except Exception as e:
    st.error(f"❌ Eroare la încărcarea comenzilor: {str(e)}")
    st.exception(e)
