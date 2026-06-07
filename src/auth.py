import secrets

import streamlit as st

from src.config import get_app_password


def require_login() -> bool:
    """Show a login form until the user enters the correct password."""
    if st.session_state.get("authenticated"):
        return True

    expected = get_app_password()
    if not expected:
        st.error(
            "This app is locked but no password is configured. "
            "Set `APP_PASSWORD` in Streamlit Cloud secrets or in "
            "`.streamlit/secrets.toml` for local runs."
        )
        st.stop()

    st.title("Money Talks")
    st.caption("Enter the password to view your portfolio data.")

    with st.form("login_form", clear_on_submit=False):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", type="primary", width="stretch")

    if submitted:
        if secrets.compare_digest(password, expected):
            st.session_state.authenticated = True
            st.rerun()
        st.error("Incorrect password.")

    return False


def render_logout_button() -> None:
    with st.sidebar:
        if st.button("Log out", width="stretch"):
            st.session_state.authenticated = False
            st.cache_data.clear()
            st.rerun()
