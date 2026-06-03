from tqdm import tqdm
import yfinance as yf


def get_current_prices(tickers, digits=5) -> dict:
    """
    Given a list of ticker symbols, return a dict of {ticker: current_price}.
    Uses Yahoo Finance via the yfinance library.
    """
    if isinstance(tickers, str):
        tickers = [tickers]

    prices = {}
    for ticker in tqdm(tickers, desc="fetching ticker prices"):
        ticker_info = yf.Ticker(ticker).info
        current_price = ticker_info.get("Open")
        if not current_price:
            current_price = ticker_info.get("previousClose")
        if not current_price:
            print(f"Could not get price for {ticker}")
            continue
        prices[ticker] = round(current_price, digits)
    return prices


def get_ticker_info(ticker):
    info = yf.Ticker(ticker)
    asset_name = info.info.get("displayName")
    if not asset_name:
        asset_name = info.info["longName"]
    ticker_info = {
        "Asset Name": asset_name,
        "Asset Class": info.info["typeDisp"],
    }
    return ticker_info
