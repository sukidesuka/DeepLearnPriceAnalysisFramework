from database.PriceDatabase import PriceDatabase
from database.TextDatabase import TextDatabase
from LogSystem import LogSystem
from scanner.ScannerManager import ScannerManager


# 全局模塊分享
class GlobalShareModule(object):
    def __init__(self):
        self.text_db: TextDatabase = None
        self.price_db: PriceDatabase = None
        self.log: LogSystem = None
        self.scanner_manager: ScannerManager = None
