import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def main():
    sysmbol = input("Input Sysmbol: ")
    #stock = yf.Ticker(sysmbol)
    stockHistory = getStockPrice(sysmbol)
    #zlemabuysell = zlema(stockHistory)
    pvtbuysell = pvt(stockHistory)
    #mafabuysell = mafa(stockHistory)
    return

def getStockPrice(stock):
    stockPriceData = yf.download(stock, period="max", interval="1d")
    stockPriceData = stockPriceData.round(4)
    #print(stockPriceData)
    return stockPriceData

def zlema(data):#Using Close to calculate
    period = 14
    lag = round((period - 1) / 2)
    data['Shift'] = data['Close'] + (data['Close'] - data['Close'].shift(lag))
    data['ZLEMA'] = data['Shift'].ewm(span=period, adjust=False).mean()
    data['ZLEMABuySell'] = np.where(data['ZLEMA'] >= data['ZLEMA'].shift(1), True, False)
    data = data[data['ZLEMA'].notna()]
    return data['ZLEMABuySell']

def pvt(data):#Using Volume to calculate
    signalPeriod = 21
    data['CloseShift1'] = data["Close"].shift(1)
    data['Pre_PVT'] = ((data['Close'] - data['CloseShift1']) / data['CloseShift1']) * data['Volume']
    data['PVT'] = data['Pre_PVT'].cumsum()
    data['Signal'] = data['PVT'].ewm(span=signalPeriod, adjust=False).mean()
    data['Signal_plus1day'] = data['Signal'].shift(-1)
    data['Signal_minus1day'] = data['Signal'].shift(1)
    data = data[['Close', 'CloseShift1', 'Volume','Pre_PVT', 'PVT', 'Signal', 'Signal_plus1day', 'Signal_minus1day']]
    data = data[data['PVT'].notna()]

    print(data)
    return data

#pd.options.display.max_rows = None
main()
