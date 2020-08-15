import queue
import threading
import time
import requests
from scanner import *
from typing import Callable


class HttpGetTask(object):
    def __init__(self, url, headers, allow_redirects=True, post=False, data=None):
        """
        將網路請求任務放到此処\n
        執行結果會被放到response
        """
        self.url = url
        self.headers = headers
        self.allow_redirects = allow_redirects
        self.post = post
        self.data = data
        self.lock = threading.Lock()
        self.lock.acquire()
        self.response: requests.models.Response = None

    def acquire(self):
        """
        請求此任務的鎖
        """
        self.lock.acquire()


class ScriptTask(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)


class ScannerManager(object):
    def __init__(self, global_share):
        """
        共用request池，以免高并發被封禁\n
        調用ask_task以新增任務\n
        任務完成后，會釋放掉任務裏的鎖
        """
        self.queue = queue.Queue()  # 存儲綫程鎖
        self.global_share = global_share  # 全局共享模塊

        # 開啓多一個綫程來間隔每秒釋放一個綫程鎖
        class Observer(threading.Thread):
            def __init__(self, que):
                threading.Thread.__init__(self)
                self.queue = que

            def run(self):
                while True:
                    time.sleep(1)
                    task: HttpGetTask = self.queue.get()
                    proxies = {'http': 'http://127.0.0.1:8888',
                               'https': 'http://127.0.0.1:8888'}
                    while True:
                        try:
                            if task.post:
                                task.response = requests.post(task.url, headers=task.headers, proxies=proxies,
                                                              allow_redirects=task.allow_redirects, data=task.data)
                            else:
                                task.response = requests.get(task.url, headers=task.headers, proxies=proxies,
                                                             allow_redirects=task.allow_redirects)
                            break
                        except requests.exceptions.ProxyError:
                            continue
                    task.lock.release()

        self.observer = Observer(self.queue)
        self.observer.start()
        self.script_thread_list = []  # 爬蟲脚本綫程列表

    def ask_task(self, url, headers, allow_redirects=True, post=False, data=None) -> HttpGetTask:
        """
        申請執行一個網絡任務\n
        返回一個對象，如果其鎖被釋放，説明已執行完成\n
        此時可以從對象的response得到網絡返回
        """
        task = HttpGetTask(url, headers, allow_redirects=allow_redirects, post=post, data=data)
        self.queue.put(task)
        return task

    def add_script(self, script_type):
        """
        添加一個脚本綫程對象到爬蟲脚本綫程列表，方便監控
        """
        script = script_type(self.global_share)
        self.script_thread_list.append(script)
        script.start()
