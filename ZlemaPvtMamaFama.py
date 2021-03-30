import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import math

def main():
    sysmbol = input("Input Sysmbol: ")
    stockHistory = getStockPrice(sysmbol)
    Zlema = zlema(stockHistory)
    Zlema = pd.concat([stockHistory, Zlema], axis=1)
    PVT = pvt(stockHistory)
    PVT = pd.concat([stockHistory, PVT], axis=1)
    MamaFama = mafa(stockHistory)
    return

def getStockPrice(stock):
    stockPriceData = yf.download(stock, period="max", interval="1d")
    stockPriceData = stockPriceData.round(4)
    return stockPriceData

def zlema(data):#Using Close to calculate
    period = 14
    lag = round((period - 1) / 2)
    localData = data.copy()
    localData['Shift'] = localData['Close'] + (localData['Close'] - localData['Close'].shift(lag))
    localData['ZLEMA'] = localData['Shift'].ewm(span=period, adjust=False).mean()
    localData['ZLEMABuySell'] = np.where(localData['ZLEMA'] >= localData['ZLEMA'].shift(1), True, False)
    #localData = localData[localData['ZLEMA'].notna()]
    return localData[['ZLEMA', 'ZLEMABuySell']]

def pvt(data):#Using Volume to calculate
    signalPeriod = 21
    localData = data.copy()
    localData['CloseShift1'] = localData["Close"].shift(1)
    localData['Pre_PVT'] = ((localData['Close'] - localData['CloseShift1']) / localData['CloseShift1']) * localData['Volume']
    localData['PVT'] = localData['Pre_PVT'].cumsum()
    localData['EMA(PVT, period)'] = localData['PVT'].ewm(span=signalPeriod, adjust=False).mean()
    localData['BuySell'] = np.where(localData['PVT'] >= localData["EMA(PVT, period)"], True, False)
    '''With None output, banned by Toby
    localData['PVTCrossSignal'] = np.where(localData['PVT'] > localData['EMA(PVT, period)'], 1, 0)
    localData['PVTPositionSignal'] = localData['PVTCrossSignal'].diff()
    localData.loc[localData['PVTPositionSignal'] == 1, 'PVTBuySell'] = True
    localData.loc[localData['PVTPositionSignal'] == 0, 'PVTBuySell'] = None
    localData.loc[localData['PVTPositionSignal'] == -1, 'PVTBuySell'] = False
    #print(localData)
    #localData = localData[data['PVT'].notna()]
    return localData[['PVT', 'EMA(PVT, period)', 'PVTBuySell']]
    '''
    return localData[['PVT', 'EMA(PVT, period)', 'BuySell']]

def mafa(data):
    localData = data.copy()
    length = 20
    er_Mole = localData['Close'] - localData['Close'].shift(length)
    er_Mole = er_Mole.abs()
    er_Denomin = localData['Close'] - localData['Close'].shift(1)
    er_Denomin = er_Denomin.abs()
    er_Denomin_sum = er_Denomin.cumsum()
    er_Denomin = er_Denomin_sum - er_Denomin_sum.shift(length)
    localData['er'] = er_Mole / er_Denomin
    localData['Alpha'] = mafa_computeAlpha(localData)
    localData['Alpha/2'] = localData['Alpha'] / 2
    localData[['MAMA', 'FAMA']] = 0
    #print(localData.loc[localData.index[21], 'Alpha'] * localData.loc[localData.index[21], 'Close'] + (1 - localData.loc[localData.index[21], 'Alpha']) * mafa_nz(localData, 'MAMA', 21, 1))
    for i in range(length + 1, len(localData)):
        localData.loc[localData.index[i], 'MAMA'] = localData.loc[localData.index[i], 'Alpha'] * localData.loc[localData.index[i], 'Close'] + (1 - localData.loc[localData.index[i], 'Alpha']) * mafa_nz(localData, 'MAMA', i, 1)
        localData.loc[localData.index[i], 'FAMA'] = localData.loc[localData.index[i], 'Alpha/2'] * localData.loc[localData.index[i], 'MAMA'] + (1 - localData.loc[localData.index[i], 'Alpha/2']) * mafa_nz(localData, 'FAMA', i, 1)
    localData.to_csv("test.csv")
    #print(localData)
    return localData

def mafa_nz(data, column, current, shift):
    if current - shift < 0:
        output = 0.0
    else:
        output = data.loc[data.index[current - shift], column]
    return output

def mafa_hilbertTransform(data, column, position):
    if(position - 6 < 0):
        output = 0
    else:
        output = (0.0962 * data.loc[data.index[position], column]) + (0.5769 * data.loc[data.index[position - 2], column]) - (0.5769 * data.loc[data.index[position - 4], column]) - (0.0962 * data.loc[data.index[position - 6], column])
    return output

def mafa_computeComponent(data, column, position, masaPeriodMult):
    output =  mafa_hilbertTransform(data, column, position) * masaPeriodMult
    return output

def mafa_smoothComponent(data):
    output = (0.2 * data) + (0.8 * (data.shift(1)).fillna(0))
    return output

def mafa_computeAlpha(data):
    localData = pd.DataFrame()
    PI = 2.0 * math.asin(1)
    localData['fastLimit'] = data['er']
    localData['slowLimit'] = data['er'] * 0.1
    localData['smooth'] = ((4 * data['Close']) + (3 * (data['Close'].shift(1)).fillna(0)) + (2 * (data['Close'].shift(2)).fillna(0)) + (data['Close'].shift(3)).fillna(0)) / 10
    localData[['mesaPeriod','mesaPeriodMult','detrender','I1', 'Q1', 'jI', 'jQ', 'I2', 'Q2', 'Re', 'Im', 'phase', 'deltaPhase', 'alpha']] = 0
    for i in range(len(localData)):
        localData.loc[localData.index[i], 'mesaPeriodMult'] = 0.075 * mafa_nz(localData, 'mesaPeriod', i, 1) + 0.54
        localData.loc[localData.index[i], 'detrender'] = mafa_computeComponent(localData, 'smooth', i, localData.loc[localData.index[i], 'mesaPeriodMult'])
        localData.loc[localData.index[i], 'I1'] = mafa_nz(localData, 'detrender', i, 3)
        localData.loc[localData.index[i], 'Q1'] = mafa_computeComponent(localData, 'detrender', i, localData.loc[localData.index[i], 'mesaPeriodMult'])
        localData.loc[localData.index[i], 'jI'] = mafa_computeComponent(localData, 'I1', i, localData.loc[localData.index[i], 'mesaPeriodMult'])
        localData.loc[localData.index[i], 'jQ'] = mafa_computeComponent(localData, 'Q1', i, localData.loc[localData.index[i], 'mesaPeriodMult'])
        localData.loc[localData.index[i], 'I2'] = localData.loc[localData.index[i], 'I1'] - localData.loc[localData.index[i], 'jQ']
        localData.loc[localData.index[i], 'Q2'] = localData.loc[localData.index[i], 'Q1'] + localData.loc[localData.index[i], 'jI']
        localData.loc[localData.index[i], 'I2'] = 0.2 * localData.loc[localData.index[i], 'I2'] + 0.8 * mafa_nz(localData, 'I2', i, 1)
        localData.loc[localData.index[i], 'Q2'] = 0.2 * localData.loc[localData.index[i], 'Q2'] + 0.8 * mafa_nz(localData, 'Q2', i, 1)
        localData.loc[localData.index[i], 'Re'] = localData.loc[localData.index[i], 'I2'] * mafa_nz(localData, 'I2', i, 1) + localData.loc[localData.index[i], 'Q2'] * mafa_nz(localData, 'Q2', i, 1)
        localData.loc[localData.index[i], 'Im'] = localData.loc[localData.index[i], 'I2'] * mafa_nz(localData, 'Q2', i, 1) - localData.loc[localData.index[i], 'Q2'] * mafa_nz(localData, 'I2', i, 1)
        localData.loc[localData.index[i], 'Re'] = 0.2 * localData.loc[localData.index[i], 'Re'] + 0.8 * mafa_nz(localData, 'Re', i, 1)
        localData.loc[localData.index[i], 'Im'] = 0.2 * localData.loc[localData.index[i], 'Im'] + 0.8 * mafa_nz(localData, 'Im', i, 1)
        if(localData.loc[localData.index[i], 'Re'] != 0 and localData.loc[localData.index[i], 'Im'] != 0):
            localData.loc[localData.index[i], 'mesaPeriod'] = 2 * PI / math.atan(localData.loc[localData.index[i], 'Im'] / localData.loc[localData.index[i], 'Re'])
        if(localData.loc[localData.index[i], 'mesaPeriod'] > 1.5 * mafa_nz(localData, 'mesaPeriod', i, 1)):
            localData.loc[localData.index[i], 'mesaPeriod'] = 1.5 * mafa_nz(localData, 'mesaPeriod', i, 1)
        if(localData.loc[localData.index[i], 'mesaPeriod'] < 0.67 * mafa_nz(localData, 'mesaPeriod', i, 1)):
            localData.loc[localData.index[i], 'mesaPeriod'] = 0.67 * mafa_nz(localData, 'mesaPeriod', i, 1)
        if(localData.loc[localData.index[i], 'mesaPeriod'] < 6):
            localData.loc[localData.index[i], 'mesaPeriod'] = 6
        if(localData.loc[localData.index[i], 'mesaPeriod'] > 50):
            localData.loc[localData.index[i], 'mesaPeriod'] = 50

        localData.loc[localData.index[i], 'mesaPeriod'] = 0.2 * localData.loc[localData.index[i], 'mesaPeriod'] + 0.8 * mafa_nz(localData, 'mesaPeriod', i, 1)

        if(localData.loc[localData.index[i], 'I1'] != 0):
            localData.loc[localData.index[i], 'phase'] = (180 / PI) * math.atan(localData.loc[localData.index[i], 'Q1'] / localData.loc[localData.index[i], 'I1'])

        localData.loc[localData.index[i], 'deltaPhase'] = mafa_nz(localData, 'phase', i, 1) - localData.loc[localData.index[i], 'phase']
        if(localData.loc[localData.index[i], 'deltaPhase'] < 1):
            localData.loc[localData.index[i], 'deltaPhase'] = 1

        localData.loc[localData.index[i], 'alpha'] = localData.loc[localData.index[i], 'fastLimit'] / localData.loc[localData.index[i], 'deltaPhase']
        if(localData.loc[localData.index[i], 'alpha'] < localData.loc[localData.index[i], 'slowLimit']):
             localData.loc[localData.index[i], 'alpha'] = localData.loc[localData.index[i], 'slowLimit']
    output = localData['alpha'].tolist()
    return output

main()
