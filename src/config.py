import os
from typing import Any
from urllib.parse import urlparse

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DEFAULT_PORTFOLIOS = ["Tiger", "MooMoo", "Vickers"]
DEFAULT_CURRENCIES = ["SGD", "USD", "HKD", "EUR", "JPY"]
DEFAULT_BASE_CURRENCY = "SGD"


def get_setting(key: str) -> Any | None:
    """Read a setting from Streamlit secrets, then environment variables."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except (AttributeError, RuntimeError):
        pass
    return os.getenv(key)


def _parse_list_setting(key: str, default: list[str]) -> list[str]:
    raw = get_setting(key)
    if raw is None:
        return default.copy()

    if isinstance(raw, (list, tuple)):
        return [str(item).strip() for item in raw if str(item).strip()]

    if isinstance(raw, str):
        return [item.strip() for item in raw.split(",") if item.strip()]

    return default.copy()


def get_portfolios() -> list[str]:
    return _parse_list_setting("PORTFOLIOS", DEFAULT_PORTFOLIOS)


def get_currencies() -> list[str]:
    return _parse_list_setting("CURRENCIES", DEFAULT_CURRENCIES)


def get_base_currency() -> str:
    raw = get_setting("BASE_CURRENCY")
    if raw is None:
        return DEFAULT_BASE_CURRENCY
    return str(raw).strip().upper()


def get_app_password() -> str | None:
    raw = get_setting("APP_PASSWORD")
    return str(raw) if raw is not None else None


def get_database_url() -> str:
    raw = get_setting("DATABASE_URL")
    if not raw:
        raise RuntimeError(
            "DATABASE_URL is not set. Add it to .streamlit/secrets.toml locally "
            "or Streamlit Cloud secrets."
        )

    url = str(raw)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and "+psycopg2" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

    if "sslmode=" not in url:
        url += "&sslmode=require" if "?" in url else "?sslmode=require"

    return url


def is_supabase_direct_host(database_url: str) -> bool:
    host = urlparse(database_url).hostname or ""
    return host.startswith("db.") and host.endswith(".supabase.co")
