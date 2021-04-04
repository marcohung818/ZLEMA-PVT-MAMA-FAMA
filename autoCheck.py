import ZlemaPvtMamaFama_MarcoVersion as ZPMF
import pandas as pd
import numpy as np
import os

def main():
    market = input("Enter the market(AMEX, NYSE, NASDAQ): ")
    stockList = market + "_TotalScore.csv"
    if os.path.exists(market + ".xlsx"):
        os.remove(market + ".xlsx")
    inputData = pd.read_csv(stockList, usecols=[0,1,3,5,7])
    print("The Point Distribution")
    print(inputData['Total Score'].value_counts().sort_index())
    inputData = inputData.drop(inputData[inputData['Total Score'] < min_total_score].index)
    min_total_score = input("Enter the minimum score for requirement: ")
    for i in range(len(inputData)):
        output = ZPMF.main(inputData.loc[inputData.index[i], 'Stock'])
        output.to_excel(market + ".xlsx", sheet_name = inputData.loc[inputData.index[i], 'Stock'])

main()
