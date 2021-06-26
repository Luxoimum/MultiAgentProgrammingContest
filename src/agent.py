from modules.server_communication import ServerCommunication
from modules.buffer_manager import BufferManager
from modules.common_structures import CommonStructures
from modules.exploration import Exploration
import json


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
        state = {}
        if response['type'] == 'request-action':
            # Catch perception from the response object
            step_id = response['content']['id']
            perception = response['content']['percept']

            # Set state of the agent
            state['perception'] = perception
            state['entities'] = self._get_entities(perception)
            state['dispenser'] = self._get_dispensers(perception)
            state['task_board'] = self._get_taskboard(perception)
            state['goal'] = self._get_goal(perception)
            state['task'] = perception['task']
            state['tasks'] = perception['tasks']
            state['attached'] = perception['attached']

        return step_id, state

    def action(self, action_id, perform_action, param):
        action = self.structures.get_action_structure(action_id, perform_action, [param])
        return self.server.send(action)

    @staticmethod
    def _get_entities(perception):
        entities = list(filter(lambda th: th['type'] == 'entity', perception['things']))
        entities = list(filter(lambda th: th['x'] != 0 or th['y'] != 0, entities))

        return list(map(lambda e: (e['y'], e['x']), entities))

    @staticmethod
    def _get_dispensers(perception):
        dispensers = list(filter(lambda th: th['type'] == 'dispenser', perception['things']))

        return list(map(lambda e: (e['y'], e['x'], e['details']), dispensers))

    @staticmethod
    def _get_taskboard(perception):
        task_boards = list(filter(lambda th: th['type'] == 'taskboard', perception['things']))

        return list(map(lambda e: (e['y'], e['x']), task_boards))

    @staticmethod
    def _get_goal(perception):
        return list(map(lambda x: [x[1], x[0]], perception['terrain']['goal'])) if 'goal' in perception['terrain'] else []

