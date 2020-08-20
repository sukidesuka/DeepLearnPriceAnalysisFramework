from scanner.ScannerManager import ScriptTask
from GlobalShareModule import GlobalShareModule
import time


class InvestingCopperNewsScanner(ScriptTask):
    def __init__(self, global_share: GlobalShareModule):
        """
        銅的新聞爬蟲
        """
        ScriptTask.__init__(self)
        self.global_share = global_share

    def run(self):
        from lxml import etree

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,'
                      'application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Host': 'www.investing.com',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/86.0.4217.0 Safari/537.36 Edg/86.0.601.1',
        }

        # 一直從第一頁往後掃描到頁面302爲止，或者掃描到整頁所有新聞都是在數據庫已存在的爲止
        i = 1
        while True:
            # 發出爬取請求
            task = self.global_share.scanner_manager.ask_task('https://www.investing.com/commodities/copper-news/{}'.
                                                              format(i), headers=headers, allow_redirects=False)
            task.lock.acquire()
            # 如果遇到頁面302，則將索引重置為1
            if task.response.status_code == 302:
                i = 1
                continue
            self.global_share.log.write('COPPER NEWS page {} success'.format(i))
            html = etree.HTML(task.response.text)
            # 一般來講，每頁文章是10個
            for x in range(1, 11):
                _title = html.xpath('//*[@id="leftColumn"]/div[8]/article[{}]/div[@class="textDiv"]/a/@title'.format(x))
                _from = html.xpath(
                    '//*[@id="leftColumn"]/div[8]/article[{}]/div[@class="textDiv"]/*['
                    '@class="articleDetails"]/span[1]/text()'.format(
                        x))
                _time = html.xpath(
                    '//*[@id="leftColumn"]/div[8]/article[{}]/div[@class="textDiv"]/*['
                    '@class="articleDetails"]/span[2]/text()'.format(
                        x))
                _link = html.xpath('//*[@id="leftColumn"]/div[8]/article[{}]/div[@class="textDiv"]/a/@href'.format(x))
                _text = html.xpath('//*[@id="leftColumn"]/div[8]/article[{}]/div[@class="textDiv"]/p/text()'.format(x))
                # 檢查是不是每個獲取結果都爲空（最後一個頁面可能沒有10個）
                if len(_title) == 0 and len(_link) == 0 and len(_time) == 0 \
                        and len(_from) == 0 and len(_text) == 0:
                    break
                _title = None if len(_title) == 0 else _title[0]
                _link = None if len(_link) == 0 else _link[0]
                _time = None if len(_time) == 0 else _time[0]
                _from = None if len(_from) == 0 else _from[0]
                _text = None if len(_text) == 0 else _text[0]
                # 洗掉日期的前綴字符
                _time = _time.replace('\xa0-\xa0', '')

                # 將日期的ago和Just轉爲爬下數據的那天
                if _time.find('ago') != -1 or _time.find('Just') != -1:
                    _time = time.strftime("%Y-%m-%d", time.localtime())
                # 否則正常解析日期
                else:
                    month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    splited = _time.split(' ')
                    if month.index(splited[0]) != -1:
                        mon = month.index(splited[0]) + 1
                    else:
                        raise Exception('Month error')
                    day = splited[1].replace(',', '')
                    year = splited[2]
                    # 如果年份為負數（新聞尾部可能如此）,則將此新聞丟棄
                    if year.find('-') != -1:
                        continue
                    _time = '{}-{}-{}'.format(year, mon, day)
                # 將獲取到的内容寫入到數據庫
                self.global_share.text_db.insert(_time, 'copper', _title, _from, _text)

            i += 1

