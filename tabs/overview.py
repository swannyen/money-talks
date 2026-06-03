import streamlit as st
import plotly.express as px


def render_overview(portfolio_summary):
    st.header("Overview")
    if not portfolio_summary.empty:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.dataframe(portfolio_summary, width="stretch", hide_index=True)
            total_nw = portfolio_summary["Total_Value_Base"].sum()
            st.metric("Total Net Worth", f"{total_nw:,.2f}")

        with col2:
            fig = px.pie(
                portfolio_summary,
                values="Total_Value_Base",
                names="Portfolio",
                title="Portfolio Breakdown by Value",
                hole=0.4,
            )
            st.plotly_chart(fig, width="stretch")
    else:
        st.info("No portfolio summary to display.")
