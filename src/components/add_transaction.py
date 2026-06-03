import streamlit as st
import pandas as pd
from typing import get_args
from datetime import date
from src.db import db
from src.models.transaction import Transaction, Currency, Portfolio
from src.models.actions import AcceptedActions
from src.helper import create_new_transaction


@st.dialog("Add Transaction", width="large")
def add_transaction_dialog(holdings_df: pd.DataFrame):
    date_col, portfolio_col, action_col = st.columns(3)

    with date_col:
        tx_date = st.date_input("Date", value=date.today())
    with portfolio_col:
        portfolio = st.selectbox("Portfolio", get_args(Portfolio))
    with action_col:
        action = st.selectbox("Action", get_args(AcceptedActions))

    open_positions = pd.DataFrame()
    if not holdings_df.empty:
        open_positions = holdings_df[
            (holdings_df["Portfolio"] == portfolio)
            & (holdings_df["Net Quantity"] > 0)
        ]

    default_quantity = 0.0
    ticker_col, currency_col, quantity_col = st.columns(3)

    ticker = ""
    with ticker_col:
        if action == "DIVIDEND":
            tickers = sorted(
                open_positions["Ticker"].dropna().astype(str).str.strip().unique().tolist()
            )
            if tickers:
                ticker = st.selectbox("Ticker", tickers)
                ticker_rows = open_positions[
                    open_positions["Ticker"].astype(str).str.strip() == ticker.strip()
                ]
                default_quantity = float(ticker_rows["Net Quantity"].sum())
            else:
                st.selectbox("Ticker", ["No open positions"], disabled=True)
        else:
            ticker = st.text_input("Ticker", placeholder="NA for cash")

    with currency_col:
        currency = st.selectbox("Currency", get_args(Currency), index=0)
    with quantity_col:
        quantity = st.number_input("Quantity", value=default_quantity, step=1.0)

    value_col, save_col, _ = st.columns(3)
    with value_col:
        value = st.number_input("Value", value=0.0, step=1.0)
    with save_col:
        st.write("")
        submitted = st.button("Save Transaction", type="primary", width="stretch")

    if submitted:
        if action == "DIVIDEND" and not ticker:
            st.error("Choose a ticker from your holdings, or pick another action.")
            return

        transaction = Transaction(
            date=str(tx_date),
            portfolio=portfolio,
            ticker=ticker,
            quantity=int(quantity) if quantity > 0 else None,
            currency=currency,
            action=action,
            value=float(value),
        )
        db.insert_transactions_from_df(create_new_transaction(transaction))
        st.success("Transaction saved successfully!")
        st.cache_data.clear()
        st.rerun()
