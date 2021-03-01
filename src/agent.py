from modules.server_communication import ServerCommunication
from modules.buffer_manager import BufferManager
from modules.common_structures import CommonStructures
from modules.exploration import Exploration
from modules.agent_state import AgentState
import json
import time


class Agent:
    def __init__(self, name, queue=None):
        self.q = queue
        self.coords = {
            'n': (-1, 0),
            's': (1, 0),
            'w': (0, -1),
            'e': (0, 1),
        }
        self.state = AgentState()
        self.buffer = BufferManager()
        self.structures = CommonStructures(name)
        self.exploration = Exploration()
        self.server = ServerCommunication(self.buffer, self.structures.CONF, self.structures.AUTH)
        self.server.connect()
        self.action = None
        while True:
            response = json.loads(self.buffer.read_percept() or '{"type": "None"}')
            print('[agent]')
            #print(json.dumps(response, indent=2))
            if response['type'] == 'request-action':
                request_action_id = response['content']['id']
                perception = response['content']['percept']
                updated_map = self.exploration.get_map(perception)

                if len(updated_map) > 0:
                    self.state.update_map(updated_map)
                    action_selected = self.exploration.get_action()
                    self.state.update_position(self.coords[action_selected])
                    self.action = self.structures.get_action_structure(request_action_id, 'move', [action_selected])

                self.server.send(self.action)

            #time.sleep(3.5)
            self.server.pol()



