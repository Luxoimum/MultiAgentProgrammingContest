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
        movements_options = {
            'n': (-1, 0),
            's': (1, 0),
            'w': (0, -1),
            'e': (0, 1),
        }
        buffer = BufferManager()
        structures = CommonStructures(self.name)
        exploration = Exploration()
        server = ServerCommunication(buffer, structures.CONF, structures.AUTH)
        server.connect()
        server.receive()
        server.receive()
        action_selected = None
        while True:
            response = json.loads(buffer.read_percept() or '{"type": "None"}')
            #print(json.dumps(response, indent=2))
            if response['type'] == 'request-action':
                # Catch perception from the response object
                request_action_id = response['content']['id']
                perception = response['content']['percept']

                # Update state of the agent
                self.state['entities'] = self._get_entities(perception)
                self.state['dispenser'] = self._get_dispensers(perception)
                self.state['taskboard'] = self._get_taskboards(perception)

                updated_map = exploration.get_map(perception)
                action_selected = exploration.get_action(perception)
                self._update_map(updated_map)

                if action_selected:
                    action = structures.get_action_structure(request_action_id, 'move', [action_selected])
                    if server.send(action):
                        self._update_position(movements_options[action_selected])

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

            for relationship in relationships:
                # For each relationship try to synchronize pairs of agents
                entities = relationships[relationship]
                current = entities.pop(0)
                discards = []
                while entities:
                    target = entities.pop(0)
                    # TODO: discard known relationships before start while loop
                    if g_map[current[0]]['map_id'] != g_map[target[0]]['map_id']:
                        # Check if both agents are in the same perception
                        current_map = g_map[current[0]]['map_id']
                        target_map = g_map[target[0]]['map_id']
                        target_position = target[1]
                        matched = self._try_synchronize_map(current_map, target_map, target_position)
                        if matched:
                            # First of all store old position
                            old_target_y = global_state['maps'][target[0]]['y']
                            old_target_x = global_state['maps'][target[0]]['x']
                            ols_map_id = global_state['maps'][target[0]]['map_id']
                            # Next update target agent
                            global_state['maps'][target[0]]['y'] = (global_state['maps'][current[0]]['y'] + current[1][0]) % 70
                            global_state['maps'][target[0]]['x'] = (global_state['maps'][current[0]]['x'] + current[1][1]) % 70
                            global_state['maps'][target[0]]['map_id'] = global_state['maps'][current[0]]['map_id']
                            # Substract old position the new one
                            old_target_y = old_target_y - global_state['maps'][target[0]]['y']
                            old_target_x = old_target_x - global_state['maps'][target[0]]['x']
                            # Then search agents with old map_id and substitute for new one and new position
                            for a in g_map:
                                if g_map[a]['map_id'] == ols_map_id:
                                    global_state['maps'][a]['y'] = (global_state['maps'][a]['y'] - old_target_y) % 70
                                    global_state['maps'][a]['x'] = (global_state['maps'][a]['x'] - old_target_x) % 70
                                    global_state['maps'][a]['map_id'] = global_state['maps'][current[0]]['map_id']
                        else:
                            discards.append(target)

                        # Add discarted entities if entities queue is emtpy
                        if not entities:
                            entities = [*entities, *discards]
                            if entities:
                                current = entities.pop(0)

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
    def _get_dispensers(perception):
        entities = list(filter(lambda th: th['type'] == 'dispenser', perception['things']))

        return list(map(lambda e: (e['y'], e['x'], e['details']), entities))

    @staticmethod
    def _get_taskboards(perception):
        entities = list(filter(lambda th: th['type'] == 'taskboard', perception['things']))

        return list(map(lambda e: (e['y'], e['x']), entities))

    @staticmethod
    def _try_synchronize_map(shared_map_id, shared_map_to_merge_id, position, debug=False):
        void_map = np.zeros((70, 70))

        # Get shared memory of both maps
        shm_m_1 = shared_memory.SharedMemory(name=shared_map_id)
        map_1 = np.ndarray(void_map.shape, dtype=void_map.dtype, buffer=shm_m_1.buf)
        shm_m_2 = shared_memory.SharedMemory(name=shared_map_to_merge_id)
        map_2 = np.ndarray(void_map.shape, dtype=void_map.dtype, buffer=shm_m_2.buf)

        # In order to check if both maps match first subtract common matrix
        # Find the correct corner for Y value
        if position[0] < 0:
            from_y = 30 + position[0]
            to_y = 40
        else:
            from_y = 30
            to_y = 40 + position[0]

        # Find the correct corner for X value
        if position[1] < 0:
            from_x = 30 + position[1]
            to_x = 40
        else:
            from_x = 30
            to_x = 40 + position[1]

        debug and print('[DEBUG_AGENT_MASTER]', 'position:', position)
        debug and print('[DEBUG_AGENT_MASTER]', 'corners:', from_y, to_y, from_x, to_x)
        # Subtract submatrix for both maps
        map_2 = np.roll(map_2, position[0], axis=0)
        map_2 = np.roll(map_2, position[1], axis=1)
        sub_map_1 = map_1[from_y:to_y, from_x:to_x]
        sub_map_2 = map_2[from_y:to_y, from_x:to_x]
        debug and print('[DEBUG_AGENT_MASTER]', 'sub_map_1:', sub_map_1)
        debug and print('[DEBUG_AGENT_MASTER]', 'sub_map_2:', sub_map_2)

        # Find intersection
        sum_sub_maps = sub_map_1 + sub_map_2
        maps_intersection = sum_sub_maps > 1
        debug and print('[DEBUG_AGENT_MASTER]', 'maps_intersection:', maps_intersection)

        # Check if both maps match
        is_matched = False
        mask_map_1 = sub_map_1[maps_intersection] > 1
        mask_map_2 = sub_map_2[maps_intersection] > 1
        debug and print('[DEBUG_AGENT_MASTER]', 'mask_map_1:', mask_map_1)
        debug and print('[DEBUG_AGENT_MASTER]', 'mask_map_2:', mask_map_2)

        if np.any(mask_map_1) and np.any(mask_map_2):
            unique, counts = np.unique(mask_map_1 == mask_map_2, return_counts=True)
            debug and print('[DEBUG_AGENT_MASTER]', 'unique', unique)
            debug and print('[DEBUG_AGENT_MASTER]', 'counts', counts)
            if unique[0]:
                matches = counts[0]
            else:
                matches = counts[1]
            debug and print('[DEBUG_AGENT_MASTER]', 'matches', matches)

            # If the match percentage is upper 0.8 we merge maps
            match_percent = matches / (counts[0] + counts[1])
            debug and print('[DEBUG_AGENT_MASTER]', 'match_percent', match_percent)

            if match_percent > 0.8:
                mask_merge = map_2 > 0
                map_1[mask_merge] = map_2[mask_merge]
                is_matched = True

        return is_matched

    @staticmethod
    def get_keys(key, debug=False):
        agent_id = key // 10000
        y = (key - (agent_id * 10000)) // 100
        x = key - (agent_id * 10000) - (y * 100)
        debug and print(agent_id, y, x)

