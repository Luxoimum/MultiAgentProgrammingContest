import numpy as np
from agent import Agent
from modules.exploration import Exploration
import time
import matplotlib.pyplot as plt
from matplotlib import colors


class AgentManager:
    def __init__(self, agents_name):
        self.maps = {}
        self.states = {}
        self.agents = {}
        self.exploration = Exploration()
        self.data_debug_agens = {}

        map_size = (70, 70)
        for agent_id, agent in enumerate(agents_name):
            print('[AGENT MANAGER]', str(agent))
            # Create a new empty map for this agent
            void_map = np.zeros(map_size)

            # Allocate shared memory, shared memory pointer, and position of this agent
            self.maps[agent] = {}
            self.maps[agent]['map'] = void_map
            self.maps[agent]['y'] = int(map_size[0]/2)
            self.maps[agent]['x'] = int(map_size[1]/2)

            # Allocate space for agent internal states
            self.states[agent] = dict()

            # Create agent instance
            self.agents[agent] = Agent(agent_id, agent, self.states[agent], self.maps[agent])
            self.agents[agent].connect()

    def step(self):
        for agent in self.agents:
            # Get perception
            step_id, perception = self.agents[agent].step()

            print('[MANAGER ' + agent + '] step_id', step_id)
            print('[MANAGER ' + agent + '] last_action', perception['lastAction'], perception['lastActionParams'])

            last_action = None
            if perception['lastAction'] == 'move':
                last_action = perception['lastActionParams'][0]
                # Update position
                self._update_position(agent, last_action)

                # Update agent map
                updated_map = self.exploration.get_map(perception)
                self._update_map(agent, updated_map)

            action = self.exploration.get_action(perception, last_action)

            self.agents[agent].action(step_id, action)

        # Look for possible map merges
        self.merge_maps(['agentA2', 'agentA14'])
        self.debugger(self.data_debug_agens, ['agentA2', 'agentA14'])
        time.sleep(1)

    def merge_maps(self, selected_agents=None):
        g_map = self.maps
        states = self.states
        relationships = {}
        # Walk through agent states looking for entities in his perception
        for a in (selected_agents or states):
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
                if g_map[current[0]]['map'] is not g_map[target[0]]['map']:
                    # Check if both agents are in the same perception
                    current_map = g_map[current[0]]['map']
                    target_map = g_map[target[0]]['map']
                    target_position = target[1]
                    matched = self._try_synchronize_map(current_map, target_map, target_position)
                    if matched:
                        # First of all store old position
                        old_target_y = g_map[target[0]]['y']
                        old_target_x = g_map[target[0]]['x']
                        ols_map = g_map[target[0]]['map']

                        # Next update target agent
                        g_map[target[0]]['map'] = g_map[current[0]]['map']
                        g_map[target[0]]['y'] = (g_map[current[0]]['y'] + current[1][0]) % 70
                        g_map[target[0]]['x'] = (g_map[current[0]]['x'] + current[1][1]) % 70

                        # Subtract old position the new one
                        old_target_y = old_target_y - g_map[target[0]]['y']
                        old_target_x = old_target_x - g_map[target[0]]['x']

                        # Then search agents with old map_id and substitute for new one and new position
                        for a in g_map:
                            if g_map[a]['map'] is ols_map:
                                g_map[a]['y'] = (g_map[a]['y'] - old_target_y) % 70
                                g_map[a]['x'] = (g_map[a]['x'] - old_target_x) % 70
                                g_map[a]['map'] = g_map[current[0]]['map']
                    else:
                        discards.append(target)

                    # Add discarted entities if entities queue is emtpy
                    if not entities:
                        entities = [*entities, *discards]
                        if entities:
                            current = entities.pop(0)

    def _update_map(self, agent, partial_map):
        map_shape = self.maps[agent]['map'].shape
        padding = map_shape[0]-len(partial_map)

        y = self.maps[agent]['y'] - 5
        x = self.maps[agent]['x'] - 5
        map_padded = np.pad(partial_map, ((0, padding), (0, padding)), mode='constant')
        map_padded = np.roll(map_padded, y, axis=0)
        map_padded = np.roll(map_padded, x, axis=1)

        mask = map_padded > 0

        self.maps[agent]['map'][mask] = map_padded[mask]

    def _update_position(self, agent, last_movement):
        movements = {
            'n': (-1, 0),
            's': (1, 0),
            'w': (0, -1),
            'e': (0, 1),
        }
        y, x = movements[last_movement]
        self.maps[agent]['y'] = (self.maps[agent]['y'] + y) % 70
        self.maps[agent]['x'] = (self.maps[agent]['x'] + x) % 70

    def debugger(self, data_debug, selected_agents=None, quiet=True):
        self.debug_map(self.maps, data_debug, selected_agents, quiet)

    @staticmethod
    def _try_synchronize_map(shared_map_id, shared_map_to_merge_id, position, debug=False):
        if np.all(shared_map_id == 0) or np.all(shared_map_to_merge_id == 0):
            return False

        # Get shared memory of both maps
        map_1 = shared_map_id
        map_2 = shared_map_to_merge_id

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
    def debug_map(global_map, number_of_renders, selected_agents=None, quiet=True):
        map_ids = []
        for agent in (selected_agents or global_map):
            if id(global_map[agent]['map']) not in map_ids:
                # Store id of this map in order to dont print the same map twice or more
                map_ids.append(id(global_map[agent]['map']))

                # Copy agent shared map into our image
                not quiet and print('[DEBUG_MAP]', agent + ': ' + str(id(global_map[agent]['map'])))
                image = np.zeros((70, 70))
                image[:] = global_map[agent]['map'][:]

                # Agents with same map_id must appear at the same map
                for a in global_map:
                    if global_map[agent]['map'] is global_map[a]['map']:
                        image[global_map[a]['y'], global_map[a]['x']] = 100

                # Set params and save an image in png of the map
                cmap = colors.ListedColormap([(0.186, 0.186, 0.186),
                                              (0.91, 0.91, 0.91),
                                              (0.26, 0.26, 0.26),
                                              'blue'])
                bounds = [0, 0.9, 9, 99, 200]
                norm = colors.BoundaryNorm(bounds, cmap.N)
                plt.imshow(image,
                           interpolation='nearest',
                           cmap=cmap,
                           norm=norm)

                number_of_renders[agent] = number_of_renders.get(agent, 0) + 1
                plt.savefig('img/' + agent + '_map_' + str(number_of_renders[agent]) + '.png')

