import ZlemaPvtMamaFama_MarcoVersion as ZPMF
import pandas as pd
import numpy as np

def backtest_by_col(data, column):
    inital_cash = 100000
    cash = inital_cash
    stocks = 0
    buy = False
    current_price = 0
    for i in range(len(data)):
        current_price = data.loc[data.index[i], 'Close']
        if data.loc[data.index[i], column] == True:
            stock_amount, balance = buy_stock(data.loc[data.index[i], 'Close'], cash)
            #print("Buy" + str(data.index[i]))
            stocks += stock_amount
            cash += balance
        elif data.loc[data.index[i], column] == False:
            stock_amount, balance = sell_stock(data.loc[data.index[i], 'Close'], stocks)
            #print("Sell" + str(data.index[i]))
            stocks += stock_amount
            cash += balance
        else:
            continue
    if stocks != 0:
        stock_amount, balance = sell_stock(current_price, stocks)
        stocks += stock_amount
        cash += balance
    increase_rate = int((cash - inital_cash) / inital_cash * 100)
    return cash, increase_rate

def buy_stock(price, available_momeny):
    stock_amount = int(available_momeny / price)
    balance = price * stock_amount * -1
    return stock_amount, balance#+amount, -money

def sell_stock(price, current_amount):
    balance = price * current_amount
    stock_amount = current_amount * -1
    return stock_amount, balance#-amount, +money

def mutlitest():
    stock = input("Input the stock name for testing: ")
    column = None
    column = input("The Testing column: ")
    for i in range(1, 10):
        print("The current position is i = " + str(i))
        output = ZPMF.main_for_backtest(stock, i, i)
        cash, increase_rate = backtest_by_col(output, column)
        print("Cash: " + str(cash))
        print("Increase_rate: " + str(increase_rate))
        print("------------------")

def singletest():
    stock = input("Input the stock name for testing: ")
    column = None
    column = input("The Testing column: ")
    output = ZPMF.main_for_backtest(stock, 7, 7)
    #output = pd.read_csv('testing.csv')
    print(output)
    backtest_by_col(output, column)

mutlitest()
