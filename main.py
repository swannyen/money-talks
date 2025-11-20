from src.fetch_yfinance import get_current_prices
from src.fetch_fx_rates import get_fx_rates, convert_amount

# example usage

def main():
    tickers = ["JYEU.SI", "MSFT", "GOOG", "TSLA"]
    current_prices = get_current_prices(tickers)
    for tkr, price in current_prices.items():
        print(f"{tkr}: {price}")   

    base = "HKD"
    targets = ["SGD", "USD", "EUR"]
    amount_hkd = 5473

    rates = get_fx_rates(base, targets)

    print(f"Base currency: {base}")
    print(f"Amount in {base}: {amount_hkd}")
    print(f"\nExchange rates (per 1 {base}):")
    for cur, r in rates.items():
        print(f"  1 {base} = {round(r, 3)} {cur}")

    print("\nConverted amounts:")
    for cur, r in rates.items():
        converted = convert_amount(amount_hkd, r)
        print(f"  {amount_hkd} {base} = {converted:.2f} {cur}")


if __name__ == "__main__":
    main() 