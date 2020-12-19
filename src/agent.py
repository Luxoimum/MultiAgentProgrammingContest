from server_communication import ServerCommunication
from buffer_manager import BufferManager
from common_structures import CommonStructures
from multiprocessing import Process
import json
import time


class Agent:
    def __init__(self, name):
        self.bm = BufferManager()
        self.cm = CommonStructures(name)
        self.sc = ServerCommunication(self.bm, self.cm.CONF, self.cm.AUTH)
        #self.p = Process(target=self.sc.connect)
        #self.p.start()
        self.sc.connect()
        while True:
            response = self.bm.read_percept()
            print('[agent]')
            if response is not None:
                print(response)
                response = json.loads(response)
                print('=======================')
                if response['type'] == 'request-action':
                    id = response['content']['id']
                    percept = response['content']['percept']
                    action = self.cm.action(id, 'move', ['n'])
                    self.sc.send(action)
            else:
                print('response is None')
            time.sleep(3.5)
            self.sc.pol()


Agent("agentA1")

