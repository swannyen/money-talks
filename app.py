import streamlit as st
import pandas as pd
from src.db import PostgresDB
from src.helper import (
    generate_dividends,
    generate_dividend_recovery_sheet,
    generate_holdings,
    generate_portfolio_summary,
    generate_realised_pl_sheet,
    generate_total_return_sheet,
)
from src.auth import require_login, render_logout_button
from tabs.dividends import render_dividends
from tabs.holdings import render_holdings
from tabs.overview import render_overview
from tabs.returns import render_returns
from tabs.transactions import render_transactions

st.set_page_config(page_title="Money Talks Dashboard", layout="wide")

if not require_login():
    st.stop()

render_logout_button()
st.title("Money Talks Dashboard")


@st.cache_data
def load_transactions() -> pd.DataFrame:
    db = PostgresDB()
    try:
        return db.get_transactions()
    finally:
        db.close()


@st.cache_data
def build_portfolio_data(transactions: pd.DataFrame):
    holdings_df = generate_holdings(transactions)
    dividends_df = generate_dividends(transactions)
    portfolio_summary = generate_portfolio_summary(holdings_df)

    try:
        realised_pl_df = generate_realised_pl_sheet(transactions)
    except Exception:
        realised_pl_df = pd.DataFrame()

    try:
        total_return_df = generate_total_return_sheet(
            holdings_df, realised_pl_df, dividends_df
        )
    except Exception:
        total_return_df = pd.DataFrame()

    try:
        dividend_recovery_df = generate_dividend_recovery_sheet(
            holdings_df, dividends_df
        )
    except Exception:
        dividend_recovery_df = pd.DataFrame()

    return (
        holdings_df,
        dividends_df,
        portfolio_summary,
        realised_pl_df,
        total_return_df,
        dividend_recovery_df,
    )


transactions = load_transactions()

if transactions.empty:
    st.warning("No transactions found in the database. Please ingest some transactions.")
    st.stop()

with st.spinner("Calculating portfolio data and fetching current prices..."):
    (
        holdings_df,
        dividends_df,
        portfolio_summary,
        realised_pl_df,
        total_return_df,
        dividend_recovery_df,
    ) = build_portfolio_data(transactions)

tab_overview, tab_holdings, tab_dividends, tab_returns, tab_transactions = st.tabs(
    ["Overview", "Holdings", "Dividends", "Realised P/L & Returns", "Raw Transactions"]
)

with tab_overview:
    render_overview(portfolio_summary)

with tab_holdings:
    render_holdings(holdings_df)

with tab_dividends:
    render_dividends(dividends_df, dividend_recovery_df)

with tab_returns:
    render_returns(total_return_df, realised_pl_df)

with tab_transactions:
    render_transactions(transactions, holdings_df)
