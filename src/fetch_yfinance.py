import yfinance as yf

def get_current_prices(tickers, digits = 5) -> dict:
    """
    Given a list of ticker symbols, return a dict of {ticker: current_price}.
    Uses Yahoo Finance via the yfinance library.
    """
    if isinstance(tickers, str):
        tickers = [tickers]

    # Download live data for all tickers at once
    data = yf.download(
        tickers=" ".join(tickers),
        period="1d",
        interval="1m",
        progress=False,
        group_by="ticker",
        auto_adjust=False,
        prepost=False
    )

    prices = {}

    # Handle single-ticker and multi-ticker shapes
    for ticker in tickers:
        try:
            if len(tickers) == 1:
                # For a single ticker, columns are not grouped by ticker
                last_valid_row = data["Close"].dropna().iloc[-1]
            else:
                # For multiple tickers, columns are MultiIndex (ticker, field)
                last_valid_row = data[ticker]["Close"].dropna().iloc[-1]

            prices[ticker] = round(float(last_valid_row), digits)
        except Exception as e:
            # If something goes wrong for a ticker, set it to None
            prices[ticker] = None
            print(f"Could not get price for {ticker}: {e}")

    return prices
