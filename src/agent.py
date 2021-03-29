from modules.server_communication import ServerCommunication
from modules.buffer_manager import BufferManager
from modules.common_structures import CommonStructures
from modules.exploration import Exploration
from multiprocessing import shared_memory
import numpy as np
import json


class Agent:
    def __init__(self, agent_id, name, state=None):
        self.agent_id = agent_id
        self.name = name
        self.global_state = state
        if name != 'master':
            self.state = state.states[name]
            self.shared_map = state.maps[name]
            print(id(state.maps[name]))

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
                    self.global_state.update_map(self.name, updated_map)
                    action_selected = exploration.get_action()
                    movements_options = {
                        'n': (-1, 0),
                        's': (1, 0),
                        'w': (0, -1),
                        'e': (0, 1),
                    }
                    self.global_state.update_position(self.name, movements_options[action_selected])

                action = structures.get_action_structure(request_action_id, 'move', [action_selected])
                server.send(action)

            server.pol()

    def play_master(self):
        g_map = self.global_state.maps
        states = self.global_state.states
        # Trying to synchronize perceptions of each agent in an unique global map
        while True:
            # Walk through agent states looking for entities in his perception
            relationships = {}
            for a in states:
                if 'entities' in states[a] and len(states[a]['entities']) > 0:
                    # Store potential relationships and entities associated value in a hashmap
                    for e in states[a]['entities']:
                        relationship = str(abs(e[0]))+str(abs(e[1]))
                        relationships[relationship] = [*relationships.get(relationship, []), (a, e)]
                        # For each relationship try to synchronize pairs of agents
                        entities = relationships[relationship]
                        if len(entities) == 2: # TODO: comprobar que los mapas tengan obstaculos
                            current = entities.pop(0)
                            target = entities.pop(0)
                            # TODO: discard known relationships before start while loop
                            if g_map[current[0]]['map_id'] != g_map[target[0]]['map_id']:
                                self.global_state.merge_maps(
                                    current=current[0],
                                    target=target[0],
                                    current_position=current[1],
                                    target_position=target[1]
                                )

    @staticmethod
    def _get_entities(perception):
        entities = list(filter(lambda th: th['type'] == 'entity', perception['things']))
        entities = list(filter(lambda th: th['x'] != 0 or th['y'] != 0, entities))

        return list(map(lambda e: (e['y'], e['x']), entities))


