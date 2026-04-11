import streamlit as st
import pandas as pd
import plotly.express as px
from src.db import SQLiteDB
from src.helper import (
    generate_holdings,
    generate_dividends,
    generate_portfolio_summary,
    generate_realised_pl_sheet,
    generate_total_return_sheet,
    generate_dividend_recovery_sheet
)

st.set_page_config(page_title="Money Talks Dashboard", layout="wide")
st.title("Money Talks Dashboard")

@st.cache_data
def load_data():
    db = SQLiteDB()
    df = db.get_table("transactions")
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
    st.header("Overview")
    if not portfolio_summary.empty:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.dataframe(portfolio_summary, use_container_width=True, hide_index=True)
            total_nw = portfolio_summary["Total_Value_Base"].sum()
            st.metric("Total Net Worth", f"{total_nw:,.2f}")
        
        with col2:
            fig = px.pie(
                portfolio_summary, 
                values="Total_Value_Base", 
                names="Portfolio", 
                title="Portfolio Breakdown by Value",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No portfolio summary to display.")

with tab2:
    st.header("Holdings")
    if not holdings_df.empty:
        st.dataframe(holdings_df, use_container_width=True, hide_index=True)
        col1, col2 = st.columns(2)
        with col1:
            fig2 = px.bar(
                holdings_df, 
                x="Ticker", 
                y="Unrealised P/L (base)", 
                color="Portfolio", 
                title="Unrealised P/L by Ticker",
                text_auto='.2s'
            )
            fig2.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
            st.plotly_chart(fig2, use_container_width=True)
        
        with col2:
            fig3 = px.bar(
                holdings_df, 
                x="Ticker", 
                y="Current Value (base)", 
                color="Portfolio", 
                title="Current Position Value",
                text_auto='.2s'
            )
            fig3.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No holdings to display.")

with tab3:
    st.header("Dividends")
    if not dividends_df.empty:
        st.dataframe(dividends_df, use_container_width=True, hide_index=True)
        fig4 = px.bar(
            dividends_df, 
            x="Year", 
            y="Total Dividends", 
            color="Ticker", 
            barmode="stack", 
            title="Dividends per Year",
            text_auto='.2s'
        )
        # Ensure year is displayed nicely in X-axis (not floating numbers if there's only 1 year)
        fig4.update_layout(xaxis=dict(tick0=dividends_df["Year"].min(), dtick=1))
        st.plotly_chart(fig4, use_container_width=True)
        
        st.subheader("Dividend Recovery")
        if not dividend_recovery_df.empty:
            st.dataframe(dividend_recovery_df, use_container_width=True, hide_index=True)
        else:
            st.info("No dividend recovery data available.")
    else:
        st.info("No dividends to display.")

with tab4:
    st.header("Realised P/L & Total Returns")
    st.subheader("Total Return by Ticker")
    if not total_return_df.empty:
        st.dataframe(total_return_df, use_container_width=True, hide_index=True)
        fig5 = px.bar(
            total_return_df, 
            x="Ticker", 
            y="Total Return (base)", 
            color="Portfolio", 
            title="Total Return (base) per Ticker",
            text_auto='.2s'
        )
        fig5.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("No total return data available.")
        
    st.subheader("Realised P/L (Sells)")
    if not realised_pl_df.empty:
        st.dataframe(realised_pl_df, use_container_width=True, hide_index=True)
    else:
        st.info("No realised P/L to display.")

with tab5:
    st.header("Raw Transactions")
    st.dataframe(transactions, use_container_width=True, hide_index=True)
