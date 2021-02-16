import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

def main():
    #pd.options.display.max_rows = None
    sysmbol = input("Input Sysmbol: ")
    stockHistory = getStockPrice(sysmbol)
    zlema(stockHistory)
    #stockHistory['Close'].plot()
    #plt.xlabel("Data")
    #plt.ylabel("$ price")
    #plt.show()
    return

def getStockPrice(sysmbol):
    shock = yf.Ticker(sysmbol)
    price = shock.history(period="5y")
    return price

def zlema(data):
    period = 14
    lag = round((period - 1) / 2)
    data['shift'] = data['Close'] + (data['Close'] - data['Close'].shift(lag))
    data = data[data['shift'].notna()]
    data['ZLEMA'] = data['shift'].ewm(span=lag).mean()
    print(data['ZLEMA'])

main()
