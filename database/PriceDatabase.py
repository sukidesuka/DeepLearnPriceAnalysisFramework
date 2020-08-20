from database.Database import Database
import pandas as pd
import numpy as np
import typing

def dateStr2Struct():
    pass


class PriceDatabase(Database):
    def __init__(self, path):
        """
        此數據庫僅適用於價格信息的存儲！\n
        日期不可重複\n
        """
        Database.__init__(self)
        # 從path讀取csv文件
        try:
            self.path = path
            self.data = pd.read_csv(path)
            # 將csv文件按照日期降序排列
            self.data = self.data.sort_values(by=['date_y', 'date_m', 'date_d'])
            self.data = self.data.reset_index()
        except FileNotFoundError:
            self.data = pd.DataFrame(columns=['date_y', 'date_m', 'date_d'])

    def insert(self, date: str, name: str, item: str, value, save_to_file=True):
        """
        將一個新的商品數據插入數據庫\n
        日期 商品名 數據項目名 值\n
        在數據庫内，列名為 商品名_數據項目名\n
        如果要頻繁寫入，請將save_to_file關掉，並寫完後手動調用save_to_file寫入磁盤\n
        """
        self.lock.acquire()

        col = "{}_{}".format(name, item)
        date_y, date_m, date_d = [int(i) for i in date.split('-')]
        # 日期不存在先插一條全nan的行
        if self.data.loc[(self.data['date_y'] == date_y) &
                         (self.data['date_m'] == date_m) &
                         (self.data['date_d'] == date_d), :].empty:
            new_row = pd.DataFrame(np.full((1, len(self.data.columns)), np.nan), columns=self.data.columns)
            new_row.loc[:, ['date_y', 'date_m', 'date_d']] = [date_y, date_m, date_d]
            self.data = self.data.append(new_row)
        # 列名不存在列則插一條全nan的列
        if col not in self.data.columns:
            self.data[col] = np.nan
        # 寫入值
        self.data.loc[(self.data['date_y'] == date_y) &
                      (self.data['date_m'] == date_m) &
                      (self.data['date_d'] == date_d), col] = value
        # 將新的數據寫到本地
        if save_to_file:
            self.data.to_csv(self.path, index=False, encoding='utf-8')

        self.lock.release()

    def get_df(self):
        """
        獲取數據庫的原始DataFrame
        """
        return self.data

    def get_value(self, date: str, name: str, item: str):
        """
        精準獲取數據庫的某個值
        """
        self.lock.acquire()
        col = "{}_{}".format(name, item)
        date_y, date_m, date_d = [int(i) for i in date.split('-')]
        res = self.data.loc[(self.data['date_y'] == date_y) &
                            (self.data['date_m'] == date_m) &
                            (self.data['date_d'] == date_d), col].values

        self.lock.release()
        if len(res) == 0:
            return None
        else:
            return res[0]

    def save_to_file(self) -> None:
        """
        手動將當前數據庫的DataFrame寫入本地\n
        適合與insert的save_to_file=False聯合使用\n
        """
        self.lock.acquire()
        self.data.to_csv(self.path, index=False, encoding='utf-8')
        self.lock.release()