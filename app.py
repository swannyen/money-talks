import streamlit as st
import pandas as pd
from src.db import PostgresDB
from src.helper import (
    generate_holdings,
    generate_dividends,
    generate_portfolio_summary,
    generate_realised_pl_sheet,
    generate_total_return_sheet,
    generate_dividend_recovery_sheet
)

from tabs.overview import render_overview
from tabs.holdings import render_holdings
from tabs.dividends import render_dividends
from tabs.returns import render_returns
from tabs.transactions import render_transactions
from src.auth import require_login, render_logout_button

st.set_page_config(page_title="Money Talks Dashboard", layout="wide")

if not require_login():
    st.stop()

render_logout_button()
st.title("Money Talks Dashboard")

@st.cache_data
def load_data():
    db = PostgresDB()
    df = db.get_transactions()
    db.close()
    return df

@st.cache_data
def get_holdings(transactions):
    return generate_holdings(transactions)

@st.cache_data
def get_dividends(transactions):
    return generate_dividends(transactions)

@st.cache_data
def get_portfolio_summary(holdings_df):
    return generate_portfolio_summary(holdings_df)

@st.cache_data
def get_realised_pl(transactions):
    return generate_realised_pl_sheet(transactions)

@st.cache_data
def get_total_returns(holdings_df, realised_pl_df, dividends_df):
    return generate_total_return_sheet(holdings_df, realised_pl_df, dividends_df)

@st.cache_data
def get_dividend_recovery(holdings_df, dividends_df):
    return generate_dividend_recovery_sheet(holdings_df, dividends_df)


# Main Application
transactions = load_data()

if transactions.empty:
    st.warning("No transactions found in the database. Please ingest some transactions.")
    st.stop()

# Generate dataframes
with st.spinner("Calculating portfolio data and fetching current prices..."):
    holdings_df = get_holdings(transactions)
    dividends_df = get_dividends(transactions)
    portfolio_summary = get_portfolio_summary(holdings_df)
    try:
        realised_pl_df = get_realised_pl(transactions)
    except Exception:
        realised_pl_df = pd.DataFrame()
    try:
        total_return_df = get_total_returns(holdings_df, realised_pl_df, dividends_df)
    except Exception:
        total_return_df = pd.DataFrame()
    try:
        dividend_recovery_df = get_dividend_recovery(holdings_df, dividends_df)
    except Exception:
        dividend_recovery_df = pd.DataFrame()

# TABS
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview", 
    "Holdings", 
    "Dividends", 
    "Realised P/L & Returns", 
    "Raw Transactions"
])

with tab1:
    render_overview(portfolio_summary)

with tab2:
    render_holdings(holdings_df)

with tab3:
    render_dividends(dividends_df, dividend_recovery_df)

with tab4:
    render_returns(total_return_df, realised_pl_df)

with tab5:
    render_transactions(transactions, holdings_df)
