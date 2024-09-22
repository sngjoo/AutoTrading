"""
This module contains the FutureMaster class, which have general information of futures.

Classes:
    FutureMaster: Manages and processes general information of futures.
"""

import pandas as pd
import win32com.client


# A mapping Korean future names to their English equivalents.
_kr_name_to_en_name = {
    "코스피200": "KOSPI200",
    "코스닥150": "KOSDAQ150",
    "미니코스피": "MINIKOSPI",
}


class FutureMaster:
    """
    FutureMaster is a class that manages and processes general information of futures.
    This class retrieves futures of three indices (KOSPI200, KOSDAQ150, MINIKOSPI)
    and generates a dictionary of {future name: front month contract code}
    pairs for each index. (We only trade front month contracts which have the
    largest trade volume.)

    Attributes:
        connected_futures (list): A list of connected future codes to be filtered out.
        future_master (pd.DataFrame): DataFrame containing future master data with columns:
        front_month_dict (dict): A dictionary where keys are future contract names and
                                 values are the corresponding front month contracts.
    """

    def __init__(self):
        self.connected_futures = ["10100", "10600", "10500"]

        self.future_master = self._get_future_master()
        self.front_month_dict = self._generate_front_month_dict()

    def _convert_to_dataframe(self, future_data: list) -> pd.DataFrame:
        """
        Converts future data to a DataFrame applying necessary transformations.

        Args:
            future_data (list): Raw data to be converted.

        Returns:
            pd.DataFrame: DataFrame containing future master data.
        """
        future_master = pd.DataFrame(
            future_data, columns=["futureid", "fname", "listed_date", "last_trade_date"]
        )
        future_master.fname = future_master.fname.replace(
            _kr_name_to_en_name, regex=True
        )
        return future_master

    def _get_future_master(self) -> pd.DataFrame:
        """
        Retrieves and processes future master data and stores it in a DataFrame.
        Colums of the DataFrame(future master) are:
            - futureid (str): The future code.
            - fname (str): The name of the future.
            - listed_date (str): The listing date of the future.
            - last_trade_date (str): The last trade date of the future.

        Returns:
            pd.DataFrame: DataFrame containing future master data.
        """
        obj_kospi200_futcode = win32com.client.Dispatch("CpUtil.CpFutureCode")
        obj_kosdaq150_futcode = win32com.client.Dispatch("CpUtil.CpKFutureCode")
        obj_code_mgr = win32com.client.Dispatch("CpUtil.CpCodeMgr")
        obj_futmst = win32com.client.Dispatch("Dscbo1.FutureMst")

        fut_list = [
            obj_kospi200_futcode.GetData(0, i)
            for i in range(obj_kospi200_futcode.GetCount())
        ]
        fut_list += [
            obj_kosdaq150_futcode.GetData(0, i)
            for i in range(obj_kosdaq150_futcode.GetCount())
        ]
        fut_list += list(obj_code_mgr.GetMiniFutureList())

        future_data = []
        for code in fut_list:

            if code in self.connected_futures:
                continue

            obj_futmst.SetInputValue(0, code)
            obj_futmst.BlockRequest()
            # Read required data based on the defined indices from Brokerage API.
            # 0: "futureid", 2: "fname", 6: "listed_date", 9: "last_trade_date"
            future_data += [[str(obj_futmst.GetHeaderValue(i)) for i in [0, 2, 6, 9]]]

        return self._convert_to_dataframe(future_data)

    def _generate_front_month_dict(self) -> dict:
        """
        Generates a dictionary mapping future names to their front month contract code.
        
        Returns:
            dict: A dictionary where keys are future contract names and values are the
                  corresponding front month contracts.
        """
        front_month_dict = {}

        for name in _kr_name_to_en_name.values():
            contract_list = self.future_master[
                self.future_master.fname.str.contains(name)
            ]
            front_month_dict[name] = contract_list[
                contract_list.listed_date == contract_list.listed_date.min()
            ].iloc[0, 0]

        return front_month_dict
