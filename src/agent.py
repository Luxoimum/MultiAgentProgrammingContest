from modules.server_communication import ServerCommunication
from modules.buffer_manager import BufferManager
from modules.common_structures import CommonStructures
from modules.exploration import Exploration
from multiprocessing import shared_memory
import numpy as np
import json
import time


class Agent:
    def __init__(self, agent_id, name):
        self.agent_id = agent_id
        self.name = name
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
        state = {}
        if response['type'] == 'request-action':
            # Catch perception from the response object
            step_id = response['content']['id']
            perception = response['content']['percept']

            # Set state of the agent
            state['entities'] = self._get_entities(perception)
            state['dispenser'] = self._get_dispensers(perception)

        return step_id, perception, state

    def action(self, action_id, perform_action):
        action = self.structures.get_action_structure(action_id, 'move', [perform_action])
        return self.server.send(action)

    @staticmethod
    def _get_entities(perception):
        entities = list(filter(lambda th: th['type'] == 'entity', perception['things']))
        entities = list(filter(lambda th: th['x'] != 0 or th['y'] != 0, entities))

        return list(map(lambda e: (e['y'], e['x']), entities))

    @staticmethod
    def _get_dispensers(perception):
        entities = list(filter(lambda th: th['type'] == 'dispenser', perception['things']))

        return list(map(lambda e: (e['y'], e['x'], e['details']), entities))

