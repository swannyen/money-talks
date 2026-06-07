import logging
from itertools import batched
from typing import Iterable

import pandas as pd
import yfinance as yf
from tqdm import tqdm
from yfinance.exceptions import YFRateLimitError

logger = logging.getLogger(__name__)

BATCH_SIZE = 50
CLOSE_FIELDS = ("Close", "Adj Close", "Open")


def _extract_last_price(data: pd.DataFrame, symbol: str) -> float | None:
    if data.empty or not isinstance(data.columns, pd.MultiIndex):
        return None
    if symbol not in data.columns.get_level_values(0):
        return None

    for field in CLOSE_FIELDS:
        if (symbol, field) not in data.columns:
            continue
        series = data[(symbol, field)].dropna()
        if not series.empty:
            return float(series.iloc[-1])
    return None


def _download_prices(symbols: list[str], digits: int) -> dict[str, float]:
    data = yf.download(
        symbols,
        period="5d",
        group_by="ticker",
        threads=True,
        progress=False,
        auto_adjust=False,
    )
    if data is None or data.empty:
        return {}

    prices: dict[str, float] = {}
    for symbol in symbols:
        value = _extract_last_price(data, symbol)
        if value is not None:
            prices[symbol] = round(value, digits)
        else:
            logger.warning("No price data returned for %s", symbol)
    return prices


def get_current_prices(
    tickers: Iterable[str] | str, digits: int = 5
) -> dict[str, float]:
    """Fetch latest prices in bulk via yfinance.download()."""
    if isinstance(tickers, str):
        tickers = [tickers]

    seen: set[str] = set()
    symbols: list[str] = []
    for ticker in tickers:
        if ticker is None or (isinstance(ticker, float) and pd.isna(ticker)):
            continue
        symbol = str(ticker).strip()
        if not symbol or symbol.upper() == "NA" or symbol in seen:
            continue
        seen.add(symbol)
        symbols.append(symbol)

    if not symbols:
        return {}

    prices: dict[str, float] = {}
    batch_count = (len(symbols) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch in tqdm(
        batched(symbols, BATCH_SIZE),
        desc="Fetching ticker prices",
        total=batch_count,
    ):
        batch_symbols = list(batch)
        try:
            prices.update(_download_prices(batch_symbols, digits))
        except YFRateLimitError:
            logger.warning(
                "Yahoo Finance rate limit hit while fetching prices for: %s",
                batch_symbols,
            )
            break
        except Exception as exc:
            logger.warning(
                "Bulk price fetch failed for batch %s: %s", batch_symbols, exc
            )

    return prices


def get_ticker_info(ticker: str) -> dict[str, str]:
    """Fetch asset metadata for a single ticker."""
    empty = {"Asset Name": "", "Asset Class": ""}
    symbol = str(ticker).strip()
    if not symbol or symbol.upper() == "NA":
        return empty

    try:
        info = yf.Ticker(symbol).info
    except YFRateLimitError:
        logger.warning("Yahoo Finance rate limit hit while fetching info for %s", symbol)
        return empty
    except Exception as exc:
        logger.warning("Failed to fetch ticker info for %s: %s", symbol, exc)
        return empty

    asset_name = info.get("displayName") or info.get("longName") or ""
    return {
        "Asset Name": asset_name,
        "Asset Class": info.get("typeDisp", "") or "",
    }
