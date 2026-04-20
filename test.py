import yfinance as yf

df = yf.download("BTC-USD", start="2020-01-01", end="2024-01-01")
print(df.head())
print("行数:", len(df))