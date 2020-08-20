from database.Database import Database
import pandas as pd
import numpy as np


class TextDatabase(Database):
    def __init__(self, path: str):
        """
        此數據庫專用於文本類的數據存儲，日期可重複
        """
        Database.__init__(self)
        try:
            self.path = path
            self.data = pd.read_csv(path)
            # 將csv文件按照日期降序排列
            self.data.sort_values(by=['date_y', 'date_m', 'date_d'])
        except FileNotFoundError:
            self.data = pd.DataFrame(columns=['date_y', 'date_m', 'date_d', 'name', 'title', 'author', 'text'])

    def get_df(self):
        """
        獲取數據庫的原始DataFrame
        """
        return self.data

    def get_value(self, date: str, name: str):
        """
        精準獲取某個商品相關的新聞，返回的是DataFrame
        """
        date_y, date_m, date_d = [int(i) for i in date.split('-')]
        res = self.data.loc[(self.data['date_y'] == date_y) &
                            (self.data['date_m'] == date_m) &
                            (self.data['date_d'] == date_d) &
                            (self.data['name'] == name), :]
        if len(res.values) == 0:
            return None
        else:
            return res

    def insert(self, date: str, name: str, title: str, author: str, text: str):
        """
        插入新的數據，但是會過濾掉一模一樣的數據\n
        如果有一模一樣的數據，則插入失敗，返回False，否則返回True\n
        僅僅是日期不同則會更新日期并返回True
        """
        self.lock.acquire()

        date_y, date_m, date_d = [int(i) for i in date.split('-')]
        name = name.strip() if name is not None else ' '
        title = title.strip() if title is not None else ' '
        author = author.strip() if author is not None else ' '
        text = text.strip() if text is not None else ' '
        # 如果已經有一模一樣的數據，則不將其插入
        # 查找日期和數據都一樣的
        res_date = self.data.loc[(self.data['date_y'] == date_y) &
                                 (self.data['date_m'] == date_m) &
                                 (self.data['date_d'] == date_d) &
                                 (self.data['name'] == name) &
                                 (self.data['title'] == title) &
                                 (self.data['author'] == author) &
                                 (self.data['text'] == text), :].values
        # 查找數據一樣的
        res = self.data.loc[(self.data['name'] == name) &
                            (self.data['title'] == title) &
                            (self.data['author'] == author) &
                            (self.data['text'] == text), :].values
        try:
            # 如果數據相同，但是日期不同，則更新日期
            if len(res) != 0 and len(res_date) == 0:
                self.data.loc[(self.data['name'] == name) &
                              (self.data['title'] == title) &
                              (self.data['author'] == author) &
                              (self.data['text'] == text),
                              ['date_y', 'date_m', 'date_d']] = [date_y, date_m, date_d]
                return True
            # 如果數據日期皆相同，則直接返回
            elif len(res_date) != 0:
                return False
            # 數據日期都不同，直接插入新數據
            else:
                new_row = pd.DataFrame([[date_y, date_m, date_d, name, title, author, text]],
                                       columns=self.data.columns)
                self.data = self.data.append(new_row)
                self.data.to_csv(self.path, index=False, encoding='utf-8')
                return True
        finally:
            self.lock.release()
