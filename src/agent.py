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
        if shared_map:
            self.shared_map = shared_map

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
                    self._update_map(updated_map)
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

    def play_master(self, global_state):
        g_map = global_state['maps']
        states = global_state['states']
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
                        if len(entities) == 2:
                            current = entities.pop(0)
                            target = entities.pop(0)
                            # TODO: discard known relationships before start while loop
                            if g_map[current[0]]['map_id'] != g_map[target[0]]['map_id']:
                                current_map = g_map[current[0]]['map_id']
                                target_map = g_map[target[0]]['map_id']
                                target_position = target[1]
                                # Check if both agents are in the same perception
                                self._try_synchronize_map(current_map, target_map, target_position)
                                # First of all store old position
                                old_target_y = global_state['maps'][target[0]]['y']
                                old_target_x = global_state['maps'][target[0]]['x']
                                ols_map_id = global_state['maps'][target[0]]['map_id']
                                # Next update target agent
                                global_state['maps'][target[0]]['y'] = (global_state['maps'][current[0]]['y'] + current[1][0]) % 70
                                global_state['maps'][target[0]]['x'] = (global_state['maps'][current[0]]['x'] + current[1][1]) % 70
                                global_state['maps'][target[0]]['map_id'] = global_state['maps'][current[0]]['map_id']
                                # TODO: Update all maps related with target agent so all agents can see each other
                                # Substract old position the new one
                                old_target_y = old_target_y - global_state['maps'][target[0]]['y']
                                old_target_x = old_target_x - global_state['maps'][target[0]]['x']
                                # Then search agents with old map_id and substitute for new one and new position
                                for a in g_map:
                                    if g_map[a]['map_id'] == ols_map_id:
                                        global_state['maps'][a]['y'] = (global_state['maps'][a]['y'] - old_target_y) % 70
                                        global_state['maps'][a]['x'] = (global_state['maps'][a]['x'] - old_target_x) % 70
                                        global_state['maps'][a]['map_id'] = global_state['maps'][current[0]]['map_id']

    def _update_map(self, partial_map):
        void_map = np.zeros((70, 70))
        shm_m = shared_memory.SharedMemory(name=self.shared_map['map_id'])
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
        self.shared_map['y'] = (self.shared_map['y'] + y) % 70
        self.shared_map['x'] = (self.shared_map['x'] + x) % 70

    @staticmethod
    def _get_entities(perception):
        entities = list(filter(lambda th: th['type'] == 'entity', perception['things']))
        entities = list(filter(lambda th: th['x'] != 0 or th['y'] != 0, entities))

        return list(map(lambda e: (e['y'], e['x']), entities))

    @staticmethod
    def _try_synchronize_map(shared_map_id, shared_map_to_merge_id, position):
        void_map = np.zeros((70, 70))
        # Get shared memory of both maps
        shm_m_1 = shared_memory.SharedMemory(name=shared_map_id)
        map_1 = np.ndarray(void_map.shape, dtype=void_map.dtype, buffer=shm_m_1.buf)
        shm_m_2 = shared_memory.SharedMemory(name=shared_map_to_merge_id)
        map_2 = np.ndarray(void_map.shape, dtype=void_map.dtype, buffer=shm_m_2.buf)

        # roll map to merge with
        map_2 = np.roll(map_2, position[0], axis=0)
        map_2 = np.roll(map_2, position[1], axis=1)

        mask = map_2 > 0

        map_1[mask] = map_2[mask]
