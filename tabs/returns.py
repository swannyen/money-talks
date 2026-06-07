import pandas as pd
import plotly.express as px
import streamlit as st

_BAR_TRACE_KWARGS = {
    "textfont_size": 12,
    "textangle": 0,
    "textposition": "outside",
    "cliponaxis": False,
}


def render_returns(total_return_df: pd.DataFrame, realised_pl_df: pd.DataFrame) -> None:
    st.header("Realised P/L & Total Returns")
    st.subheader("Total Return by Ticker")

    if total_return_df.empty:
        st.info("No total return data available.")
    else:
        st.dataframe(total_return_df, width="stretch", hide_index=True)
        fig = px.bar(
            total_return_df,
            x="Ticker",
            y="Total Return (base)",
            color="Portfolio",
            title="Total Return (base) per Ticker",
            text_auto=".2s",
        )
        fig.update_traces(**_BAR_TRACE_KWARGS)
        st.plotly_chart(fig, width="stretch")

    st.subheader("Realised P/L (Sells)")
    if realised_pl_df.empty:
        st.info("No realised P/L to display.")
    else:
        st.dataframe(realised_pl_df, width="stretch", hide_index=True)
