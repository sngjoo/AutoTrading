"""
This module implements a real-time trading bot for stocks using a moving average breakout strategy.
It subscribes to real-time stock market data, processes the data,
and executes trades based on predefined strategies.
Classes:
    DataListener(RequestHandler): Processes real-time stock market data and executes trading.
    DataStream: Manages subscriptions to real-time stock market data streams.
"""
from datetime import datetime

from bot.brokerage_api_actions import BrokerageApiDataSteamManager as DataSteamManager
from bot.brokerage_api_actions import BrokerageApiRequestHandler as RequestHandler
from bot.brokerage_api_actions import BrokerageApiObjects
from bot.chart_builder import StockChartBuilder

from bot.trading_strategy import StockMovingAverageBreakOutStrategy as strategy


class DataListener(RequestHandler):
    """
    DataListener is a subclass of RequestHandler that processes
    real-time stock market data and executes trading strategies.
    Attributes:        
        conclude_map (dict): A dictionary mapping execution flags to their corresponding description.
        buy_sell_map (dict): A dictionary mapping buy/sell flags to their corresponding description.
    """

    def __init__(self, trade_universe: dict):
        self.api_obj = BrokerageApiObjects()
        self.chart_builder = StockChartBuilder(trade_universe, self.api_obj)
        self.today = datetime.today().strftime("%Y%m%d")

        # Data Transformation
        self.conclude_map = {"1" : "Execute", "2" : "Confirm", "3" : "Reject", "4" : "Receive"}
        self.buy_sell_map = {"1" : "Buy", "2" : "Sell"}

    def OnReceived(self):
        """
        Handles real-time data reception and processes trading logic based on the data received.
        Depending on the type of data received, it performs the following actions:
        - Updates the chart with the latest market data.
        - Executes buy or sell trades based on the trading strategy.
        - Stops trading at the end of the trading session if all stock price data are loaded.
        - Prints execution details for real-time order updates.
        """
        if self.name == "stockcur":  # Realtime Transaction - Market order execution

            code = self.client.GetHeaderValue(0)  # Stock code
            timess = self.client.GetHeaderValue(18)  # Time(hhmmss)
            cprice = self.client.GetHeaderValue(13)  # Market price
            mtype = self.client.GetHeaderValue(20)  # Market Type 1:Pre-market expected,
            #             2:Regular market time,
            #             3:Pre-market extended,
            #             4:After-hours extended,
            #             5:Post-market expected

            prior_chart = self.chart_builder.chart.copy()  # copy current chart
            self.chart_builder.realtime_chart_builder(self.today, code, timess, cprice)  # update chart

            if prior_chart.equals(self.chart_builder.chart):  # Return if chart is not updated
                return

            # Execute Trading
            position = self.chart_builder.chart.loc[self.chart_builder.chart.index[-1], "position"]
            if position == False and strategy(self.api_obj).buy_signal(
                self.chart_builder.chart, code, cprice, timess
            ):
                self.api_obj.trade_stock(code, "2")
                self.chart_builder.chart.loc[self.chart_builder.chart.index[-1], "position"] = code
            elif position == code and strategy(self.api_obj).sell_signal(
                self.chart_builder.chart, code, cprice, timess
            ):
                self.api_obj.trade_stock(code, "1")
                self.chart_builder.chart.loc[self.chart_builder.chart.index[-1], "position"] = False

            # End trading if timess >= 153000 and all stock price data are loaded
            if (
                timess >= strategy(self.api_obj).end_time * 100
                and not self.chart_builder.chart.iloc[-1].isnull().any()
            ):
                self.caller.stop()  # Unsubscribe

        elif (
            self.name == "stockexpcur"
        ):  # Realtime Transaction - Expected execution of Market order

            code = self.client.GetHeaderValue(0)  # Stock code
            timess = self.client.GetHeaderValue(1)  # Time(hhmmss)
            cprice = self.client.GetHeaderValue(2)  # Expected execution price
            mtype = self.client.GetHeaderValue(
                8
            )  # Market Type 1:Opening Single Price Auction,
            #             2:Intraday Single Price Auction,
            #             3:Closing Single Price Auction

            if mtype == ord(
                "3"
            ):  # Execute 'Closing Single Price Auction' to sell, ignore 1,2
                if position == code and strategy(self.api_obj).sell_signal(
                    self.chart_builder.chart, code, cprice, timess
                ):
                    self.api_obj.trade_stock(code, "1")
                    self.chart_builder.chart.loc[self.chart_builder.chart.index[-1], "position"] = (
                        False
                    )
                    return

        elif self.name == "conclusion":  # Real-time order execution updates

            conflag = self.client.GetHeaderValue(14)  # Execution Flag
            ordernum = self.client.GetHeaderValue(5)  # Order number
            amount = self.client.GetHeaderValue(3)  # Executed amount
            price = self.client.GetHeaderValue(4)  # price

            bs = self.client.GetHeaderValue(12)  # buy/sell
            balance = self.client.GetHeaderValue(23)  # balance after execution

            code = self.client.GetHeaderValue(9)  # stock code

            conflags = self.conclude_map.get(conflag)  # Execution Flag conversion to Korean
            bss = self.buy_sell_map.get(bs)  # buy/sell conversion to Korean

            print("[ " + bss + conflags + " # " + str(ordernum) + " ]")
            if conflag == "1":
                print(
                    "[ price : "
                    + str(price)
                    + ", amount : "
                    + str(amount)
                    + ", balance : "
                    + str(balance)
                    + " ]"
                )


class DataStream:
    """
    DataStream class subscribes to real-time stock price data for stocks in trade universe.

    Attributes:
        objcur (dict): Dictionary to store current stock data stream managers.
        objexp (dict): Dictionary to store expected stock data stream managers.
        objconclusion (DataSteamManager): Data stream manager for stock order execution data.
    """

    def __init__(self, trade_universe: dict):
        """
        subscribe real time price of stocks in trade_universe and order execution data.
        """
        self.objcur = {}
        for code in trade_universe.keys():
            self.objcur["A" + code] = DataSteamManager("stockcur", "DsCbo1.StockCur")
            self.objcur[code].set_inputs(0, "A" + code)
            self.objcur["A" + code].subscribe(self, DataListener)

        self.objexp = {}
        for code in trade_universe.keys():
            self.objexp["A" + code] = DataSteamManager(
                "stockexpcur", "DsCbo1.StockExpectCur"
            )
            self.objexp["A" + code].set_inputs(0, "A" + code)
            self.objexp["A" + code].subscribe(self, DataListener)

        self.objconclusion = DataSteamManager("conclusion", "DsCbo1.CpConclusion")
        self.objconclusion.subscribe(self, DataListener)

    def stop(self):
        """
        Stops the trading bot by unsubscribing objects.
        """
        for v in self.objcur.values():
            v.unsubscribe()

        for v in self.objexp.values():
            v.unsubscribe()
