import pandas as pd
import streamlit as st

from src.auth import require_login, render_logout_button
from src.db import PostgresDB
from src.helper import (
    generate_dividends,
    generate_dividend_recovery_sheet,
    generate_holdings,
    generate_portfolio_summary,
    generate_realised_pl_sheet,
    generate_total_return_sheet,
)
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
def build_portfolio_data(transactions_df: pd.DataFrame):
    holdings = generate_holdings(transactions_df)
    dividends = generate_dividends(transactions_df)
    summary = generate_portfolio_summary(holdings)

    try:
        realised_pl = generate_realised_pl_sheet(transactions_df)
    except Exception:
        realised_pl = pd.DataFrame()

    try:
        total_return = generate_total_return_sheet(holdings, realised_pl, dividends)
    except Exception:
        total_return = pd.DataFrame()

    try:
        dividend_recovery = generate_dividend_recovery_sheet(holdings, dividends)
    except Exception:
        dividend_recovery = pd.DataFrame()

    return holdings, dividends, summary, realised_pl, total_return, dividend_recovery


transactions = load_transactions()

if transactions.empty:
    st.warning(
        "No transactions found in the database. Please ingest some transactions."
    )
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
