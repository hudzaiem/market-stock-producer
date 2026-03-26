import pandas as pd 
import pathlib


def get_stock_list():
    # You can download it from idx
    stock_list = pd.read_excel(pathlib.Path(__file__).parent.parent.parent / 'seeds/stock_list.xlsx')
    return [item + '.JK' for item in stock_list['Code'].to_list()]