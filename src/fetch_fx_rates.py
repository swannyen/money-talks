import requests


def get_fx_rates(base_currency: str, currencies: list[str]) -> dict[str, float]:
    """
    Get FX rates for a list of currencies relative to a base currency.

    Returns a dict where rates[target] = how many units of target per 1 unit of base.
    """
    base_currency = base_currency.upper()
    symbols = ",".join(currency.upper() for currency in currencies)

    response = requests.get(
        "https://api.frankfurter.app/latest",
        params={"from": base_currency, "to": symbols},
        timeout=100,
    )
    response.raise_for_status()

    data = response.json()
    if "rates" not in data:
        raise RuntimeError(f"Unexpected FX API response: {data}")

    return data["rates"]


def convert_amount_from_base(amount_base: float, rate: float) -> float:
    """Convert an amount from base currency to target: amount_base * rate."""
    return amount_base * rate


def convert_amount_to_base(amount: float, rate: float) -> float:
    """Convert an amount from target currency to base: amount / rate."""
    return amount / rate
