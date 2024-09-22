"""
This script runs an future trading bot.

Execution:
    - Checks the connection to the brokerage API.
    - Defines a trade universe with `FutureMaster`.
    - Starts the `DataStream` from `trader_future` with the trading universe.
    - Continuously pumps waiting messages until the specified time (15:50).
    - Handles any exceptions that occur during execution.
"""
import sys
from datetime import datetime
from pythoncom import PumpWaitingMessages

from bot import trader_future
from bot import future_master as fm
from bot import brokerage_api_actions


if __name__ == '__main__':

    if not brokerage_api_actions.BrokerageApiObjects().check_connection():
        sys.exit()

    future_master = fm.FutureMaster() # Requires for future case
    trade_universe = {future_master.front_month_dict['MINIKOSPI'] : 'MINIKOSPI',
                      future_master.front_month_dict['KOSDAQ150'] : 'KOSDAQ150',}

    # Run
    print('[ trader_future ] turn on')

    try:
        trader_future.DataStream(trade_universe)

        while True:
            PumpWaitingMessages()

            # Turn off (1545+5)
            if int(datetime.now().strftime('%H%M')) > 1550: 
                break

    except Exception as e:
        print('[ trader_future ] error : ' + str(e))

    print('[ trader_future ] turn off')
