from typing import List, Dict
import requests


def get_fx_rates(base_currency: str, currencies: List[str]) -> Dict[str, float]:
    """
    Get FX rates for a list of currencies relative to a base currency.

    Returns a dict where:
        rates[target] = how many units of target per 1 unit of base.

    Example:
        base_currency = "HKD"
        currencies = ["SGD", "USD"]
        -> { "SGD": 0.17..., "USD": 0.12... }
    """
    base_currency = base_currency.upper()
    symbols = ",".join([c.upper() for c in currencies])

    # Frankfurter API (no API key needed)
    url = "https://api.frankfurter.app/latest"
    params = {"from": base_currency, "to": symbols}

    response = requests.get(url, params=params, timeout=100)
    response.raise_for_status()

    data = response.json()

    # Frankfurter returns a dict like:
    # {"amount":1.0,"base":"HKD","date":"2025-11-20","rates":{"SGD":0.17,...}}
    if "rates" not in data:
        raise RuntimeError(f"Unexpected FX API response: {data}")

    return data["rates"]


def convert_amount_from_base(amount_base, rate) -> float:
    """
    Convert an amount using a given FX rate.

    amount_in_base * rate = amount_in_target
    """
    return amount_base * rate


def convert_amount_to_base(amount, rate) -> float:
    """
    Convert an amount using a given FX rate.

    amount_in_base * rate = amount_in_target
    """
    return amount / rate
