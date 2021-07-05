import os, sys
import numpy as np
from agent import Agent
from modules.exploration import Exploration
import matplotlib.pyplot as plt
from matplotlib import colors
from modules.planification_system import PlannerSystem
from modules.action_calculator import ActionCalculator
from functools import reduce
import time


class AgentManager:
    def __init__(self, agents_name):
        self.maps = {}
        self.dispensers = {}
        self.taskboards = {}
        self.goals = {}
        self.states = {}
        self.agents = {}
        self.exploration = Exploration()
        self.data_debug_agents = {}
        self.step_id = None
        self.planner = PlannerSystem()
        self.action_planner = ActionCalculator()
        self.time = True

        # Build debug directories
        f = open('debug/count.txt', 'r')
        self.dir = f.read()
        f.close()
        self.path = 'debug/' + self.dir

        os.mkdir(self.path, 0o755)
        os.mkdir(self.path + '/img', 0o755)

        f = open('debug/count.txt', 'w')
        f.write(str(int(self.dir) + 1))

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
        start = time.time()
        # Get state for any agent
        for agent in self.agents:
            # Get agent perception
            self.step_id, self.states[agent] = self.agents[agent].step()

            file_name = self.path + '/' + agent
            lastActionParams = self.states[agent]['perception']['lastActionParams']
            self.write_debug(file_name, '[STEP ' + str(self.step_id) + '] ' + agent + ' lastAction: ' + self.states[agent]['perception']['lastAction'] + '\n')
            self.write_debug(file_name, '[STEP ' + str(self.step_id) + '] ' + agent + ' lastActionResult: ' + self.states[agent]['perception']['lastActionResult'] + '\n')
            self.write_debug(file_name, '[STEP ' + str(self.step_id) + '] ' + agent + ' lastActionParams: ' + (lastActionParams[0] + '\n' if lastActionParams else 'no-param\n'))

            if self.states[agent]['perception']['lastAction'] == 'move' and self.states[agent]['perception']['lastActionResult'] == 'success':
                last_action = self.states[agent]['perception']['lastActionParams'][0]
                # Update agent position
                self._update_position(agent, last_action)

                # Update agent map
                updated_map = self.exploration.get_map(self.states[agent]['perception'])
                self._update_map(agent, updated_map)

        print('[MANAGER] step ', self.step_id)
        end = time.time()
        self.time and print('[TIME] perceptions: ', end - start)
        start = end

        # Look for possible map merges
        self._merge_maps()
        end = time.time()
        self.time and print('[TIME] merge_maps: ', end - start)
        start = end

        # Create global state by the processing of the unit states and merge maps
        merged_maps = self._get_global_state()
        end = time.time()
        self.time and print('[TIME] change data structure: ', end - start)
        start = end

        # Plan strategy to get task for any agent
        self.planner.inflate(merged_maps, self.dispensers, self.taskboards, self.goals, self.states)
        tasks = self.planner.get_task()
        for t in tasks:
            file_name = self.path + '/' + t
            self.write_debug(file_name, '[STEP ' + str(self.step_id) + '] ' + t + ' task: ' + tasks[t] + '\n')

        for ids in merged_maps:
            t = []
            for a in merged_maps[ids]['agents']:
                t.append((a[0], tasks[a[0]]))
            print('[MAPAS] ', ids, t)
        print('[MAPAS RECUENTO]', len(merged_maps))

        end = time.time()
        self.time and print('[TIME] get tasks: ', end - start)
        start = end

        # Plan strategy to get actions for any task given by an agent
        self.action_planner.inflate(merged_maps, self.dispensers, self.taskboards, self.goals, self.states)
        actions = self.action_planner.get_action(tasks)
        for a in actions:
            file_name = self.path + '/' + a[0]
            self.write_debug(file_name, '[STEP ' + str(self.step_id) + '] ' + a[0] + ' action: ' + a[1] + ' ' + str(a[2]) + '\n')
            self.write_debug(file_name, '======================\n')

        # print('[ACTIONS]', actions)
        end = time.time()
        self.time and print('[TIME] get actions: ', end - start)
        start = end

        # Perform actions by sending a message to the server
        for action in actions:
            agent, perform_action, action_param = action

            if not self.states[agent]['perception']['disabled']:
                if perform_action == 'move':
                    available_params = self.exploration.get_available_cells(self.states[agent]['perception'])
                    if available_params and action_param not in available_params:
                        random_move = np.random.randint(len(available_params)) if available_params else 0
                        action_param = available_params[random_move]

                self.agents[agent].action(self.step_id, perform_action, action_param)

        self.step_id % 2 == 0 and self.debugger(self.data_debug_agents)
        end = time.time()
        self.time and print('[TIME] perform actions: ', end - start)
        #time.sleep(0.5)

    def _merge_maps(self, selected_agents=None):
        relationships = {}
        # Walk through agent states looking for entities in his perception
        for a in (selected_agents or self.states):
            if 'entities' in self.states[a] and len(self.states[a]['entities']) > 0:
                # Store potential relationships and entities associated value in a hashmap
                for e in self.states[a]['entities']:
                    relationship = 10000 + 100*abs(e[0]) + abs(e[1])
                    relationships[relationship] = [*relationships.get(relationship, []), (a, e)]

        # For each relationship try to synchronize pairs of agents
        for relationship in relationships:
            entities = relationships[relationship]
            while entities:
                current = entities.pop(0)
                for target in entities:
                    # If both entities are in the same map clean target from entities
                    if self.maps[current[0]]['map'] is self.maps[target[0]]['map'] and len(entities) == 1:
                        entities.remove(target)
                    else:
                        # Check if both agents are in the same perception
                        current_map = self.exploration.get_map(self.states[current[0]]['perception'])
                        target_map = self.exploration.get_map(self.states[target[0]]['perception'])
                        target_position = target[1]
                        matched = self._check_same_perception(
                            current_map,
                            target_map,
                            target_position
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
        if last_movement:
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
        self._debug_map(self.maps, data_debug, selected_agents, quiet)

    def _get_global_state(self, debug=False):
        map_ids = []
        merged_maps = {}
        for i, agent in enumerate(self.maps):
            # Get map id
            agent_map_id = id(self.maps[agent]['map'])

            # Check if agent map does exist
            if agent_map_id in map_ids:
                merged_maps[agent_map_id]['agents'].append((agent, self.maps[agent]['y'], self.maps[agent]['x']))
            else:
                map_ids.append(agent_map_id)
                merged_maps[agent_map_id] = {}
                merged_maps[agent_map_id]['map'] = self.maps[agent]['map']
                merged_maps[agent_map_id]['agents'] = [(agent, self.maps[agent]['y'], self.maps[agent]['x'])]

            # Get obstacles and calculate map weights for interested elements
            obstacles = np.where(self.maps[agent]['map'] == 10)
            if self.states[agent]['dispenser']:
                for dispenser in self.states[agent]['dispenser']:
                    y = (self.maps[agent]['y'] + dispenser[0]) % 70
                    x = (self.maps[agent]['x'] + dispenser[1]) % 70

                    if agent_map_id not in self.dispensers:
                        self.dispensers[agent_map_id] = {}

                    if dispenser[2] not in self.dispensers[agent_map_id]:
                        # Create empty map to store this dispenser
                        empty_map = np.full((70, 70), np.nan)

                        # Update dispenser position
                        empty_map[y, x] = 0

                        # Add new dispenser map
                        self.dispensers[agent_map_id][dispenser[2]] = empty_map
                        self.dispensers[agent_map_id][dispenser[2]] = self._cost_calc(self.dispensers[agent_map_id][dispenser[2]], obstacles)
                    else:
                        # Store dispenser in map if doesnt exist
                        if self.dispensers[agent_map_id][dispenser[2]][y, x] != 0:
                            self.dispensers[agent_map_id][dispenser[2]][y, x] = 0
                            self.dispensers[agent_map_id][dispenser[2]] = self._cost_calc(self.dispensers[agent_map_id][dispenser[2]], obstacles)
                for dispenser in self.dispensers[agent_map_id]:
                    plt.imshow(self.dispensers[agent_map_id][dispenser])
                    plt.savefig(self.path + '/img/' + str(self.step_id) + '_' + agent + '_' + dispenser + '_' + '.png')
                    plt.cla()

            if self.states[agent]['task_board']:
                for task_board in self.states[agent]['task_board']:
                    if agent_map_id not in self.taskboards:
                        self.taskboards[agent_map_id] = np.full((70, 70), np.nan)

                    # Update task_board position
                    y = (self.maps[agent]['y'] + task_board[0]) % 70
                    x = (self.maps[agent]['x'] + task_board[1]) % 70

                    if self.taskboards[agent_map_id][y, x] != 0:
                        self.taskboards[agent_map_id][y, x] = 0
                        self.taskboards[agent_map_id] = self._cost_calc(self.taskboards[agent_map_id], obstacles)
                plt.imshow(self.taskboards[agent_map_id])
                plt.savefig(self.path + '/img/' + str(self.step_id) + '_' + agent + '_taskboards_' + '.png')
                plt.cla()

            # TODO: 1 new map per goal zone
            if self.states[agent]['goal']:
                for position in self.states[agent]['goal']:
                    if agent_map_id not in self.goals:
                        self.goals[agent_map_id] = np.full((70, 70), np.nan)

                    # Update goal position
                    y = (self.maps[agent]['y'] + position[0]) % 70
                    x = (self.maps[agent]['x'] + position[1]) % 70
                    if self.goals[agent_map_id][y, x] != 0:
                        self.goals[agent_map_id][y, x] = 0

                self.goals[agent_map_id] = self._cost_calc(self.goals[agent_map_id], obstacles)
                plt.imshow(self.goals[agent_map_id])
                plt.savefig(self.path + '/img/' + str(self.step_id) + '_' + agent + '_goal_' + '.png')
                plt.cla()

        return merged_maps

    @staticmethod
    def _check_same_perception(current_map, target_map, target_position, debug=False):
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

        # Create a cannon matrix that involves both perceptions (current and target)
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
    def _debug_map(global_map, number_of_renders, selected_agents=None, quiet=True):
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

    def _cost_calc(self, empty_map, obstacles):
        # Create new map in order to the algorithm calculates the weight
        new_map = np.ndarray(shape=empty_map.shape)
        new_map[:] = empty_map[:]
        new_map[obstacles] = np.inf

        # Get the position of elements to look for the calculation
        elements = np.where(empty_map == 0)
        elements = list(zip(elements[0], elements[1]))

        w = 1
        queue = reduce(lambda a, b: a + b, [self._get_neighbours(e, w) for e in elements])
        while queue:
            y, x, w = queue.pop()
            new_map[y, x] = w

            for neighbour in self._get_neighbours([y, x], w + 1):
                if np.isnan(new_map[neighbour[0], neighbour[1]]):
                    queue.append(neighbour)

        return new_map

    @staticmethod
    def _get_neighbours(position, wieght):
        return [
            [(position[0] + 1) % 70, position[1], wieght],
            [(position[0] - 1) % 70, position[1], wieght],
            [position[0], (position[1] + 1) % 70, wieght],
            [position[0], (position[1] - 1) % 70, wieght],
        ]

    @staticmethod
    def write_debug(file_name, text):
        f = open(file_name + '.txt', 'a')
        f.write(text)
        f.close()

