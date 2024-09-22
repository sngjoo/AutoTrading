"""
This module contains the unit tests for the ChartBuilder class 
in the chart_builder module.
"""
import unittest
import pandas as pd

from bot import chart_builder as cb

class ChartBuilderTest(unittest.TestCase):
    """
    Unit tests for the ChartBuilder class.
    """
    def _generate_test_data(self) -> tuple:
        # Create a mock ChartBuilder object
        chart_builder = cb.ChartBuilder({'AAPL':'apple'})

        # Initialize the chart DataFrame with some test data
        stock_symbol = 'AAPL'
        today = '20230101'
        chart_builder.chart = pd.DataFrame({
            'date': [today, today],
            'time': [930, 931],
            f"open_{stock_symbol}": [150, 151],
            f"high_{stock_symbol}": [152, 153],
            f"low_{stock_symbol}": [149, 150],
            f"close_{stock_symbol}": [151, 152],
            'position': [False, False],
        })

        # Set end_time for the test
        chart_builder.end_time = 153000

        return chart_builder, today, stock_symbol

    def test_realtime_chart_builder_new_minute(self):
        """
        Test updating the chart with a new minute.
        """
        chart_builder, today, stock_symbol = self._generate_test_data()
        chart_builder.realtime_chart_builder(today, stock_symbol, 93100, 153.0)

        # Check if a new row is added
        self.assertEqual(len(chart_builder.chart), 3)
        self.assertEqual(chart_builder.chart.iloc[-1]['time'], 932.0)
        self.assertEqual(chart_builder.chart.iloc[-1][f"open_{stock_symbol}"], 153.0)

    def test_realtime_chart_builder_existing_minute(self):
        """
        Test updating the chart within the same minute
        """
        chart_builder, today, stock_symbol = self._generate_test_data()
        chart_builder.realtime_chart_builder(today, stock_symbol, 93059, 154.0)

        print(chart_builder.chart)

        # Check if the existing row is updated
        self.assertEqual(len(chart_builder.chart), 2)
        self.assertEqual(chart_builder.chart.iloc[-1][f"close_{stock_symbol}"], 154.0)

if __name__ == '__main__':
    unittest.main()
