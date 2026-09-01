import yfinance as yf

h = yf.Ticker('HINDALCO.NS').history(period='5d')
print(h[['Open', 'High', 'Low', 'Close', 'Volume']])