import streamlit as st
from typing import get_args
from datetime import date
from src.db import db
from src.models.transaction import Transaction, Currency, Portfolio
from src.models.actions import AcceptedActions
from src.helper import create_new_transaction

@st.dialog("Add Transaction")
def add_transaction_dialog():
    with st.form("add_transaction_form"):
        c1, c2 = st.columns(2)

        with c1:
            tx_date = st.date_input("Date", value=date.today())
            portfolio = st.selectbox("Portfolio", get_args(Portfolio))
            action = st.selectbox("Action", get_args(AcceptedActions))
            ticker = st.text_input("Ticker")
            st.caption("Enter 'NA' for Ticker if depositing/withdrawing cash.")

        with c2:
            currency = st.selectbox("Currency", get_args(Currency), index=0)
            quantity = st.number_input("Quantity", value=0, step=1)
            value = st.number_input("Value", value=0.0, step=1.0)
            submitted = st.form_submit_button("Save Transaction")

    if submitted:
        # INSERT INTO DB
        transaction = Transaction(
            date=str(tx_date),
            portfolio=portfolio,
            ticker=ticker,
            quantity=int(quantity) if quantity > 0 else None,
            currency=currency,
            action=action,
            value=float(value)
        )
        new_transaction_df = create_new_transaction(transaction)
        db.insert_transactions_from_df(new_transaction_df)
        st.success("Transaction saved successfully into portfolio.db!")

        # CLEAR CACHE (IMPORTANT)
        # Clear all cached data across the app to force recalculation 
        # of holdings, dividends, portfolios etc.
        st.cache_data.clear()

        # FORCE UI REFRESH
        st.rerun()
