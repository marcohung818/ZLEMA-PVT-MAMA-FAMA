import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def main():
    sysmbol = input("Input Sysmbol: ")
    stock = yf.Ticker(sysmbol)
    stockHistory = getStockPrice(stock)
    zlemabuysell = zlema(stockHistory)
    #print(zlemabuysell)
    #pvtbuysell = pvt(stockHistory)
    #mafabuysell = mafa(stockHistory)
    return

def getStockPrice(stock):
    price = stock.history(period="5y")
    return price

def zlema(data):#Using Close to calculate
    period = 14
    lag = round((period - 1) / 2)
    data['shift'] = data['Close'] + (data['Close'] - data['Close'].shift(lag))
    data['ZLEMA'] = data['shift'].ewm(span=period, adjust=False).mean()
    data['ZLEMABuySell'] = np.where(data['ZLEMA'] >= data['ZLEMA'].shift(1), True, False)
    data = data[data['shift'].notna()]
    data = data.iloc[1:]
    print(data)
    return data['ZLEMABuySell']

def pvt(data):#Using Volume to calculate
    print(data['Volume'])
    return

pd.options.display.max_rows = None
main()
