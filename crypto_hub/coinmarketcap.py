import pandas as pd


def get_coinmarketcap_data():
    data = pd.read_json('https://api.coinmarketcap.com/v1/ticker/')
    data.index = data.symbol
    return data
