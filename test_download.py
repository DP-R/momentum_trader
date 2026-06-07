import yfinance as yf
import time

tickers = ['3MINDIA.NS', 'AARTIIND.NS', 'BBTC.NS', 'BHARATFORG.NS', 'CHOLAHLDNG.NS']

start = time.time()
data = yf.download(tickers, start='2020-01-01', end='2023-01-01', progress=False)
end = time.time()

print(f"Time taken for download: {end - start:.2f}s")
print(data.columns.nlevels)
print(data.columns)

# Test extracting one ticker
print(data.xs('3MINDIA.NS', axis=1, level=1).head(2))
