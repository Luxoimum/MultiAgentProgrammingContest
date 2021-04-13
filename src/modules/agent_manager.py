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
        self.data_debug_agents = {}
        self.step_id = None

        map_size = (70, 70)
        for agent_id, agent in enumerate(agents_name):
            print('[MANAGER]', str(agent))
            # Create a new empty map for this agent and store pointer and position of this agent
            self.maps[agent] = {}
            self.maps[agent]['map'] = np.zeros(map_size)
            self.maps[agent]['y'] = int(map_size[0]/2)
            self.maps[agent]['x'] = int(map_size[1]/2)

            # Allocate space for agent internal states
            self.states[agent] = dict()

            # Create agent instance
            self.agents[agent] = Agent(agent_id, agent)
            self.agents[agent].connect()

    def step(self):
        for agent in self.agents:
            # Get perception
            self.step_id, self.states[agent] = self.agents[agent].step()

            if self.states[agent]['perception']['lastAction'] != 'no_action' and self.states[agent]['perception']['lastActionResult'] == 'success':
                last_action = self.states[agent]['perception']['lastActionParams'][0]
                # Update position
                self._update_position(agent, last_action)

                # Update agent map
                updated_map = self.exploration.get_map(self.states[agent]['perception'])
                self._update_map(agent, updated_map)

        # Look for possible map merges
        self.merge_maps()

        for agent in self.agents:
            last_action = None
            if self.states[agent]['perception']['lastAction'] != 'no_action':
                last_action = self.states[agent]['perception']['lastActionParams'][0]

            if not self.states[agent]['perception']['disabled']:
                action = self.exploration.get_action(self.states[agent]['perception'], last_action)
                self.agents[agent].action(self.step_id, action)

            self.step_id % 2 == 0 and agent == 'agentA15' and self.debugger(self.data_debug_agents)
        #time.sleep(0.5)

    def merge_maps(self, selected_agents=None):
        start = time.time()
        relationships = {}
        # Walk through agent states looking for entities in his perception
        for a in (selected_agents or self.states):
            if 'entities' in self.states[a] and len(self.states[a]['entities']) > 0:
                # Store potential relationships and entities associated value in a hashmap
                for e in self.states[a]['entities']:
                    relationship = 10000 + 100*abs(e[0]) + abs(e[1])
                    relationships[relationship] = [*relationships.get(relationship, []), (a, e)]

        for relationship in relationships:
            # For each relationship try to synchronize pairs of agents
            entities = relationships[relationship]
            while entities:
                current = entities.pop(0)
                for target in entities:
                    if self.maps[current[0]]['map'] is self.maps[target[0]]['map']:
                        # Both are in the same map so clean target from entities
                        entities.remove(target)
                    else:
                        # Check if both agents are in the same perception
                        current_map = self.exploration.get_map(self.states[current[0]]['perception'])
                        target_map = self.exploration.get_map(self.states[target[0]]['perception'])
                        target_position = target[1]
                        matched = self._try_synchronize_map(
                            current_map,
                            target_map,
                            target_position,
                            debug=True
                        )
                        if matched:
                            print('[MANAGER ' + current[0] + '] match with ' + target[0])
                            # First of all clean target from entities
                            entities.remove(target)

                            # Then store old position
                            old_target_y = self.maps[target[0]]['y']
                            old_target_x = self.maps[target[0]]['x']
                            old_target_map = self.maps[target[0]]['map']

                            # Next update target agent
                            self.maps[target[0]]['map'] = self.maps[current[0]]['map']
                            self.maps[target[0]]['y'] = (self.maps[current[0]]['y'] + current[1][0]) % 70
                            self.maps[target[0]]['x'] = (self.maps[current[0]]['x'] + current[1][1]) % 70

                            # And Subtract old position the new one
                            old_target_y = old_target_y - self.maps[target[0]]['y']
                            old_target_x = old_target_x - self.maps[target[0]]['x']

                            # Roll original target map in order to merge with current map
                            target_map_to_merge = np.roll(old_target_map, old_target_y, axis=0)
                            target_map_to_merge = np.roll(target_map_to_merge, old_target_x, axis=1)

                            # Ignore cells with value = 0 in order to merge only valuable data
                            mask_merge = target_map_to_merge > 0

                            self.maps[current[0]]['map'][mask_merge] = target_map_to_merge[mask_merge]

                            # Finally search agents with old map_id and substitute for new one and new position
                            for a in self.maps:
                                if self.maps[a]['map'] is old_target_map:
                                    self.maps[a]['y'] = (self.maps[a]['y'] - old_target_y) % 70
                                    self.maps[a]['x'] = (self.maps[a]['x'] - old_target_x) % 70
                                    self.maps[a]['map'] = self.maps[current[0]]['map']
        print('[MANAGER] merge_maps', time.time() - start)

    def _update_map(self, agent, partial_map):
        map_shape = self.maps[agent]['map'].shape
        padding = map_shape[0]-len(partial_map)
        map_padded = np.pad(partial_map, ((0, padding), (0, padding)), mode='constant')

        y = self.maps[agent]['y'] - 5
        x = self.maps[agent]['x'] - 5
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
    def _try_synchronize_map(current_map, target_map, target_position, debug=False):
        if np.all(current_map < 10) or np.all(target_map < 10):
            return False

        # In order to check if both maps match first subtract common matrix
        # Find the correct corner for Y value being the center of the map (35, 35)
        if target_position[0] < 0:
            from_y = 30 + target_position[0]
            to_y = 41
        else:
            from_y = 30
            to_y = 41 + target_position[0]

        # Find the correct corner for X value being the center of the map (35, 35)
        if target_position[1] < 0:
            from_x = 30 + target_position[1]
            to_x = 41
        else:
            from_x = 30
            to_x = 41 + target_position[1]

        debug and print('[DEBUG_AGENT_MASTER]', 'target_position:', target_position)
        debug and print('[DEBUG_AGENT_MASTER]', 'corners:', from_y, to_y, from_x, to_x)

        void_map = np.zeros((to_y - from_y, to_x - from_x))
        map_shape = void_map.shape
        padding = map_shape[0]-len(current_map)

        current_map_pad = np.pad(current_map, ((0, padding), (0, padding)), mode='constant')
        target_map_pad = np.pad(target_map, ((0, padding), (0, padding)), mode='constant')

        # Subtract submatrix for both maps
        target_map_pad = np.roll(target_map_pad, target_position[0], axis=0)
        target_map_pad = np.roll(target_map_pad, target_position[1], axis=1)

        debug and print('[DEBUG_AGENT_MASTER]', 'current_map_pad:', current_map_pad)
        debug and print('[DEBUG_AGENT_MASTER]', 'target_map_pad:', target_map_pad)

        # Find intersection
        sum_sub_maps = current_map_pad + target_map_pad
        debug and print('[DEBUG_AGENT_MASTER]', 'sum_sub_maps:', sum_sub_maps)
        maps_intersection = sum_sub_maps == 20

        # Check if both maps match
        is_matched = False
        mask_current_map = current_map_pad[maps_intersection]
        mask_target_map = target_map_pad[maps_intersection]

        debug and print('[DEBUG_AGENT_MASTER]', 'mask_current_map:', mask_current_map)
        debug and print('[DEBUG_AGENT_MASTER]', 'mask_target_map:', mask_target_map)

        if np.any(mask_current_map) and np.any(mask_target_map):
            if np.all(mask_current_map == mask_target_map):
                debug and print('[DEBUG_AGENT_MASTER]', 'match')
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
                plt.cla()
