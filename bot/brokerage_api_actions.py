"""
This module provides classes and methods to interact with a brokerage API 
for trading stocks and futures. It includes functionalities for setting
parameters, handling requests, subscribing to data streams, and performing
various trading operations.

The number and types of input values for each object vary and are verbose by
necessity. Typically, the input values for an object exceed 20. Only essential
values or those differing from the default are set using SetInputValue. The
input value settings provided here are for trading as introduced in this
repository. Different settings can be provided to use other functionalities. 
For more details, refer to the brokerage firm's website(https://money2.creontra
de.com/e5/mboard/ptype_basic/HTS_Plus_Helper/DW_Basic_List_Page.aspx?boardseq=2
84&m=9505&p=8841&v=8643), but note that it is in Korean.

Classes:
    BrokerageApiRequestHandler: A handler class for managing brokerage API
                                requests and responses.
    BrokerageApiDataSteamManager: Manages the data stream from a brokerage API.
    BrokerageApiObjects: A class to interact with the brokerage API for trading
                         stocks and futures.
"""

import ctypes
import win32com.client
import win32event
from pythoncom import PumpWaitingMessages


class BrokerageApiDataSteamManager:
    """
    Manages the data stream from a brokerage API.
    """

    def __init__(self, name: str, service_id: str) -> None:
        self.name = name
        self.obj = win32com.client.Dispatch(service_id)

    def set_inputs(self, input_type: int, code: str) -> None:
        """
        Sets the input values for the brokerage API.

        Args:
            input_type (int): The type of input to set.
            code (str): The code corresponding to the input type.
        """
        self.obj.SetInputValue(input_type, code)

    def subscribe(self, caller: object, listener: object) -> None:
        """
        Subscribes a listener to the brokerage API events.

        Args:
            caller (object): The caller for callback purposes.
            listener (object): The object that will handle the events.
        """
        handler = win32com.client.WithEvents(self.obj, listener)
        handler.set_params(self.obj, self.name, caller)
        self.obj.subscribe()

    def unsubscribe(self):
        """
        Unsubscribes from the current subscription.
        """
        self.obj.unsubscribe()

class BrokerageApiRequestHandler:
    """
    A handler class for managing brokerage API requests and responses.
    """

    def set_params(self, client: str, name: str, caller: str) -> None:
        """
        Sets the parameters for the brokerage API actions.

        Args:
            client (str): Real-time Communication Object.
            name (str): The name associated with the action.
            caller (str): The caller for callback purposes.
        """
        self.client = client
        self.name = name
        self.caller = caller

    def OnReceived(self) -> None:
        """
        Handles the event when a message is received.
        Method name must be 'OnReceived' for the event handler.
        """
        print(self.name, "received")
        win32event.SetEvent(self.caller.stop_event)

    def request(self, obj: object, obj_name: str) -> None:
        """
        Sends a request to the given object.

        Args:
            obj (object): The object to send the request to.
            obj_name (str): The name of the object.

        Raises:
            RuntimeError: If an unexpected return value is encountered from
                          win32event.MsgWaitForMultipleObjects.
        """
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

        handler = win32com.client.WithEvents(obj, BrokerageApiRequestHandler)
        handler.set_params(obj, obj_name, self)

        obj.Request()
        while True:
            response_code = win32event.MsgWaitForMultipleObjects(
                [self.stop_event], 0, 1000, win32event.QS_ALLEVENTS
            )
            if response_code == 0:
                print("stop event")
                break
            elif response_code == 1:
                print("pump")
                if PumpWaitingMessages():
                    break
            elif response_code == 258:
                print("timeout")
                return
            else:
                print("exception")
                raise RuntimeError("unexpected win32wait return value")

class BrokerageApiObjects:
    """
    A class to interact with the brokerage API for trading stocks and futures.
    """

    def __init__(self):
        obj_trade = win32com.client.Dispatch("CpTrade.CpTdUtil")
        obj_trade.TradeInit(0)  # Intialize Trade
        self.account_number = obj_trade.AccountNumber[0]  # Account Number
        self.request_handler = BrokerageApiRequestHandler()

    def get_start_and_end_time(self) -> tuple:
        """
        Retrieves the market start and end times.

        Returns:
            tuple: A tuple containing the market start time and end time.
        """
        obj_code_mgr = win32com.client.Dispatch("CpUtil.CpCodeMgr")
        start_time = obj_code_mgr.GetMarketStartTime()
        end_time = obj_code_mgr.GetMarketEndTime()

        return start_time, end_time

    def check_connection(self) -> bool:
        """
        Checks the connection status to the brokerage API.
        This method performs the following checks:
        1. Verifies if the process is running with administrator privileges.
        2. Checks if the connection to the brokerage API is established.

        Returns:
            bool: True if the connection is established and the process is
                  running as administrator, False otherwise.
        """
        obj_status = win32com.client.Dispatch("CpUtil.CpCybos")

        # Check whether the process is running as administrator
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("Please run as administrator")
            return False

        # Check connection
        if obj_status.IsConnect == 0:
            print("Connection not found")
            return False

        return True

    def _order_stock(
        self, stock_code: str, buysell: str, amount: int, price: int = None
    ) -> None:
        """
        Places an order to buy or sell a stock.

        Args:
            stock_code (str)
            buysell (str): The type of order, '1' for sell and '2' for buy.
            amount (int): The number of shares to buy or sell.
            price (int, optional): The price at which to buy or sell the stock.
                                   If not provided, a market order is placed.
        """
        obj_order = win32com.client.Dispatch("CpTrade.CpTd0311")

        obj_order.SetInputValue(0, buysell)  # '1':sell '2':buy
        obj_order.SetInputValue(1, self.account_number)  # account number
        obj_order.SetInputValue(2, "01")  # account flag
        obj_order.SetInputValue(3, "A" + stock_code)  # stock code
        obj_order.SetInputValue(4, amount)  # amount

        if price:
            obj_order.SetInputValue(5, price)  # limit order
        else:
            obj_order.SetInputValue(8, "03")  # market order

        self.request_handler.request(obj_order, "order")

    def _order_future(
        self, future_code: str, buysell: str, amount: int, price: int = None
    ) -> None:
        """
        Places an order for a future contract.

        Args:
            future_code (str): The code of the future contract.
            buysell (str): The type of order, '1' for Sell and '2' for Buy.
            amount (int): The amount of the future contract to order.
            price (int, optional): The price at which to place the order. If
                                   not provided, a market order is placed.
        """
        obj_order = win32com.client.Dispatch("CpTrade.CpTd6831")

        obj_order.SetInputValue(1, self.account_number)  # account number
        obj_order.SetInputValue(2, future_code)  # future code
        obj_order.SetInputValue(3, amount)  # amount
        obj_order.SetInputValue(5, buysell)  # '1':sell '2':buy

        if price:
            obj_order.SetInputValue(6, "1")  # order type1 : limit order(default)
            obj_order.SetInputValue(4, price)
        else:
            obj_order.SetInputValue(6, "2")  # order type1 : market order

        self.request_handler.request(obj_order, "order")

    def fetch_chart_stock(self, stock_code: str, count: int, chart_type: str) -> object:
        """
        Fetches stock chart data for a given stock code.

        Args:
            stock_code (str): The stock code to fetch the chart for.
            count (int): The number of bars to fetch.
            chart_type (str): The type of chart to fetch ('D' for daily, 'm' for minute).

        Returns:
            object: The chart data object.
        """
        obj_chart = win32com.client.Dispatch("CpSysDib.StockChart")

        obj_chart.SetInputValue(0, "A" + stock_code)  # stock code
        obj_chart.SetInputValue(
            1, ord("2")
        )  # fetch type '1':by period '2':by bar count
        obj_chart.SetInputValue(4, count)  # bar count
        obj_chart.SetInputValue(
            5, [0, 1, 2, 3, 4, 5]
        )  # 0:date 1:time 2:open 3:high 4:low 5:close
        obj_chart.SetInputValue(6, ord(chart_type))  # chart type, D:daily m:minute

        self.request_handler.request(obj_chart, "chart")

        return obj_chart

    def fetch_chart_future(
        self, future_code: str, count: int, chart_type: str
    ) -> object:
        """
        Fetches the future chart data for a given future code.

        Args:
            future_code (str): The future code to fetch the chart for.
            count (int): The number of bars to fetch.
            chart_type (str): The type of chart to fetch ('D' for daily, 'm' for minute).

        Returns:
            object: The chart data object.
        """
        obj_chart = win32com.client.Dispatch("CpSysDib.FutOptChart")

        obj_chart.SetInputValue(0, future_code)  # future code
        obj_chart.SetInputValue(1, ord("2"))  # fetch type 1:by period 2:by bar count
        obj_chart.SetInputValue(4, count)  # bar count
        obj_chart.SetInputValue(
            5, [0, 1, 2, 3, 4, 5]
        )  # 0:date 1:time 2:open 3:high 4:low 5:close
        obj_chart.SetInputValue(6, ord(chart_type))  # chart type, D:daily m:minute

        self.request_handler.request(obj_chart, "f_chart")

        return obj_chart

    def fetch_buyable_amount_stock(self, stock_code: str, price: int = None) -> object:
        """
        Fetches the buyable amount of a stock.

        Args:
            stock_code (str): The stock code.
            price (int, optional): The price at which to buy the stock.
                                   If not provided, a market order is assumed.

        Returns:
            object: The object containing the buyable amount information.
        """
        obj_buy_amt = win32com.client.Dispatch("CpTrade.CpTdNew5331A")

        obj_buy_amt.SetInputValue(0, self.account_number)  # account number
        obj_buy_amt.SetInputValue(1, "01")  # account Flag
        obj_buy_amt.SetInputValue(2, "A" + stock_code)  # stock code
        obj_buy_amt.SetInputValue(
            6, ord("2")
        )  # fetch type '1':value '2':amount(quantity)

        if price:
            obj_buy_amt.SetInputValue(3, "01")  # order type : limit order(default)
            obj_buy_amt.SetInputValue(4, price)
        else:
            obj_buy_amt.SetInputValue(3, "03")  # order type : market order

        self.request_handler.request(obj_buy_amt, "buyamt")

        return obj_buy_amt

    def fetch_stock_account_balance(self) -> object:
        """
        Fetches the stock account balance.
        Stock account balance is used to find sellable stock amount and check current position.

        Returns:
            object: The object containing the account balance information.
        """
        obj_acc = win32com.client.Dispatch("CpTrade.CpTd6033")

        obj_acc.SetInputValue(0, self.account_number)  # account number
        obj_acc.SetInputValue(1, "01")  # account flag
        obj_acc.SetInputValue(2, 50)  # fetch amount(max 50, default 14)

        self.request_handler.request(obj_acc, "acc_info")

        return obj_acc

    def fetch_tradable_amount_future(
        self, future_code: str, price: int = None
    ) -> object:
        """
        Fetches the tradable amount for a given future code.

        Args:
            future_code (str): The code of the future for which tradable amount is to be fetched.
            price (int, optional): The price at which the future is to be traded.
                                   If not provided, a market order is assumed.

        Returns:
            object: The object containing the tradable amount information.
        """
        obj_buysell_amt = win32com.client.Dispatch("CpTrade.CpTd6722")

        obj_buysell_amt.SetInputValue(0, self.account_number)  # account number
        obj_buysell_amt.SetInputValue(1, future_code)  # future code

        if price:
            obj_buysell_amt.SetInputValue(2, price)  # order type : limit order(default)
            obj_buysell_amt.SetInputValue(3, "1")
        else:
            obj_buysell_amt.SetInputValue(3, "2")  # order type : market order

        self.request_handler.request(obj_buysell_amt, "f_bsamt")

        return obj_buysell_amt

    def fetch_future_account_balance(self) -> object:
        """
        Fetches the future account balance
        Future account balance is used to find clearable future amount.

        Returns:
            object: The object containing the future account balance information.
        """
        obj_acc = win32com.client.Dispatch("CpTrade.CpTd0723")
        obj_acc.SetInputValue(0, self.account_number)  # account number
        obj_acc.SetInputValue(5, 50)  # fetch amount(Max 50, default 14)

        self.request_handler.request(obj_acc, "f_acc_info")

        return obj_acc

    def trade_stock(self, stock_code: str, buysell: str) -> None:
        """
        Executes a trade for a given stock based on the specified action (buy/sell).

        Args:
            stock_code (str): The code of the stock to be traded.
            buysell (str): The action to be taken. '1' for selling the stock,
                           '2' for buying the stock.

        Raises:
            ValueError: If the buysell parameter is not '1' or '2'.

        Notes:
            - For selling, the method fetches the stock account balance
              and determines the amount of stock to sell.
            - For buying, the method fetches the buyable amount for the stock.
            - The method then places a market order for the specified action.
        """
        if buysell == "1":  # sell
            obj_sell_amt = self.fetch_stock_account_balance()
            for i in range(
                obj_sell_amt.GetHeaderValue(7)
            ):  # GetHeaderValue(7) : Number of stocks
                if obj_sell_amt.GetDataValue(12, i) == "A" + stock_code:
                    amount = obj_sell_amt.GetDataValue(15, i)  # Get the amount of stock
                    break

            self._order_stock(stock_code, buysell, amount)  # sell market order execution

        elif buysell == "2":  # buy
            obj_buy_amt = self.fetch_buyable_amount_stock(stock_code)
            amount = obj_buy_amt.GetHeaderValue(18)

            self._order_stock(stock_code, buysell, amount)  # buy market order execution

        else:
            raise ValueError(
                "Invalid buysell value. Please enter '1' for sell, '2' for buy."
            )

    def trade_future(self, future_code: str, buysell: str, trd_flag: str) -> None:
        """
        Executes a trade for a specified future contract.

        Args:
            future_code (str): The code of the future contract to be traded.
            buysell (str): Indicates whether the trade is a buy ('2') or sell ('1') action.
            trd_flag (str): Specifies the type of trade action,
                            'entry' for entering a position or 'clear' for clearing a position.
        """
        obj_buysell_amt = self.fetch_tradable_amount_future(future_code)

        if trd_flag == "entry":
            if buysell == "1":
                amount = obj_buysell_amt.GetHeaderValue(19)  # enter sell 19
            elif buysell == "2":
                amount = obj_buysell_amt.GetHeaderValue(29)  # enter buy 29
        elif trd_flag == "clear":
            if buysell == "1":
                amount = obj_buysell_amt.GetHeaderValue(18)  # clear sell 18
            elif buysell == "2":
                amount = obj_buysell_amt.GetHeaderValue(28)  # clear buy 28

        self._order_future(future_code, buysell, amount)
