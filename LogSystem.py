import time


class LogSystem(object):
    def __init__(self, path):
        """
        日志系統
        :param path:
        """
        if path is None:
            self.path = 'log.txt'
        else:
            self.path = path

    def write(self, s):
        with open(self.path, 'a') as f:
            will_write = '[{}]'.format(time.strftime("%m-%d %H:%M:%S", time.localtime())) + s + '\n'
            f.write(will_write)
        print(will_write, end='')
