import pandas as pd
import plotly.express as px
import streamlit as st


def render_dividends(
    dividends_df: pd.DataFrame, dividend_recovery_df: pd.DataFrame
) -> None:
    st.header("Dividends")
    if dividends_df.empty:
        st.info("No dividends to display.")
        return

    st.dataframe(dividends_df, width="stretch", hide_index=True)
    fig = px.bar(
        dividends_df,
        x="Year",
        y="Total Dividends",
        color="Ticker",
        barmode="stack",
        title="Dividends per Year",
        text_auto=".2s",
    )
    fig.update_layout(xaxis={"tick0": dividends_df["Year"].min(), "dtick": 1})
    st.plotly_chart(fig, width="stretch")

    st.subheader("Dividend Recovery")
    if dividend_recovery_df.empty:
        st.info("No dividend recovery data available.")
        return

    st.dataframe(dividend_recovery_df, width="stretch", hide_index=True)
