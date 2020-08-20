from scanner.ScannerManager import ScriptTask
from GlobalShareModule import GlobalShareModule


class InvestingCopperPriceScanner(ScriptTask):
    def __init__(self, global_share: GlobalShareModule):
        """
        銅的價格爬蟲
        """
        ScriptTask.__init__(self)
        self.global_share = global_share

    def run(self):
        from lxml import etree
        import pandas as pd
        import numpy as np

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/86.0.4204.0 Safari/537.36 Edg/86.0.587.0',
            'X-Requested-With': 'XMLHttpRequest',
        }

        # 從1950年開始遍歷到結束
        i = 1950
        while True:
            data = {
                'curr_id': 8831,
                'smlID': 300012,
                'header': 'Copper Futures Historical Data',
                'st_date': '01/01/{}'.format(i),
                'end_date': '12/31/{}'.format(i),
                'interval_sec': 'Daily',
                'sort_col': 'date',
                'sort_ord': 'DESC',
                'action': 'historical_data'
            }
            url = 'https://www.investing.com/instruments/HistoricalDataAjax'
            task = self.global_share.scanner_manager.ask_task(url, headers=headers, post=True, data=data)
            task.acquire()

            self.global_share.log.write('COPPER PRICE year {} success'.format(i))

            html = etree.HTML(task.response.text)

            # 獲取表頭
            columns = html.xpath('//*[@id="curr_table"]/thead/tr/th/text()')
            # 獲取行數
            rows = html.xpath('//*[@id="curr_table"]/tbody/tr')
            # 獲取數據
            values = [html.xpath('//*[@id="curr_table"]/tbody/tr[{}]/td/text()'.format(i)) for i in range(1, len(rows) + 1)]
            # 如果沒有數據，則跳過此年（如果是有數據以後才這樣，還要先重置到1950年）
            if values[0][0] == 'No results found':
                if i > 2000:
                    i = 1950
                    continue
                else:
                    i += 1
                    continue
            # 轉爲DataFrame格式
            df = pd.DataFrame(values, columns=columns)

            # 將日期轉爲標準日期
            def parse_date(date_str):
                month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                split = date_str.split(' ')
                if month.index(split[0]) != -1:
                    mon = month.index(split[0]) + 1
                else:
                    raise Exception('Month error')
                day = split[1].replace(',', '')
                year = split[2]
                res = '{}-{}-{}'.format(year, mon, day)
                return res

            df['Date'] = df['Date'].map(parse_date)
            # 去除價格中的逗號（價格過千就會有逗號）
            df['Price'] = df['Price'].map(lambda x: float(x.replace(',', '')))
            df['Open'] = df['Open'].map(lambda x: float(x.replace(',', '')))
            df['High'] = df['High'].map(lambda x: float(x.replace(',', '')))
            df['Low'] = df['Low'].map(lambda x: float(x.replace(',', '')))
            # 將交易量轉爲正常數字
            df['Vol.'] = df['Vol.'].map(lambda x: x.replace(',', ''))
            df['Vol.'] = df['Vol.'].map(lambda x: x.replace('K', ''))
            df['Vol.'] = df['Vol.'].map(lambda x: np.nan if x == '-' else x)
            df['Vol.'] = df['Vol.'].map(lambda x: float(x) * 1000)
            # 將每次變化轉爲正常數字
            df['Change %'] = df['Change %'].map(lambda x: x.replace('%', ''))
            df['Change %'] = df['Change %'].map(lambda x: float(x) / 100)

            # 將數據塞入數據庫
            for row in df.values:
                # 表頭為 ['Date', 'Price', 'Open', 'High', 'Low', 'Vol.', 'Change %']
                self.global_share.price_db.insert(row[0], 'copper', 'price', row[1], save_to_file=False)
                self.global_share.price_db.insert(row[0], 'copper', 'open', row[2], save_to_file=False)
                self.global_share.price_db.insert(row[0], 'copper', 'high', row[3], save_to_file=False)
                self.global_share.price_db.insert(row[0], 'copper', 'low', row[4], save_to_file=False)
                self.global_share.price_db.insert(row[0], 'copper', 'vol', row[5], save_to_file=False)
                self.global_share.price_db.insert(row[0], 'copper', 'change', row[6], save_to_file=False)
            self.global_share.price_db.save_to_file()
            i += 1
