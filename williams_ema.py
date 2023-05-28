from freqtrade.strategy import IStrategy
from functools import reduce
import talib.abstract as ta

class WilliamsFractalEMA(IStrategy):
    # Buy hyperspace params:
    buy_params = {
        "fractal_value": 1,
    }

    # Sell hyperspace params:
    sell_params = {
        "fractal_value": -1,
    }

    # ROI table:
    minimal_roi = {
        "0": 0.05
    }

    # Stoploss:
    stoploss = -0.10

    def informative_pairs(self):
        return []

    def populate_indicators(self, dataframe, metadata):
        # Calculate Williams Fractal indicator:
        dataframe = calculate_fractals(dataframe)
        dataframe['ema20'] = ta.EMA(dataframe, timeperiod=20)
        dataframe['ema50'] = ta.EMA(dataframe, timeperiod=50)
        return dataframe

    def populate_buy_trend(self, dataframe, metadata):
        # Buy when bullish fractal is formed:
        conditions= []
        conditions.append(
            dataframe["fractals"].shift(2) == self.buy_params["fractal_value"]
        )

        conditions.append(
            dataframe["ema20"] >  dataframe['ema50']
        )
        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions), "buy"
            ] = 1
        return dataframe

    def populate_sell_trend(self, dataframe, metadata):
        # Sell when bearish fractal is formed:
        conditions = []
        conditions.append(
        dataframe["fractals"].shift(2) == self.sell_params["fractal_value"]
        )
        conditions.append(
            dataframe['ema50'] > dataframe['ema20']
        )
        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions), "sell"
            ] = 1
        return dataframe

def calculate_fractals(dataframe, column_name="fractals"):
    """Calculate the Williams Fractal indicator."""
    dataframe[column_name] = 0
    for i in range(2, len(dataframe) - 2):
        if (
                (dataframe["high"][i] > dataframe["high"][i - 1])
                and (dataframe["high"][i] > dataframe["high"][i - 2])
                and (dataframe["high"][i] > dataframe["high"][i + 1])
                and (dataframe["high"][i] > dataframe["high"][i + 2])
        ):
            dataframe.at[i, column_name] = -1
        elif (
                (dataframe["low"][i] < dataframe["low"][i - 1])
                and (dataframe["low"][i] < dataframe["low"][i - 2])
                and (dataframe["low"][i] < dataframe["low"][i + 1])
                and (dataframe["low"][i] < dataframe["low"][i + 2])
        ):
            dataframe.at[i, column_name] = 1
    return dataframe

