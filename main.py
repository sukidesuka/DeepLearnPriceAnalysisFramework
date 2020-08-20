from GlobalShareModule import GlobalShareModule
from LogSystem import LogSystem
from database.PriceDatabase import PriceDatabase
from database.TextDatabase import TextDatabase
from scanner.ScannerManager import ScannerManager

from scanner.InvestingSilverNewsScanner import InvestingSilverNewsScanner
from scanner.InvestingGoldNewsScanner import InvestingGoldNewsScanner
from scanner.InvestingGoldPriceScanner import InvestingGoldPriceScanner
from scanner.InvestingSilverPriceScanner import InvestingSilverPriceScanner
from scanner.InvestingCopperNewsScanner import InvestingCopperNewsScanner
from scanner.InvestingCopperPriceScanner import InvestingCopperPriceScanner

import os


if __name__ == '__main__':
    # 全局共享模塊
    global_share = GlobalShareModule()

    # 初始日志模块
    log = LogSystem(None)

    # 初始化數據庫
    price_db = PriceDatabase('price_db.csv')
    text_db = TextDatabase('text_db.csv')

    global_share.price_db = price_db
    global_share.text_db = text_db
    global_share.log = log

    # 加载爬虫模块
    scanner_manager = ScannerManager(global_share)
    global_share.scanner_manager = scanner_manager
    scanner_manager.add_script(InvestingGoldNewsScanner)
    scanner_manager.add_script(InvestingGoldPriceScanner)
    scanner_manager.add_script(InvestingSilverNewsScanner)
    scanner_manager.add_script(InvestingSilverPriceScanner)
    scanner_manager.add_script(InvestingCopperNewsScanner)
    scanner_manager.add_script(InvestingCopperPriceScanner)

    print(os.getcwd())