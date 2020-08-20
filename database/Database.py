import threading


class Database(object):
    def __init__(self):
        # 數據庫的同步鎖
        self.lock = threading.Lock()
