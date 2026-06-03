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
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df["Value (base)"] = pd.to_numeric(df["Value (base)"], errors="coerce")

    # Sort for stable WAC calc
    df = df.sort_values(["Portfolio", "Ticker", "Currency", "Date"]).reset_index(drop=True)
    return df


def process_transactions_wac(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Process transactions using Weighted Average Cost (WAC).

    Return:
    - holdings_df : pd.DataFrame (Open positions only)
    - realised_pl_df : pd.DataFrame (One row per SELL transaction)
    """
    group_cols = ["Portfolio", "Ticker", "Asset Name", "Asset Class", "Currency"]

    holdings_rows = []
    realised_rows = []

    for key, group in df.groupby(group_cols, sort=False):
        portfolio, ticker, asset_name, asset_class, currency = key

        shares = 0
        cost_basis_base = 0.0
        net_cashflow_base = 0.0

        for _, row in group.iterrows():
            action = row["Action"]
            qty = row["Quantity"]
            val_base = row["Value (base)"]

            if pd.isna(qty) or pd.isna(val_base):
                continue

            val_base = float(val_base)

            if action == "BUY":
                shares += qty
                cost_basis_base += val_base
                net_cashflow_base += val_base

            elif action == "SELL":
                if shares <= 0:
                    continue

                avg_cost = cost_basis_base / shares if shares > 0 else 0.0
                cost_of_shares_sold = qty * avg_cost
                realised_pl = val_base - cost_of_shares_sold
                realised_pl_pct = (
                    realised_pl / cost_of_shares_sold
                    if cost_of_shares_sold > 0 else np.nan
                )

                realised_rows.append(
                    {
                        "Date": row["Date"],
                        "Portfolio": portfolio,
                        "Ticker": ticker,
                        "Asset Name": asset_name,
                        "Asset Class": asset_class,
                        "Currency": currency,
                        "Quantity Sold": qty,
                        "Sell Value (base)": val_base,
                        "Avg Cost Per Unit Before Sell (base)": avg_cost,
                        "Cost of Shares Sold (base)": cost_of_shares_sold,
                        "Realised P/L (base)": realised_pl,
                        "Realised P/L % (base)": realised_pl_pct,
                    }
                )

                cost_basis_base -= cost_of_shares_sold
                shares -= qty
                net_cashflow_base -= val_base

            else:
                continue

        # floating point cleanup
        if shares < 1e-12:
            shares = 0.0
        if cost_basis_base < 1e-8:
            cost_basis_base = 0.0

        if shares != 0:
            holdings_rows.append(
                {
                    "Portfolio": portfolio,
                    "Ticker": ticker,
                    "Asset Name": asset_name,
                    "Asset Class": asset_class,
                    "Currency": currency,
                    "Net Quantity": shares,
                    "Cost Basis Remaining (base)": cost_basis_base,
                    "Avg Cost (base)": (
                        cost_basis_base / shares if shares > 0 else np.nan
                    ),
                    "Net Cashflow (base)": net_cashflow_base,
                    "House Money (base)": max(-net_cashflow_base, 0.0),
                }
            )

    holdings_df = pd.DataFrame(holdings_rows)
    realised_pl_df = pd.DataFrame(realised_rows)

    return holdings_df, realised_pl_df


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
    ).reset_index(drop=True)

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
    holdings, _ = process_transactions_wac(df)
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


def generate_portfolio_summary(holdings_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate portfolio-level summary from holdings sheet.
    """

    # Aggregate per portfolio
    summary = holdings_df.groupby("Portfolio", as_index=False).agg(
        Total_Value_Base=("Current Value (base)", "sum"),
        Total_Cost_Base=("Cost Basis Remaining (base)", "sum"),
        Unrealised_PL_Base=("Unrealised P/L (base)", "sum"),
    )

    # P/L %
    summary["PL_%"] = np.where(
        summary["Total_Cost_Base"] > 0,
        summary["Unrealised_PL_Base"] / summary["Total_Cost_Base"],
        np.nan,
    )

    # % of total net worth
    total_networth = summary["Total_Value_Base"].sum()

    summary["%_of_Total_NetWorth"] = np.where(
        total_networth > 0,
        summary["Total_Value_Base"] / total_networth,
        np.nan,
    )

    # Formatting
    summary["Total_Value_Base"] = summary["Total_Value_Base"].round(4)
    summary["Total_Cost_Base"] = summary["Total_Cost_Base"].round(4)
    summary["Unrealised_PL_Base"] = summary["Unrealised_PL_Base"].round(4)
    summary["PL_%"] = summary["PL_%"].round(4)
    summary["%_of_Total_NetWorth"] = summary["%_of_Total_NetWorth"].round(4)

    summary = summary.sort_values("Total_Value_Base", ascending=False).reset_index(
        drop=True
    )

    return summary


def generate_dividend_recovery_sheet(
    holdings_df: pd.DataFrame,
    dividends_asset_df: pd.DataFrame,
) -> pd.DataFrame:
    """Generate a dividend recovery sheet per portfolio + ticker"""

    # Aggregate just in case either sheet has duplicates
    holdings_summary = holdings_df.groupby(
        ["Portfolio", "Ticker", "Asset Name"], as_index=False
    )["Cost Basis Remaining (base)"].sum()

    dividends_summary = dividends_asset_df.groupby(
        ["Portfolio", "Ticker", "Asset Name"], as_index=False
    )["Total Dividends"].sum()

    recovery_df = holdings_summary.merge(
        dividends_summary,
        on=["Portfolio", "Ticker", "Asset Name"],
        how="left",
    )

    recovery_df["Total Dividends"] = recovery_df["Total Dividends"].fillna(0.0)

    recovery_df["Dividend Recovery %"] = np.where(
        recovery_df["Cost Basis Remaining (base)"] > 0,
        recovery_df["Total Dividends"] / recovery_df["Cost Basis Remaining (base)"],
        np.nan,
    )

    recovery_df["Net Capital Remaining After Dividends"] = (
        recovery_df["Cost Basis Remaining (base)"] - recovery_df["Total Dividends"]
    )

    recovery_df["Paid For?"] = np.where(
        recovery_df["Net Capital Remaining After Dividends"] <= 0,
        "Yes",
        "No",
    )

    numeric_cols = [
        "Cost Basis Remaining (base)",
        "Total Dividends",
        "Dividend Recovery %",
        "Net Capital Remaining After Dividends",
    ]
    recovery_df[numeric_cols] = recovery_df[numeric_cols].round(4)

    recovery_df = recovery_df.sort_values(
        ["Portfolio", "Dividend Recovery %", "Ticker"],
        ascending=[True, False, True],
    ).reset_index(drop=True)

    return recovery_df

def finalise_realised_pl(realised_pl: pd.DataFrame) -> pd.DataFrame:
    if realised_pl.empty:
        return realised_pl

    realised_pl = realised_pl.copy()

    numeric_cols = [
        "Quantity Sold",
        "Sell Value (base)",
        "Avg Cost Per Unit Before Sell (base)",
        "Cost of Shares Sold (base)",
        "Realised P/L (base)",
        "Realised P/L % (base)",
    ]

    realised_pl[numeric_cols] = realised_pl[numeric_cols].round(4)

    realised_pl = realised_pl.sort_values(
        ["Date", "Portfolio", "Ticker"]
    ).reset_index(drop=True)

    return realised_pl


def generate_realised_pl_sheet(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate realised P/L sheet from transaction dataframe.
    """
    df = prepare_transactions_df(df)
    _, realised_pl = process_transactions_wac(df)
    realised_pl = finalise_realised_pl(realised_pl)
    return realised_pl

def generate_total_return_sheet(holdings_df: pd.DataFrame, realised_pl_df: pd.DataFrame, dividends_df: pd.DataFrame) -> pd.DataFrame:
    """
    using holdings, realised P/L and dividends,
    Generate total return sheet by combining realised P/L and dividends.
    """
    holdings = holdings_df.copy()

    holdings_summary = holdings[
        [
            "Portfolio",
            "Ticker",
            "Asset Name",
            "Cost Basis Remaining (base)",
            "Current Value (base)",
            "Unrealised P/L (base)",
            "Net Cashflow (base)",
        ]
    ]

    # Aggregate dividends per portfolio + ticker
    dividends_summary = dividends_df.groupby(
        ["Portfolio", "Ticker"], as_index=False
    )["Total Dividends"].sum()

    # Aggregate realised P/L per portfolio + ticker
    realised_pl_summary = realised_pl_df.groupby(
        ["Portfolio", "Ticker"], as_index=False
    )["Realised P/L (base)"].sum()

    total_return_df = holdings_summary.merge(
        dividends_summary,
        on=["Portfolio", "Ticker"],
        how="left",
    ).merge(
        realised_pl_summary,
        on=["Portfolio", "Ticker"],
        how="left",
    )

    total_return_df["Total Dividends"] = total_return_df["Total Dividends"].fillna(0.0)
    total_return_df["Realised P/L (base)"] = total_return_df[
        "Realised P/L (base)"
    ].fillna(0.0)
    total_return_df["Total Cost (base)"] = total_return_df["Net Cashflow (base)"]
    total_return_df["Total Return (base)"] = (
        total_return_df["Unrealised P/L (base)"]
        + total_return_df["Realised P/L (base)"]
        + total_return_df["Total Dividends"]
    )

    total_return_df["Total Return % (base)"] = np.where(
        total_return_df["Total Cost (base)"] != 0,
        total_return_df["Total Return (base)"] / total_return_df["Total Cost (base)"],
        np.nan,
    )


    numeric_cols = [
        "Total Cost (base)",
        "Unrealised P/L (base)",
        "Realised P/L (base)",
        "Total Dividends",
        "Total Return (base)",
        "Total Return % (base)",
    ]
    total_return_df[numeric_cols] = total_return_df[numeric_cols].round(4)

    total_return_df = total_return_df.sort_values(
        ["Portfolio", "Total Return (base)", "Ticker"],
        ascending=[True, False, True],
    ).reset_index(drop=True)

    return total_return_df