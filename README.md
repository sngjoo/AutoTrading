# AutoTrading
This library demonstrates how to create a trading bot with the following features:

- Communicate with brokerage APIs to receive real-time market updates
- Develop trading strategies
- Automate trading with status monitoring

In this implementation, we will use the Moving Range Breakout strategy and Daishin Securities' Creon API, which facilitates trading in the Korean stock and futures markets. You can find runnable scripts in the `examples` directory.

## Prerequisites
- The project must be run on Windows.
- The Creon API must be running.
- Python 3.6 or a higher (32-bit) is required.
- The script should be run with administrator privileges.
- For futures trading, ensure you have completed the necessary educational courses and met any other prerequisites specific to your region.

## Overview
![system architecture](https://github.com/user-attachments/assets/01e085db-a68a-4267-89d0-08fcb07344b4)

- Many actions are based on the brokerage API:
    - For the chart building module:
        - Fetching chart data
        - Fetching account balance
        - Getting market start/end time
    - For the trader module:
        - Data streaming
        - Request handling
        - Trading
    - For running:
        - Connection check
- The trading strategy is defined in a separate module, and the trader refers to it in `trading_strategy`.
- Due to the characteristics of futures, an additional module is needed to find specific contract codes (e.g., the front-month contract code in this implementation).

## Getting Started
To get started with the `AutoTrading` package, follow these steps:

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/AutoTrading.git
    cd AutoTrading
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Set up your environment variables for the Creon API.

4. Run the example script to see the trading bot in action:
    ```sh
    python examples/run_etf_trading.py
    python examples/run_future_trading.py
    ```

## Test
To run unit test,
```
pytest tests
```
