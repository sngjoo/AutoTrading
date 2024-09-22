"""
This script runs an ETF trading bot.

Execution:
    - Checks the connection to the brokerage API.
    - Defines a trade universe with stock(ETF) codes and their descriptions.
    - Starts the `DataStream` from `trader_stock` with the trading universe.
    - Continuously pumps waiting messages until the specified time (15:35).
    - Handles exceptions and prints error messages if any occur.
"""
import sys
from datetime import datetime
from pythoncom import PumpWaitingMessages

from bot import trader_stock
from bot import brokerage_api_actions


if __name__ == '__main__':

    if not brokerage_api_actions.BrokerageApiObjects().check_connection():
        sys.exit()

    trade_universe = {'122630' : 'KOSPI200 INDEX x2 ETF',
                      '233740' : 'KOSDAQ150 INDEX x2 ETF', 
                      '251340' : 'KOSDAQ150 INDEX INVERSE ETF'} 

    # Run
    print('[ trader_etf ] turn on')

    try:
        trader_stock.DataStream(trade_universe)

        while True:
            PumpWaitingMessages()

            # Turn off (1530+5)
            if int(datetime.now().strftime('%H%M')) > 1535:
                break

    except Exception as e:
        print('[ trader_etf ] error : ' + str(e))

    print('[ trader_etf ] turn off')
    