import os
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from src.models.transaction import Transaction
from src.models.actions import is_valid_action
from src.fetch_fx_rates import get_fx_rates, convert_amount_to_base
from src.fetch_yfinance import get_ticker_info, get_current_prices
from src.date_utils import get_date_year

load_dotenv()

BASE_CURRENCY = os.getenv("BASE_CURRENCY", "SGD")


def create_new_transaction(transaction: Transaction) -> pd.DataFrame:
    # Validate the action
    if not is_valid_action(transaction.action):
        raise ValueError(f"Action '{transaction.action}' is not accepted.")

    converted_value = transaction.value
    if transaction.currency != BASE_CURRENCY:
        fx_rates = get_fx_rates(BASE_CURRENCY, [transaction.currency])
        converted_value = convert_amount_to_base(
            transaction.value, fx_rates[transaction.currency]
        )

    formatted_date, year = get_date_year(transaction.date)
    new_transaction = {
        "Date": formatted_date,
        "Portfolio": transaction.portfolio,
        "Ticker": transaction.ticker,
        "Quantity": 1 if transaction.quantity is None else transaction.quantity,
        "Currency": transaction.currency,
        "Action": transaction.action,
        "Value": transaction.value,
        "Value (base)": converted_value,
        "Price per Unit": converted_value
        / (transaction.quantity if transaction.quantity is not None else 1),
        **(
            get_ticker_info(transaction.ticker)
            if transaction.ticker not in {"NA"}
            else {}
        ),
        "Year": year,
    }
    new_transaction_df = pd.DataFrame([new_transaction])

    return new_transaction_df


def prepare_transactions_df(transactions: pd.DataFrame) -> pd.DataFrame:
    # Work on a copy to avoid mutating original
    df = transactions.copy()

    # Normalize action column (safety)
    df["Action"] = df["Action"].str.upper().str.strip()
    df["Ticker"] = df["Ticker"].str.strip()
    df["Currency"] = df["Currency"].str.upper().str.strip()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    print(df["Date"])
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df["Value (base)"] = pd.to_numeric(df["Value (base)"], errors="coerce")

    # Sort for stable WAC calc
    df = df.sort_values(["Portfolio", "Ticker", "Currency", "Date"])
    print(df["Date"])
    return df


def compute_holdings_wac(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute holdings using Weighted Average Cost (WAC) method.
    Inputs:
    - df: pd.DataFrame of transactions sheet
    Returns:
    - pd.DataFrame: Holdings dataframe grouped by Portfolio and Ticker
    """
    group_cols = ["Portfolio", "Ticker", "Asset Name", "Asset Class", "Currency"]
    rows = []
    for key, group in df.groupby(group_cols, sort=["Date"]):
        portfolio, ticker, asset_name, asset_class, currency = key
        shares = 0
        cost_basis_base = 0.0  # remaining cost basis in base currency
        net_cashflow_base = 0.0  # buys - sells (outflow - inflow), can go negative

        for _, row in group.iterrows():
            action = row["Action"]
            qty = row["Quantity"]
            val_base = row["Value (base)"]
            if "DIDI" in ticker:
                print(action, qty, val_base, shares)
            if pd.isna(qty) or pd.isna(val_base):
                continue

            if action == "BUY":
                shares += qty
                cost_basis_base += val_base
                net_cashflow_base += val_base

            elif action == "SELL":
                avg_cost = cost_basis_base / shares if shares > 0 else 0.0
                cost_basis_base -= qty * avg_cost
                shares -= qty
                net_cashflow_base -= val_base
            else:
                # Dividend/Fee/etc excluded from holdings basis by default.
                # You can incorporate fees into cost basis if desired.
                continue
        # floating-point cleanup
        if shares < 1e-12:
            shares = 0
        if cost_basis_base < 1e-8:
            cost_basis_base = 0.0

        if shares != 0:
            rows.append(
                {
                    "Portfolio": portfolio,
                    "Ticker": ticker,
                    "Asset Name": asset_name,
                    "Asset Class": asset_class,
                    "Currency": currency,
                    "Net Quantity": shares,
                    "Cost Basis Remaining (base)": cost_basis_base,
                    "Avg Cost (base)": (
                        (cost_basis_base / shares) if shares != 0 else np.nan
                    ),
                    "Net Cashflow (base)": net_cashflow_base,
                    "House Money (base)": max(-net_cashflow_base, 0.0),
                }
            )

    return pd.DataFrame(rows)


def attach_current_prices_values(holdings: pd.DataFrame) -> pd.DataFrame:
    if holdings.empty:
        return holdings

    unique_tickers = holdings["Ticker"].dropna().unique()
    price_map = get_current_prices(unique_tickers, 3)
    if price_map is None:
        raise TypeError(
            "get_ticker_price(unique_tickers) returned None; expected dict-like {ticker: price}."
        )

    holdings["Current Price Per Unit"] = holdings["Ticker"].map(price_map)
    holdings["Current Value"] = (
        holdings["Net Quantity"] * holdings["Current Price Per Unit"]
    )

    # FX Conversion
    unique_currencies = holdings["Currency"].dropna().unique()
    filtered_currencies = [
        currency for currency in unique_currencies if currency != BASE_CURRENCY
    ]
    fx_rates = get_fx_rates(BASE_CURRENCY, filtered_currencies)
    if BASE_CURRENCY in unique_currencies:
        fx_rates[BASE_CURRENCY] = 1.0
    holdings["FX_RATE"] = holdings["Currency"].map(fx_rates)

    # Convert to base currency
    holdings["Current Value (base)"] = holdings["Current Value"] / holdings["FX_RATE"]

    # Unrealized P/L
    holdings["Unrealised P/L (base)"] = (
        holdings["Current Value (base)"] - holdings["Cost Basis Remaining (base)"]
    )
    holdings["Unrealised P/L % (base)"] = np.where(
        holdings["Cost Basis Remaining (base)"] > 0,
        holdings["Unrealised P/L (base)"] / holdings["Cost Basis Remaining (base)"],
        np.nan,
    )
    return holdings


def attach_portfolio_weights(holdings: pd.DataFrame) -> pd.DataFrame:
    holdings["Portfolio Total Value (base)"] = holdings.groupby("Portfolio")[
        "Current Value (base)"
    ].transform("sum")
    holdings["Portfolio Weight (base)"] = np.where(
        holdings["Portfolio Total Value (base)"] > 0,
        holdings["Current Value (base)"] / holdings["Portfolio Total Value (base)"],
        np.nan,
    )
    return holdings


def finalise_holdings(holdings: pd.DataFrame) -> pd.DataFrame:
    if holdings.empty:
        return holdings

    # Optional rounding for display
    numeric_cols = [
        "Net Quantity",
        "Cost Basis Remaining (base)",
        "Avg Cost (base)",
        "Current Price Per Unit",
        "FX_RATE",
        "Current Value",
        "Current Value (base)",
        "Unrealised P/L (base)",
        "Unrealised P/L % (base)",
        "Net Cashflow (base)",
        "House Money (base)",
        "Portfolio Total Value (base)",
        "Portfolio Weight (base)",
    ]

    holdings[numeric_cols] = holdings[numeric_cols].round(4)

    # Optional: sort nicely
    holdings = holdings.sort_values(
        ["Portfolio", "Portfolio Weight (base)", "Ticker"],
        ascending=[True, False, True],
    )

    return holdings


def generate_holdings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate holdings sheet from transaction dataframe.
    Inputs:
    - df: pd.DataFrame of transactions sheet
    Returns:
    - pd.DataFrame: Holdings dataframe grouped by Portfolio and Ticker
    """
    df = prepare_transactions_df(df)
    holdings = compute_holdings_wac(df)
    holdings = attach_current_prices_values(holdings)
    holdings = attach_portfolio_weights(holdings)
    holdings = finalise_holdings(holdings)

    return holdings


def generate_dividends(transactions: pd.DataFrame) -> pd.DataFrame:
    dividends_df = transactions[transactions["Action"] == "DIVIDEND"].copy()
    dividends_df = dividends_df.dropna(subset=["Date", "Value (base)"])

    # Extract year
    dividends_df["Date"] = pd.to_datetime(dividends_df["Date"], errors="coerce")
    dividends_df["Year"] = dividends_df["Date"].dt.year

    dividends_df["Value (base)"] = pd.to_numeric(
        dividends_df["Value (base)"], errors="coerce"
    )

    # Aggregate
    dividends_summary = (
        dividends_df.groupby(
            ["Year", "Portfolio", "Ticker", "Asset Name"], as_index=False
        )["Value (base)"]
        .sum()
        .rename(columns={"Value (base)": "Total Dividends"})
    )

    # Average monthly dividend across full year
    dividends_summary["Average Monthly Dividend"] = (
        dividends_summary["Total Dividends"] / 12
    )

    # Optional rounding
    dividends_summary["Total Dividends"] = dividends_summary["Total Dividends"].round(4)
    dividends_summary["Average Monthly Dividend"] = dividends_summary[
        "Average Monthly Dividend"
    ].round(4)

    # Sort nicely
    dividends_summary = dividends_summary.sort_values(
        ["Year", "Portfolio", "Ticker"]
    ).reset_index(drop=True)

    return dividends_summary


def generate_portfolio_dividends(dividends_df: pd.DataFrame) -> pd.DataFrame:
    portfolio_dividends = (
        dividends_df.groupby(["Year", "Portfolio"], as_index=False)["Total Dividends"]
        .sum()
        .rename(columns={"Total Dividends": "Portfolio Total Dividends"})
    )
    # Average monthly dividend across full year
    portfolio_dividends["Average Monthly Dividend"] = (
        portfolio_dividends["Portfolio Total Dividends"] / 12
    )

    portfolio_dividends["Portfolio Total Dividends"] = portfolio_dividends[
        "Portfolio Total Dividends"
    ].round(4)
    portfolio_dividends["Average Monthly Dividend"] = portfolio_dividends[
        "Average Monthly Dividend"
    ].round(4)

    portfolio_dividends = portfolio_dividends.sort_values(
        ["Year", "Portfolio"]
    ).reset_index(drop=True)

    return portfolio_dividends
