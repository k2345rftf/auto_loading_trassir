import multiprocessing as mp
from time import sleep
import pandas as pd
from trassir import RemoteTrassirArchive


class Worker(mp.Process):

    def __init__(self, queue):
        mp.Process.__init__(self)
        self.queue = queue


    def run(self):
        while True:

            if self.queue.empty():
                break
            data = self.queue.get()
            # key, operations = data.items()
            for (ip, port, username, password), operations in data.items():

                trass = RemoteTrassirArchive(ip, port, username, password)
                trass.load_screenshots(operations)
        print('done')


class ProcessingVideo:

    def __init__(self, queue, count_proc=2):
        self.count_proc = count_proc
        self._process_list = []
        self.queue = queue

    def initialize_workers(self):
        for i in range(self.count_proc):
            self._process_list.append(Worker(self.queue))

    def load(self):
        self.initialize_workers()
        try:
            for proc in self._process_list:
                proc.start()
        except KeyboardInterrupt as e:
            print('Аварийное завершение работы')


if __name__=='__main__':
    df = pd.read_excel('1.xlsx')
    queue = mp.Queue()
    servers = {}
    df['start'] = pd.to_datetime(df['start'])
    df['end'] = pd.to_datetime(df['end'])

    for row in df.itertuples():
        key = (row.ip, row.port, row.username, row.password)
        value = (row.cam_name, row.start, row.end)
        if (row.ip, row.port, row.username, row.password) not in servers:
            servers[key] = []
        servers[key].append(value)

    for key, value in servers.items():
        queue.put({key: value})

    pm = ProcessingVideo(queue)
    pm.load()
