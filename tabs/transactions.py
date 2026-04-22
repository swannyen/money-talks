import streamlit as st
from src.components.add_transaction import add_transaction_dialog


def render_transactions(transactions_df):
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.header("Raw Transactions")
    with col2:
        st.write("")  # Add some padding to align vertically
        if st.button("Add Transaction", width="stretch"):
            add_transaction_dialog()

    st.dataframe(transactions_df, width="stretch", hide_index=True)
