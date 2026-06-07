import pandas as pd
import plotly.express as px
import streamlit as st

_BAR_TRACE_KWARGS = {
    "textfont_size": 12,
    "textangle": 0,
    "textposition": "outside",
    "cliponaxis": False,
}


def render_holdings(holdings_df: pd.DataFrame) -> None:
    st.header("Holdings")
    if holdings_df.empty:
        st.info("No holdings to display.")
        return

    st.dataframe(holdings_df, width="stretch", hide_index=True)
    col1, col2 = st.columns(2)

    with col1:
        fig_pl = px.bar(
            holdings_df,
            x="Ticker",
            y="Unrealised P/L (base)",
            color="Portfolio",
            title="Unrealised P/L by Ticker",
            text_auto=".2s",
        )
        fig_pl.update_traces(**_BAR_TRACE_KWARGS)
        st.plotly_chart(fig_pl, width="stretch")

    with col2:
        fig_value = px.bar(
            holdings_df,
            x="Ticker",
            y="Current Value (base)",
            color="Portfolio",
            title="Current Position Value",
            text_auto=".2s",
        )
        fig_value.update_traces(**_BAR_TRACE_KWARGS)
        st.plotly_chart(fig_value, width="stretch")
