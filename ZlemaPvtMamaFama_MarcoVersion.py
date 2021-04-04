import yfinance as yf
import pandas as pd
import numpy as np
import math

def main(sysmbol):
    #sysmbol = input("Input Sysmbol: ")
    stockHistory = getStockPrice(sysmbol)
    result = stockHistory.copy()
    result['Zlema'] = zlema(stockHistory)
    #Zlema = pd.concat([stockHistory, Zlema], axis=1)
    result['PVT'] = pvt(stockHistory)
    #PVT = pd.concat([stockHistory, PVT], axis=1)
    result['MAMAFAMA'] = mafa(stockHistory)
    result[['BuySellCount', 'BuySell']] = 0
    for i in range(0, len(result)):
        if(result.loc[result.index[i], 'Zlema'] == True):
            result.loc[result.index[i], 'BuySellCount'] += 1
        elif(result.loc[result.index[i], 'Zlema'] == False):
            result.loc[result.index[i], 'BuySellCount'] -= 1
        if(result.loc[result.index[i], 'PVT'] == True):
            result.loc[result.index[i], 'BuySellCount'] += 1
        elif(result.loc[result.index[i], 'PVT'] == False):
            result.loc[result.index[i], 'BuySellCount'] -= 1
        if(result.loc[result.index[i], 'MAMAFAMA'] == True):
            result.loc[result.index[i], 'BuySellCount'] += 1
        elif(result.loc[result.index[i], 'MAMAFAMA'] == False):
            result.loc[result.index[i], 'BuySellCount'] -= 1
        if(result.loc[result.index[i], 'BuySellCount'] >= 2):
            result.loc[result.index[i], 'BuySell'] = "Buy"
        elif(result.loc[result.index[i], 'BuySellCount'] <= -2):
            result.loc[result.index[i], 'BuySell'] = "Sell"
    return result['BuySell']

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
    return localData['ZLEMABuySell']

def pvt(data):#Using Volume to calculate
    signalPeriod = 21
    localData = data.copy()
    localData['CloseShift1'] = localData["Close"].shift(1)
    localData['Pre_PVT'] = ((localData['Close'] - localData['CloseShift1']) / localData['CloseShift1']) * localData['Volume']
    localData['PVT'] = localData['Pre_PVT'].cumsum()
    localData['EMA(PVT, period)'] = localData['PVT'].ewm(span=signalPeriod, adjust=False).mean()
    localData['PVTCrossSignal'] = np.where(localData['PVT'] > localData['EMA(PVT, period)'], 1, 0)
    localData['PVTPositionSignal'] = localData['PVTCrossSignal'].diff()
    localData.loc[localData['PVTPositionSignal'] == 1, 'PVTBuySell'] = True
    localData.loc[localData['PVTPositionSignal'] == 0, 'PVTBuySell'] = None
    localData.loc[localData['PVTPositionSignal'] == -1, 'PVTBuySell'] = False
    return localData['PVTBuySell']

def mafa(data):
    localData = data.copy()
    length = 20
    fast_length = 10
    slow_length = 20
    crypto_boolean = False
    normalize = 300
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
    for i in range(length + 1, len(localData)):
        localData.loc[localData.index[i], 'MAMA'] = localData.loc[localData.index[i], 'Alpha'] * localData.loc[localData.index[i], 'Close'] + (1 - localData.loc[localData.index[i], 'Alpha']) * mafa_nz(localData, 'MAMA', i, 1)
        localData.loc[localData.index[i], 'FAMA'] = localData.loc[localData.index[i], 'Alpha/2'] * localData.loc[localData.index[i], 'MAMA'] + (1 - localData.loc[localData.index[i], 'Alpha/2']) * mafa_nz(localData, 'FAMA', i, 1)
    localData['fast_ma'] = localData['Close'].ewm(span=fast_length, adjust=False).mean()
    localData['slow_ma'] = localData['Close'].ewm(span=slow_length, adjust=False).mean()
    localData['macd'] = localData['fast_ma'] - localData['slow_ma']
    localData['hist'] = localData['MAMA'] - localData['FAMA']
    localData['hist_z'] = localData['hist'] - localData['hist'].rolling(normalize).mean()
    localData[['hist_z_sd', 'macd_z_sd', 'macd_z_std']] = 0
    for i in range(normalize + 1, len(localData)):
        localData.loc[localData.index[i], 'hist_z_sd'] = mafa_pine_script_stdev(localData, 'hist', i, normalize)
    localData['hist_z'] = localData['hist_z'] / localData['hist_z_sd']
    localData['macd_z'] = localData['macd'] - localData['macd'].rolling(normalize).mean()
    for i in range(normalize + 1, len(localData)):
        localData.loc[localData.index[i], 'macd_z_sd'] = mafa_pine_script_stdev(localData, 'macd', i, normalize)
    localData['macd_z'] = localData['macd_z'] / localData['macd_z_sd']
    for i in range(normalize + 1, len(localData)):
        localData.loc[localData.index[i], 'macd_z_std'] = mafa_pine_script_stdev(localData, 'macd_z', i, 20)
    localData['hist_z_ema5'] = localData['hist_z'].ewm(span=10, adjust=False).mean()
    localData['HISTCrossSignal'] = np.where(localData['hist_z'] > localData['hist_z_ema5'], 1, 0)
    localData['HISTPositionSignal'] = localData['HISTCrossSignal'].diff()
    localData.loc[localData['HISTPositionSignal'] == 1, 'HISTBuySell'] = True
    localData.loc[localData['HISTPositionSignal'] == 0, 'HISTBuySell'] = None
    localData.loc[localData['HISTPositionSignal'] == -1, 'HISTBuySell'] = False
    localData['MACDCrossSignal'] = np.where(localData['hist_z'] > localData['hist_z_ema5'], 1, 0)
    localData['MACDPositionSignal'] = localData['MACDCrossSignal'].diff()
    localData.loc[localData['MACDPositionSignal'] == 1, 'MACDBuySell'] = True
    localData.loc[localData['MACDPositionSignal'] == 0, 'MACDBuySell'] = None
    localData.loc[localData['MACDPositionSignal'] == -1, 'MACDBuySell'] = False
    localData['MAMAFAMABuySell'] = localData['HISTBuySell']
    '''
    for i in range(len(localData)):
        if(localData.loc[localData.index[i], 'HISTBuySell'] == True or localData.loc[localData.index[i], 'MACDBuySell'] == True):
            localData.loc[localData.index[i], 'MAMAFAMABuySell'] == True
        elif(localData.loc[localData.index[i], 'HISTBuySell'] == False or localData.loc[localData.index[i], 'MACDBuySell'] == False):
            localData.loc[localData.index[i], 'MAMAFAMABuySell'] == False
    '''
    localData.to_csv("test.csv")
    return localData['MAMAFAMABuySell']

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

def mafa_pine_script_stdev(data, column, current_p, length):
    localData = data.copy()
    localData['avg'] = localData[column].rolling(length).mean()
    sumofsd = 0
    for i in range(length - 1):
        sum = mafa_sum(localData.loc[localData.index[current_p - i], column], -localData.loc[localData.index[current_p], 'avg'])
        sumofsd = sumofsd + sum * sum
    stdev = math.sqrt(sumofsd / length)
    return stdev

def mafa_sum(fst, snd):
    EPS = 0.0000000001
    res = fst + snd
    if mafa_isZero(res, EPS):
        res = 0
    elif mafa_isZero(res, 0.0001):
        res = 15
    return res

def mafa_isZero(val, eps):
    if (abs(val) <= eps):
        return True
    else:
        return False
