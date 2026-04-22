import streamlit as st
import plotly.express as px


def render_dividends(dividends_df, dividend_recovery_df):
    st.header("Dividends")
    if not dividends_df.empty:
        st.dataframe(dividends_df, width="stretch", hide_index=True)
        fig4 = px.bar(
            dividends_df,
            x="Year",
            y="Total Dividends",
            color="Ticker",
            barmode="stack",
            title="Dividends per Year",
            text_auto=".2s",
        )
        # Ensure year is displayed nicely in X-axis (not floating numbers if there's only 1 year)
        fig4.update_layout(xaxis=dict(tick0=dividends_df["Year"].min(), dtick=1))
        st.plotly_chart(fig4, width="stretch")

        st.subheader("Dividend Recovery")
        if not dividend_recovery_df.empty:
            st.dataframe(dividend_recovery_df, width="stretch", hide_index=True)
        else:
            st.info("No dividend recovery data available.")
    else:
        st.info("No dividends to display.")
