"""
Module for generating trading strategies.

Classes:
    TradingStrategy: Abstract base class for generating trading strategies.
    StockMovingAverageBreakOutStrategy: Implements a moving average breakout
                                        strategy for stocks.
    FutureMovingAverageBreakOutStrategy: Implements a moving average breakout
                                         strategy for futures.
"""

import abc
import pandas as pd


class TradingStrategy(metaclass=abc.ABCMeta):
    """
    Abstract base class for trading strategies.
    """

    def buy_signal(self) -> bool:
        """Generate a buy signal."""
        raise NotImplementedError()

    def sell_signal(self) -> bool:
        """Generate a sell signal."""
        raise NotImplementedError()


class StockMovingAverageBreakOutStrategy(TradingStrategy):
    """
    StockMovingAverageBreakOutStrategy is a subclass that inherits from TradingStrategy.
    It implements a moving average breakout strategy for stocks.

    Attributes:
        start_time (int): The stock market start time.
        end_time (int): The stock market end time.
    """

    def __init__(self, api: object = None) -> None:
        if api is None:
            # For testing purposes
            self.start_time, self.end_time = 900,1530
        else:
            self.start_time, self.end_time = api.get_start_and_end_time()

    def buy_signal(
        self, chart: pd.DataFrame, code: str, cur_price: float, cur_time: int
    ) -> bool:
        """
        Determines whether a buy signal is generated based on the given conditions.

        Args:
            chart (pd.DataFrame): DataFrame containing stock chart data.
            code (str): The stock code.
            cur_price (float): The current price of the stock.
            cur_time (int): The current time in HHMMSS format.

        Returns:
            bool: True if all conditions for a buy signal are met, False otherwise.

        Conditions:
            - Market Opening Filter: Do not buy in the first 130 minutes.
            - Market Closing Filter: Do not buy in the last 10 minutes.
            - Minimum of Low Price Trend: Minimum of low price in the last 120 minutes is
              higher than the minimum of the last 360 minutes.
            - Minimum of High Price Trend: Minimum of high price in the last 75 minutes is
              higher than the minimum of the last 360 minutes.
            - Current Price: Current price is higher than the maximum of the last 120 minutes.
        """
        conditions = [
            cur_time // 100 > self.start_time + 130,
            cur_time // 100 < self.end_time - 10,
            min(chart[f"low_{code}"][-121:-1]) > min(chart[f"low_{code}"][-361:-1]),
            min(chart[f"high_{code}"][-76:-1]) > min(chart[f"high_{code}"][-361:-1]),
            cur_price > max(chart[f"high_{code}"][-121:-1]),
        ]

        print(conditions)

        if all(conditions):  # All Satisfied, then buy
            return True
        return False

    def sell_signal(self, chart, code, cur_price, cur_time) -> bool:
        """
        Determines whether a sell signal is generated based on the given conditions.

        Args:
            chart (pd.DataFrame): DataFrame containing stock chart data.
            code (str): The stock code.
            cur_price (float): The current price of the stock.
            cur_time (int): The current time in HHMMSS format.

        Returns:
            bool: True if any of the sell conditions are met, otherwise False.

        Conditions:
            - Market Closing Sell: Sell from last 10 minutes.
            - Lower than Prior 120min Min Price: Current price is lower than
              the minimum of the last 120 minutes.
            - Lower than Prior (120min Max Price)*0.96: Current price is lower than
              96% of the maximum of the last 120 minutes
        """
        conditions = [
            cur_time // 100 > self.end_time - 10,
            cur_price < min(chart[f"low_{code}"][-121:-1]),
            cur_price < max(chart[f"high_{code}"][-121:-1]) * 0.96,
        ]

        if any(conditions):  # Any Satisfied, then sell
            return True
        return False


class FutureMovingAverageBreakOutStrategy(StockMovingAverageBreakOutStrategy):
    """
    A trading strategy that extends the StockMovingAverageBreakOutStrategy to include
    futures trading. This strategy adjusts the start and end times for trading by
    subtracting 15 minutes from the start time and adding 15 minutes to the end time.

    Attributes:
        start_time (int): The future marekt start time.
        end_time (int): The future market end time.
    """

    def __init__(self , api: object = None) -> None:
        super().__init__(api)
        self.start_time = self.start_time - 15
        self.end_time = self.end_time + 15
