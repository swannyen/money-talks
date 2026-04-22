import streamlit as st
import plotly.express as px


def render_holdings(holdings_df):
    st.header("Holdings")
    if not holdings_df.empty:
        st.dataframe(holdings_df, width="stretch", hide_index=True)
        col1, col2 = st.columns(2)
        with col1:
            fig2 = px.bar(
                holdings_df,
                x="Ticker",
                y="Unrealised P/L (base)",
                color="Portfolio",
                title="Unrealised P/L by Ticker",
                text_auto=".2s",
            )
            fig2.update_traces(
                textfont_size=12, textangle=0, textposition="outside", cliponaxis=False
            )
            st.plotly_chart(fig2, width="stretch")

        with col2:
            fig3 = px.bar(
                holdings_df,
                x="Ticker",
                y="Current Value (base)",
                color="Portfolio",
                title="Current Position Value",
                text_auto=".2s",
            )
            fig3.update_traces(
                textfont_size=12, textangle=0, textposition="outside", cliponaxis=False
            )
            st.plotly_chart(fig3, width="stretch")
    else:
        st.info("No holdings to display.")
