from src.fetch_yfinance import get_current_prices

# example usage

def main():
    tickers = ["JYEU.SI", "MSFT", "GOOG", "TSLA"]
    current_prices = get_current_prices(tickers)
    for tkr, price in current_prices.items():
        print(f"{tkr}: {price}")   

if __name__ == "__main__":
    main() 