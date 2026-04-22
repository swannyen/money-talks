import streamlit as st
import plotly.express as px


def render_returns(total_return_df, realised_pl_df):
    st.header("Realised P/L & Total Returns")
    st.subheader("Total Return by Ticker")
    if not total_return_df.empty:
        st.dataframe(total_return_df, width="stretch", hide_index=True)
        fig5 = px.bar(
            total_return_df,
            x="Ticker",
            y="Total Return (base)",
            color="Portfolio",
            title="Total Return (base) per Ticker",
            text_auto=".2s",
        )
        fig5.update_traces(
            textfont_size=12, textangle=0, textposition="outside", cliponaxis=False
        )
        st.plotly_chart(fig5, width="stretch")
    else:
        st.info("No total return data available.")

    st.subheader("Realised P/L (Sells)")
    if not realised_pl_df.empty:
        st.dataframe(realised_pl_df, width="stretch", hide_index=True)
    else:
        st.info("No realised P/L to display.")
