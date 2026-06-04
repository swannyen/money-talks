import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

DEFAULT_PORTFOLIOS = ["Tiger", "MooMoo", "Vickers"]
DEFAULT_CURRENCIES = ["SGD", "USD", "HKD", "EUR", "JPY"]
DEFAULT_BASE_CURRENCY = "SGD"


def _raw_setting(key: str) -> Any | None:
    try:
        import streamlit as st

        if key in st.secrets:
            return st.secrets[key]
    except (AttributeError, RuntimeError, ImportError):
        pass

    env_value = os.getenv(key)
    if env_value is not None:
        return env_value
    return None


def _parse_list_setting(key: str, default: list[str]) -> list[str]:
    raw = _raw_setting(key)
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
    raw = _raw_setting("BASE_CURRENCY")
    if raw is None:
        return DEFAULT_BASE_CURRENCY
    return str(raw).strip().upper()
