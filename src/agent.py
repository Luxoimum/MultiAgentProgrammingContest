from modules.server_communication import ServerCommunication
from modules.buffer_manager import BufferManager
from modules.common_structures import CommonStructures
from modules.exploration import Exploration
from multiprocessing import shared_memory
import numpy as np
import json
import time


class Agent:
    def __init__(self, agent_id, name, state=None, agent_map=None):
        self.agent_id = agent_id
        self.name = name
        self.state = state
        self.map = agent_map
        if agent_map:
            self.agent_map = agent_map
        self.buffer = BufferManager()
        self.structures = CommonStructures(self.name)
        self.server = ServerCommunication(self.buffer, self.structures.CONF, self.structures.AUTH)
        self.exploration = Exploration()

    def connect(self):
        self.server.connect()
        self.server.receive()

    def step(self, debug=False):
        response = self.server.receive(debug)
        response = json.loads(response or '{"type": "None"}')
        step_id = None
        perception = None
        if response['type'] == 'request-action':
            # Catch perception from the response object
            step_id = response['content']['id']
            perception = response['content']['percept']

            # Update state of the agent
            self.state['entities'] = self._get_entities(perception)
            self.state['dispenser'] = self._get_dispensers(perception)

            updated_map = self.exploration.get_map(perception)
            self._update_map(updated_map)

        return step_id, perception

    def action(self, action_id, perform_action):
        action = self.structures.get_action_structure(action_id, 'move', [perform_action])
        return self.server.send(action)

    def _update_map(self, partial_map):
        map_shape = self.map['map'].shape
        padding = map_shape[0]-len(partial_map)

        y = self.map['y'] - 5
        x = self.map['x'] - 5
        map_padded = np.pad(partial_map, ((0, padding), (0, padding)), mode='constant')
        map_padded = np.roll(map_padded, y, axis=0)
        map_padded = np.roll(map_padded, x, axis=1)

        mask = map_padded > 0

        self.map['map'][mask] = map_padded[mask]

    def _update_position(self, updated_position):
        y, x = updated_position
        self.map['y'] = (self.map['y'] + y) % 70
        self.map['x'] = (self.map['x'] + x) % 70

    @staticmethod
    def _get_entities(perception):
        entities = list(filter(lambda th: th['type'] == 'entity', perception['things']))
        entities = list(filter(lambda th: th['x'] != 0 or th['y'] != 0, entities))

        return list(map(lambda e: (e['y'], e['x']), entities))

    @staticmethod
    def _get_dispensers(perception):
        entities = list(filter(lambda th: th['type'] == 'dispenser', perception['things']))

        return list(map(lambda e: (e['y'], e['x'], e['details']), entities))

