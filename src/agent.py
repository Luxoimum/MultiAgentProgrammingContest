from server_communication import ServerCommunication
from buffer_manager import BufferManager
from common_structures import CommonStructures
from exploration_module import ExplorationModule
import json
import time


class Agent:
    def __init__(self, name, queue=None):
        self.q = queue
        self.bm = BufferManager()
        self.cm = CommonStructures(name)
        self.em = ExplorationModule()
        self.sc = ServerCommunication(self.bm, self.cm.CONF, self.cm.AUTH)
        self.sc.connect()
        while True:
            response = self.bm.read_percept()
            print('[agent]')
            if response is not None:
                response = json.loads(response)
                print(json.dumps(response, indent=2))
                print('=======================')
                if response['type'] == 'request-action':
                    request_action_id = response['content']['id']
                    percept = response['content']['percept']
                    if 'obstacle' in json.dumps(percept):
                        self.em.update_map(obstacles=percept['terrain']['obstacle'])
                    print(self.em.get_action())
                    action = self.cm.action(request_action_id, 'move', [self.em.get_action()])
                    self.sc.send(action)
            else:
                print('response is None')
            time.sleep(3.5)
            self.sc.pol()

