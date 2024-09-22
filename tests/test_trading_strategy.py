"""
This module contains the test cases for the trading_strategy module.
"""
import unittest
import pandas as pd

from parameterized import parameterized

from bot import trading_strategy


class StockMovingAverageBreakOutStrategyTest(unittest.TestCase):
    """
    Unit tests for the StockMovingAverageBreakOutStrategy class.
    """
    def setUp(self):
        # Create a mock strategy object
        self.strategy = trading_strategy.StockMovingAverageBreakOutStrategy()

        # Initialize the chart DataFrame with some test data
        self.code = "AAPL"
        self.cur_time = 123456

        self.chart = pd.DataFrame(
            {
                "date": list(range(400)),
                "time": list(range(400)),
                f"open_{self.code}": list(range(400)),
                f"high_{self.code}": [i + 1 for i in range(400)],
                f"low_{self.code}": [i - 1 for i in range(400)],
                f"close_{self.code}": list(range(400)),
            }
        )

    @parameterized.expand(
        [
            [500, True],
            [35, False],
        ]
    )
    def test_buy(self, cur_price, expected_signal):
        """
        Test if the buy signal is correctly generated when the current price is 
        greater than the maximum of the last 120 minutes.
        """
        signal = self.strategy.buy_signal(self.chart, self.code, cur_price, self.cur_time)
        self.assertEqual(signal, expected_signal)

    @parameterized.expand(
        [
            [35, True],
            [500, False],
        ]
    )
    def test_sell(self, cur_price, expected_signal):
        """
        Test if the sell signal is correctly generated when the current price is 
        lower than the minimum of the last 120 minutes.
        """
        signal = self.strategy.sell_signal(self.chart, self.code, cur_price, self.cur_time)
        self.assertEqual(signal, expected_signal)

    def test_buy_raise_key_error(self):
        """
        Test when the key does not include the code, so it needs to raise a KeyError.
        """
        chart = pd.DataFrame({"time": [1, 2, 3, 4, 5], "price": [10, 20, 30, 40, 50]})
        cur_price = 35
        with self.assertRaises(KeyError):
            self.strategy.buy_signal(chart, self.code, cur_price, self.cur_time)

if __name__ == "__main__":
    unittest.main()
