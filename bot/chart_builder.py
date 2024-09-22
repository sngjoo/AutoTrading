"""
This module provides classes for building and updating trading charts for
stocks and futures. 

It includes the following classes:
Classes:
    ChartBuilder: Abstract base class for building trading charts.
    StockChartBuilder: Concrete class for building stock trading charts.
    FutureChartBuilder: Concrete class for building future trading charts.
"""

import abc
import math
from typing import Union
import pandas as pd


class ChartBuilder(metaclass=abc.ABCMeta):
    """
    ChartBuilder is an abstract base class designed to build and manage trading charts.
    It fetches initial chart data and updates the chart in real-time based on incoming trade data.

    Attributes:
        api (BrokerageApiObjects): An instance of the BrokerageApiObjects class.
        trade_universe (dict): A dictionary of {stock or future code : name} pairs.
        chart (pd.DataFrame): A DataFrame containing the chart data.
        start_time (int): The market start time.
        end_time (int): The market end time.
    """

    def __init__(self, trade_universe: dict, api: object = None) -> None:

        self.api = api
        self.trade_universe = trade_universe
        self.chart = None

        if api is None:
            # For testing purposes
            self.start_time, self.end_time = 9000,1530
        else:
            self.start_time, self.end_time = api.get_start_and_end_time()

    def _fetch_chart(self) -> pd.DataFrame:
        """Generate initial chart from api object"""
        return pd.DataFrame()

    def _current_position(self) -> Union[str, bool]:
        """Get current position for initial chart"""
        raise NotImplementedError()

    def realtime_chart_builder(self, date: str, code: str, time: int, cur_price: float) -> None:
        """
        Updates the real-time chart with the latest trade information.

        Args:
            date (str): The date of the trade in YYYYMMDD format.
            code (str): The stock ro future code for which the chart is being updated.
            time (int): The current time in HHMMSS format.
            cur (float): The current trade price.
        """
        hhmm = time // 100

        if hhmm >= self.end_time:
            hhmm = self.end_time
        elif hhmm % 100 == 59:
            hhmm = (hhmm // 100 + 1) * 100
        else:
            hhmm += 1

        rownow = self.chart.query(f"date == '{date}' and time == {hhmm}")

        target_cols = [i for i in self.chart.columns if code[1:] in i]
        last_idx_nm = self.chart.index[-1]
        last_posi = self.chart.position.iloc[-1]

        # The first trade entered in the current minute
        if len(rownow) == 0:
            self.chart.loc[
                len(self.chart), ["date", "time", "position"] + target_cols
            ] = [date, hhmm, last_posi] + [cur_price] * 4

        # The first trade for this stock or future in the current minute,
        # although other stocks or futures have been traded
        elif len(rownow) == 1 and math.isnan(
            self.chart.loc[last_idx_nm, target_cols[0]]
        ):
            self.chart.loc[last_idx_nm, target_cols] = [cur_price] * 4

        # Update the high, low, and closing prices
        else:
            self.chart.loc[last_idx_nm, target_cols[3]] = (
                cur_price  # Update close price
            )
            if (
                self.chart.loc[last_idx_nm, target_cols[1]] < cur_price
            ):  # Update high price
                self.chart.loc[last_idx_nm, target_cols[1]] = cur_price
            if (
                self.chart.loc[last_idx_nm, target_cols[2]] > cur_price
            ):  # Update low price
                self.chart.loc[last_idx_nm, target_cols[2]] = cur_price


class StockChartBuilder(ChartBuilder):
    """
    StockChartBuilder is a subclass of ChartBuilder designed to handle the creation of stock charts.
    """

    def __init__(self, trade_universe: dict, api: object = None) -> None:

        super().__init__(trade_universe, api)
        self.chart = self._fetch_chart()

    def _fetch_chart(self) -> pd.DataFrame:
        """
        Fetches and constructs a DataFrame containing stock chart data for the trade universe.
        This method iterates over the trade universe, fetches the stock chart data
        for each stock code and constructs a DataFrame with the following columns for each stock:
        - date: The date of the data point.
        - time: The time of the data point.
        - open_{code}: The opening price of the stock.
        - high_{code}: The highest price of the stock.
        - low_{code}: The lowest price of the stock.
        - close_{code}: The closing price of the stock.
        The resulting DataFrame is indexed by 'date' and 'time'
        and includes an additional column 'position' representing the current position.

        Returns:
            pd.DataFrame: A DataFrame containing the concatenated stock chart data
                          for all stocks in the trade universe.
        """
        if self.api is None:
            return pd.DataFrame()

        data = []
        for code in self.trade_universe.keys():

            obj_chart = self.api.fetch_chart_stock(
                code, 381, "m"
            )  # Max 381 tick a day
            row_list = [
                [obj_chart.GetDataValue(j, i) for j in range(6)]
                for i in range(obj_chart.GetHeaderValue(3))[::-1]
            ]

            df = pd.DataFrame(
                row_list,
                columns=[
                    "date",
                    "time",
                    f"open_{code}",
                    f"high_{code}",
                    f"low_{code}",
                    f"close_{code}",
                ],
            )

            df.set_index(["date", "time"], inplace=True)
            data.append(df)

        data = pd.concat(data, axis=1).reset_index()
        data["position"] = self._current_position()

        return data

    def _current_position(self) -> Union[str, bool]:
        """
        Determines the current stock position from the account balance.
        This method fetches the stock account balance using the `api_obj` and iterates
        through the account data to find if any stock in the `trade_universe` is currently held.
        If a match is found, it returns the stock code. If no match is found, it returns False.

        Returns:
            str: The stock code if a position is found.
            bool: False if no position is found.
        """
        obj_acc = self.api.fetch_stock_account_balance()

        for i in range(obj_acc.GetHeaderValue(7)):
            for stock_code in self.trade_universe.keys():
                if obj_acc.GetDataValue(12, i) == "A" + stock_code:
                    return stock_code
        return False


class FutureChartBuilder(ChartBuilder):
    """
    FutureChartBuilder is a subclass of ChartBuilder designed to
    handle the creation of future charts.

    Attributes:
        trade_universe (dict): A dictionary of {future code : name} pairs.
        start_time (int): The start time adjusted by subtracting 15.
                          (Future market opens 15 minutes earlier than stock market)
        end_time (int): The end time adjusted by adding 15.
                        (Future market closes 15 minutes later than stock market)
    """

    def __init__(self, trade_universe: dict, api: object = None) -> None:

        super().__init__(trade_universe, api)

        self.start_time = self.start_time - 15
        self.end_time = self.end_time + 15

    def _fetch_chart(self) -> pd.DataFrame:
        """
        Fetches and constructs a DataFrame containing future chart data for the trade universe.
        This method iterates over the trade universe, fetches the future chart data
        for each future code and constructs a DataFrame with the following columns for each future:
        - date: The date of the data point.
        - time: The time of the data point.
        - open_{code}: The opening price of the future.
        - high_{code}: The highest price of the future.
        - low_{code}: The lowest price of the future.
        - close_{code}: The closing price of the future.
        The resulting DataFrame is indexed by 'date' and 'time',
        and includes an additional column 'position' representing the current position.

        Returns:
            pd.DataFrame: A DataFrame containing the concatenated future chart data
            for all futures in the trade universe.
        """
        if self.api is None:
            return pd.DataFrame()

        data = []
        for code in self.trade_universe.keys():

            obj_chart = self.api.fetch_chart_future(
                code, 411, "m"
            )  # Max 411 tick a day
            row_list = [
                [obj_chart.GetDataValue(j, i) for j in range(6)]
                for i in range(obj_chart.GetHeaderValue(3))[::-1]
            ]

            df = pd.DataFrame(
                row_list,
                columns=[
                    "date",
                    "time",
                    f"open_{code}",
                    f"high_{code}",
                    f"low_{code}",
                    f"close_{code}",
                ],
            )

            df.set_index(["date", "time"], inplace=True)
            data.append(df)

        data = pd.concat(data, axis=1).reset_index()
        data["position"] = self._current_position()

        return data

    def _current_position(self) -> Union[str, bool]:
        """
        Determines the current future position from the account balance.
        This method fetches the future account balance using the `api_obj` and iterates
        through the account data to find if any future in the `trade_universe` is currently held.
        If a match is found, it returns the future code. If no match is found, it returns False.

        Returns:
            str: The future code if a position is found.
            bool: False if no position is found.
        """
        obj_acc = self.api.fetch_future_account_balance()

        for i in range(obj_acc.GetHeaderValue(2)):
            for future_code in self.trade_universe.keys():
                if obj_acc.GetDataValue(0, i) == future_code:
                    return future_code
        return False
