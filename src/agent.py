from modules.server_communication import ServerCommunication
from modules.buffer_manager import BufferManager
from modules.common_structures import CommonStructures
from modules.exploration import Exploration
from multiprocessing import shared_memory
import numpy as np
import json


class Agent:
    def __init__(self, agent_id, name, state=None, shared_map=None):
        self.agent_id = agent_id
        self.name = name
        self.state = state
        self.shared_map_id = shared_map['map_id']
        self.shared_map = shared_map
        self.number_of_renders = 0

    def play_slave(self):
        buffer = BufferManager()
        structures = CommonStructures(self.name)
        exploration = Exploration()
        server = ServerCommunication(buffer, structures.CONF, structures.AUTH)
        server.connect()
        action_selected = None
        while True:
            response = json.loads(buffer.read_percept() or '{"type": "None"}')
            #print(json.dumps(response, indent=2))
            if response['type'] == 'request-action':
                request_action_id = response['content']['id']
                perception = response['content']['percept']
                self.state['entities'] = self._get_entities(perception)

                updated_map = exploration.get_map(perception)
                if len(updated_map) > 0:
                    self.state['perception'] = updated_map
                    self._update_map(self.shared_map_id, updated_map)
                    action_selected = exploration.get_action()
                    movements_options = {
                        'n': (-1, 0),
                        's': (1, 0),
                        'w': (0, -1),
                        'e': (0, 1),
                    }
                    self._update_position(movements_options[action_selected])

                action = structures.get_action_structure(request_action_id, 'move', [action_selected])
                server.send(action)

            server.pol()

    def play_master(self):
        pass

    def _update_map(self, shared_map_id, partial_map):
        void_map = np.zeros((70, 70))
        shm_m = shared_memory.SharedMemory(name=shared_map_id)
        global_map = np.ndarray(void_map.shape, dtype=void_map.dtype, buffer=shm_m.buf)
        map_shape = global_map.shape
        padding = map_shape[0]-len(partial_map)

        y = self.shared_map['y'] - 5
        x = self.shared_map['x'] - 5
        map_padded = np.pad(partial_map, ((0, padding), (0, padding)), mode='constant')
        map_padded = np.roll(map_padded, y, axis=0)
        map_padded = np.roll(map_padded, x, axis=1)

        mask = map_padded > 0

        global_map[mask] = map_padded[mask]

    def _update_position(self, updated_position):
        y, x = updated_position
        self.shared_map['y'] += y
        self.shared_map['x'] += x

    @staticmethod
    def _get_entities(perception):
        entities = list(filter(lambda th: th['type'] == 'entity', perception['things']))
        entities = list(filter(lambda th: th['x'] != 0 or th['y'] != 0, entities))

        return list(map(lambda e: (e['y'], e['x']), entities))
