import ZlemaPvtMamaFama_MarcoVersion as ZPMF
import pandas as pd
import numpy as np

def main():
    AMEX = pd.read_csv('AMEX_TotalScore.csv', usecols=[0,1,3,5,7])
    AMEX = AMEX.drop(AMEX[AMEX['Total Score'] < 14].index)
    output = ZPMF.main('LGL')
    print(output)

main()
