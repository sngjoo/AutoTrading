"""
This module implements a real-time trading bot for futures using a moving average breakout strategy.
It subscribes to real-time future market data, processes the data,
and executes trades based on predefined strategies.Classes:
    DataListener(RequestHandler): Handles real-time data received from the brokerage API.
    DataStream: Manages subscriptions to real-time data streams for futures.
"""
from datetime import datetime

from bot.brokerage_api_actions import BrokerageApiDataSteamManager as DataSteamManager
from bot.brokerage_api_actions import BrokerageApiRequestHandler as RequestHandler
from bot.brokerage_api_actions import BrokerageApiObjects
from bot.chart_builder import FutureChartBuilder

from bot.trading_strategy import FutureMovingAverageBreakOutStrategy as strategy


class DataListener(RequestHandler):
    """
    DataListener is a subclass of RequestHandler that processes
    real-time stfuatureock market data and executes trading strategies.

    Attributes:
        order_status (dict): A dictionary mapping order status codes 
                               to their corresponding descriptions.
        buy_sell_map (dict):  A dictionary mapping buy/sell codes to their corresponding description
    """

    def __init__(self, trade_universe: dict):
        self.api_obj = BrokerageApiObjects()
        self.chart_builder = FutureChartBuilder(trade_universe, self.api_obj)
        self.today = datetime.today().strftime("%Y%m%d")

        # Data Transformation
        self.order_status = {
            "1": "Accept",
            "2": "Modification Confirm",
            "3": "Cancellation Confirm",
            "4": "Execute",
            "5": "Reject",
        }
        self.buy_sell_map = {"1": "Sell", "2": "Buy"}

    def OnReceived(self):
        """
        Handles real-time data reception and processes trading logic based on the data received.
        Depending on the type of data received, it performs the following actions:
        - Updates the chart with the latest market data.
        - Executes buy or sell trades based on the trading strategy.
        - Stops trading at the end of the trading session if all stock price data are loaded.
        - Prints execution details for real-time order updates.
        """
        if self.name == "futurecur":  # Realtime Transaction - Market order execution

            code = self.client.GetHeaderValue(0)   # Future code
            timess = self.client.GetHeaderValue(15)  # Time(hhmmss)
            cprice = self.client.GetHeaderValue(1) # Market price
            mtype = self.client.GetHeaderValue(28) # Market Type 30:Closing Single Price, 40:Intraday

            prior_chart = self.chart_builder.chart.copy()  # copy current chart
            self.chart_builder.realtime_chart_builder(self.today, code, timess, cprice)  # update chart

            if prior_chart.equals(self.chart_builder.chart):  # Return if chart is not updated
                return

            # Execute Trading
            position = self.chart_builder.chart.loc[self.chart_builder.chart.index[-1], "position"]
            if position == False and strategy(self.api_obj).buy_signal(
                self.chart_builder.chart, code, cprice, timess
            ):
                self.api_obj.trade_future(code, "2", "entry")
                self.chart_builder.chart.loc[self.chart_builder.chart.index[-1], "position"] = code
            elif position == code and strategy(self.api_obj).sell_signal(
                self.chart_builder.chart, code, cprice, timess
            ):
                self.api_obj.trade_future(code, "2", "clear")
                self.chart_builder.chart.loc[self.chart_builder.chart.index[-1], "position"] = False

            # End trading if timess >= 154500 and All all Future price data are loaded
            if (
                timess >= strategy(self.api_obj).end_time * 100
                and not self.chart_builder.chart.iloc[-1].isnull().any()
            ):
                self.caller.stop()  # Unsubscribe

        elif (
            self.name == "futureexp"
        ):  # Realtime Transaction - Expected execution of Market order

            code = self.client.GetHeaderValue(0)   # Future code
            timess = self.client.GetHeaderValue(1) # Time(hhmmss)
            cprice = self.client.GetHeaderValue(2) # Expected execution price
            mtype = self.client.GetHeaderValue(4) # Market Type 30:Closing Single Price, 40:Intraday

            if mtype == 30 and timess > 153500:
                if position == code and strategy(self.api_obj).sell_signal(
                    self.chart_builder.chart, code, cprice, timess
                ):
                    self.api_obj.trade_future(code, "2", "clear")
                    self.chart_builder.chart.loc[self.chart_builder.chart.index[-1], "position"] = (
                        False
                    )
                    return

        elif self.name == "Fconclusion":  # Real-time order execution updates

            amount = self.client.GetHeaderValue(3)    # Executed amount
            price = self.client.GetHeaderValue(4)     # Executed price
            ordernum = self.client.GetHeaderValue(5)  # Order number

            bs = self.client.GetHeaderValue(12)       # buy/sell
            balance = self.client.GetHeaderValue(46)  # balance after execution
            orderstatus = self.client.GetHeaderValue(44)  # order status

            orderstat = self.order_status[
                orderstatus
            ]  # order status conversion to Korean
            bss = self.buy_sell_map[bs]  # buy/sell conversion to Korean

            print("[ " + bss + orderstat + " # " + str(ordernum) + " ]")
            if orderstatus == "4":  # Executed
                print(
                    "[ price : "
                    + str(price)
                    + "), amount : "
                    + str(amount)
                    + ", balance : "
                    + str(balance)
                    + " ]"
                )


class DataStream:
    """
    DataStream class subscribes to real-time future price data for futures in trade universe.

    Attributes:
        objcur (dict): Dictionary to store current future data stream managers.
        objexp (dict): Dictionary to store expected future data stream managers.
        objconclusion (DataSteamManager): Data stream manager for future order execution data.
    """

    def __init__(self, trade_universe: dict):
        # subscribe real time price of futures in trade_universe
        self.objcur = {}
        for code in trade_universe.keys():
            self.objcur[code] = DataSteamManager("futurecur", "DsCbo1.FutureCurOnly")
            self.objcur[code].set_inputs(0, code)
            self.objcur[code].subscribe(self, DataListener)

        self.objexp = {}
        for code in trade_universe.keys():
            self.objexp[code] = DataSteamManager("futureexp", "CpSysDib.FOExpectCur")
            self.objexp[code].SetInputValue(0, code)
            self.objexp[code].SetInputValue(2, "*")
            self.objexp[code].subscribe(self, DataListener)

        self.objconclusion = DataSteamManager("Fconclusion", "Dscbo1.CpFConclusion")
        self.objconclusion.subscribe(self, DataListener)

    def stop(self):
        """
        Stops the trading bot by unsubscribing objects.
        """
        for v in self.objcur.values():
            v.unsubscribe()

        for v in self.objexp.values():
            v.unsubscribe()
