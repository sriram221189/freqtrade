"""
Supertrend strategy:
* Description: Generate a 3 supertrend indicators for 'buy' strategies & 3 supertrend indicators for 'sell' strategies
               Buys if the 3 'buy' indicators are 'up'
               Sells if the 3 'sell' indicators are 'down'
* Author: @juankysoriano (Juan Carlos Soriano)
* github: https://github.com/juankysoriano/
*** NOTE: This Supertrend strategy is just one of many possible strategies using `Supertrend` as indicator. It should on any case used at your own risk.
          It comes with at least a couple of caveats:
            1. The implementation for the `supertrend` indicator is based on the following discussion: https://github.com/freqtrade/freqtrade-strategies/issues/30 . Concretelly https://github.com/freqtrade/freqtrade-strategies/issues/30#issuecomment-853042401
            2. The implementation for `supertrend` on this strategy is not validated; meaning this that is not proven to match the results by the paper where it was originally introduced or any other trusted academic resources
"""

import logging
from numpy.lib import math
from freqtrade.strategy import IStrategy
from freqtrade.strategy import IntParameter, BooleanParameter
from pandas import DataFrame, concat
import talib.abstract as ta
import numpy as np
import freqtrade.vendor.qtpylib.indicators as qtpylib


class SupertrendBB(IStrategy):
    # Buy params, Sell params, ROI, Stoploss and Trailing Stop are values generated by 'freqtrade hyperopt --strategy Supertrend --hyperopt-loss ShortTradeDurHyperOptLoss --timerange=20210101- --timeframe=1h --spaces all'
    # It's encourage you find the values that better suites your needs and risk management strategies

    # Buy hyperspace params:
    buy_params = {
        "buy_m1": 3,
        "buy_p1": 15,
        "buy_bb_window": 14,
        "buy_bb_std": 2
    }

    # Sell hyperspace params:
    sell_params = {
        # "sell_m1": 3,
        # "sell_p1": 15
    }

    # ROI table:
    minimal_roi = {
        "0": 0.332,
        "101": 0.047,
        "215": 0.032,
        "474": 0
    }

    # Stoploss:
    stoploss = -0.297

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.069
    trailing_stop_positive_offset = 0.086
    trailing_only_offset_is_reached = True

    timeframe = '15m'

    startup_candle_count = 18

    buy_m1 = IntParameter(1, 7, default=3)
    buy_p1 = IntParameter(7, 21, default=15)
    buy_bb_window = IntParameter(5, 16, default=14)
    buy_bb_std = IntParameter(1,3, default=2)

    # sell_m1 = IntParameter(1, 7, default=3)
    # sell_p1 = IntParameter(7, 21, default=15)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        calc_dict = {}
        for multiplier in self.buy_m1.range:
            for period in self.buy_p1.range:
                calc_dict['supertrend_1_buy_'+str(multiplier)+"_"+str(period)] = self.supertrend(dataframe, multiplier, period)[
                    'STX']

        for window in self.buy_bb_window.range:
            for std in self.buy_bb_std.range:
                bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=window, stds=std)
                calc_dict['bb_lower_'+str(window)+"_"+str(std)] = bollinger['lower']
                calc_dict['bb_middle_' + str(window) + "_" + str(std)] = bollinger['mid']
                calc_dict['bb_upper_' + str(window) + "_" + str(std)] = bollinger['upper']

        # for multiplier in self.sell_m1.range:
        #     for period in self.sell_p1.range:
        #         calc_dict['supertrend_1_sell_' + str(multiplier) + "_" + str(period)] = self.supertrend(dataframe, multiplier, period)[
        #             'STX']

        supertrend_bb_data = DataFrame.from_dict(calc_dict)
        dataframe = concat([dataframe, supertrend_bb_data],axis=1)
        print(metadata)
        print(dataframe.columns)
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                    (dataframe[f'supertrend_1_buy_{self.buy_m1.value}_{self.buy_p1.value}'] == 'up') &
                    (dataframe['close'] < dataframe[f'bb_lower_{self.buy_bb_window.value}_{self.buy_bb_std.value}']) &
                    # (dataframe[f'supertrend_1_buy_{self.buy_m1.value}_{self.buy_p1.value}'].iloc[-2] == 'down') &
                    # (dataframe[f'supertrend_2_buy_{self.buy_m2.value}_{self.buy_p2.value}'] == 'up') &
                    # (dataframe[f'supertrend_3_buy_{self.buy_m3.value}_{self.buy_p3.value}'] == 'up') &  # The three indicators are 'up' for the current candle
                    (dataframe['volume'] > 0)  # There is at least some trading volume
            ),
            'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # dataframe.loc[
        #     (
        #             (dataframe[f'supertrend_1_sell_{self.sell_m1.value}_{self.sell_p1.value}'] == 'down') &
        #             # (dataframe[f'supertrend_2_sell_{self.sell_m2.value}_{self.sell_p2.value}'] == 'down') &
        #             # (dataframe[f'supertrend_3_sell_{self.sell_m3.value}_{self.sell_p3.value}'] == 'down') &  # The three indicators are 'down' for the current candle
        #             (dataframe['volume'] > 0)  # There is at least some trading volume
        #     ),
        #     'sell'] = 1
        return dataframe

    """
        Supertrend Indicator; adapted for freqtrade
        from: https://github.com/freqtrade/freqtrade-strategies/issues/30
    """

    def supertrend(self, dataframe: DataFrame, multiplier, period):
        df = dataframe.copy()

        df['TR'] = ta.TRANGE(df)
        df['ATR'] = ta.SMA(df['TR'], period)

        st = 'ST_' + str(period) + '_' + str(multiplier)
        stx = 'STX_' + str(period) + '_' + str(multiplier)

        # Compute basic upper and lower bands
        df['basic_ub'] = (df['high'] + df['low']) / 2 + multiplier * df['ATR']
        df['basic_lb'] = (df['high'] + df['low']) / 2 - multiplier * df['ATR']

        # Compute final upper and lower bands
        df['final_ub'] = 0.00
        df['final_lb'] = 0.00
        for i in range(period, len(df)):
            df['final_ub'].iat[i] = df['basic_ub'].iat[i] if df['basic_ub'].iat[i] < df['final_ub'].iat[i - 1] or \
                                                             df['close'].iat[i - 1] > df['final_ub'].iat[i - 1] else \
            df['final_ub'].iat[i - 1]
            df['final_lb'].iat[i] = df['basic_lb'].iat[i] if df['basic_lb'].iat[i] > df['final_lb'].iat[i - 1] or \
                                                             df['close'].iat[i - 1] < df['final_lb'].iat[i - 1] else \
            df['final_lb'].iat[i - 1]

        # Set the Supertrend value
        df[st] = 0.00
        for i in range(period, len(df)):
            df[st].iat[i] = df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df['close'].iat[
                i] <= df['final_ub'].iat[i] else \
                df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_ub'].iat[i - 1] and df['close'].iat[i] > \
                                         df['final_ub'].iat[i] else \
                    df['final_lb'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df['close'].iat[i] >= \
                                             df['final_lb'].iat[i] else \
                        df['final_ub'].iat[i] if df[st].iat[i - 1] == df['final_lb'].iat[i - 1] and df['close'].iat[i] < \
                                                 df['final_lb'].iat[i] else 0.00
        # Mark the trend direction up/down
        df[stx] = np.where((df[st] > 0.00), np.where((df['close'] < df[st]), 'down', 'up'), np.NaN)

        # Remove basic and final bands from the columns
        df.drop(['basic_ub', 'basic_lb', 'final_ub', 'final_lb'], inplace=True, axis=1)

        df.fillna(0, inplace=True)

        return DataFrame(index=df.index, data={
            'ST': df[st],
            'STX': df[stx]
        })

    def supertrend_vec(self, dataframe: DataFrame, period, multiplier):
        """
        data: pandas dataframe with Close price data
        period: period for moving average calculation
        multiplier: multiplier for ATR calculation
        """
        # Calculate ATR
        st = 'ST_' + str(period) + '_' + str(multiplier)
        stx = 'STX_' + str(period) + '_' + str(multiplier)
        dataframe['ATR'] = np.mean(dataframe[['high', 'low']].rolling(period).max() - dataframe[['high', 'low']].rolling(period).min(),
                              axis=1)

        # Calculate SuperTrend
        dataframe['SuperTrend'] = dataframe['close'].rolling(period).mean()
        dataframe['UpperBand'] = dataframe['SuperTrend'] + multiplier * dataframe['ATR']
        dataframe['LowerBand'] = dataframe['SuperTrend'] - multiplier * dataframe['ATR']
        dataframe[st] = np.where(
            (dataframe['close'] <= dataframe['UpperBand'].shift(1)) & (dataframe['close'] > dataframe['UpperBand']), dataframe['LowerBand'],
            np.where((dataframe['close'] >= dataframe['LowerBand'].shift(1)) & (dataframe['close'] < dataframe['LowerBand']),
                     dataframe['UpperBand'], dataframe['SuperTrend'].shift(1)))
        dataframe[stx] = np.where((dataframe[st] > 0.00), np.where((dataframe['close'] < dataframe[st]), 'down', 'up'), np.NaN)

        dataframe.fillna(0, inplace=True)

        return DataFrame(index=dataframe.index, data={
            'ST': dataframe[st],
            'STX': dataframe[stx]
        })