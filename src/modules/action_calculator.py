import numpy as np
from modules.exploration import Exploration
from functools import reduce


class ActionCalculator:
    def __init__(self):
        self.exploration = Exploration()
        self.ensamble_map = {}
        self.maps = {}
        self.dispensers = {}
        self.agents_info = {}
        self.taskboards = {}
        self.goals = {}
        self.last_actions = {}
        self.blocks_attached = {}
        self.states = {}
        self.skip = 'skip'
        self.s_b0 = 'b0'
        self.s_b1 = 'b1'
        self.s_b2 = 'b2'
        self.s_taskboard = 'taskboard'
        self.s_goal = 'goal'
        self.asemble_structure = 'asemble_structure'

    def inflate(self, maps, dispensers, taskboards, goals, states):
        self.maps = maps
        self.dispensers = dispensers
        self.taskboards = taskboards
        self.goals = goals
        self.states = states

    def get_action(self, tasks):
        actions = []
        for map_id in self.maps:
            for agent in self.maps[map_id]['agents']:
                task = tasks[agent[0]]
                if task == self.skip:
                    actions.append(self.default_action(agent[0]))
                elif task == self.s_taskboard:
                    actions.append(self._taskboard_transition(map_id, agent))
                elif task == self.asemble_structure:
                    actions.append(self._goal_transition_taskboard(map_id, agent))
                elif task in [self.s_b0, self.s_b1, self.s_b2]:
                    if len(self.states[agent[0]]['attached']) > 0:
                        print('[ATTACHED] ' + agent[0], self.states[agent[0]]['attached'])
                        actions.append(self._goal_transition_block(map_id, agent, task))
                    else:
                        actions.append(self._block_transition(map_id, agent, task))
                else:
                    actions.append(self.default_action(agent[0]))

        return actions

    def default_action(self, agent):
        if agent in self.last_actions:
            action = self.last_actions[agent]
            param = self._get_available_movement(self.states[agent]['perception'], action[2])
            action = (*action[:2], param)
        else:
            action = (agent, 'move', self._get_available_movement(self.states[agent]['perception']))
            self.last_actions[agent] = action

        return action

    def _taskboard_transition(self, map_id, agent):
        name, y, x = agent
        if map_id in self.taskboards:
            if self.taskboards[map_id][y, x] == 0:
                task_name = None
                for task in self.states[name]['tasks']:
                    if task['reward'] == 1:
                        task_name = task['name']
                if task_name:
                    action = (name, 'accept', task_name)
                else:
                    action = (name, 'skip', None)
            else:
                param = self._get_movement_from_map(self.taskboards[map_id], agent)
                param = self._get_available_movement(self.states[name]['perception'], param)
                action = (name, 'move', param)
        else:
            action = self.default_action(name)
        return action

    def _block_transition(self, map_id, agent, block_type):
        name, y, x = agent
        if map_id in self.dispensers and block_type in self.dispensers[map_id]:
            print('[ACTIONS] dispenser: ' + block_type, agent, self.dispensers[map_id][block_type][y, x])
            blocks = np.where(self.dispensers[map_id][block_type] == 0)
            elem_blocks = list(zip(blocks[0], blocks[1]))
            for b in elem_blocks:
                print('[ACTIONS] ' + block_type + ':', b, self.dispensers[map_id][block_type][b[0], b[1]])
            if self.dispensers[map_id][block_type][y, x] <= 2:
                # Find block in perception and store its position
                destiny_position = None
                print(self.states[name]['perception']['things'])
                for thing in self.states[name]['perception']['things']:
                    if thing['details'] == block_type:
                        destiny_position = [thing['y'], thing['x']]
                print(destiny_position)
                # Check position of block in perception
                if abs(sum(destiny_position)) == 1:
                    action = self._get_block_from_dispenser(name)
                else:
                    # Calc distance with local position
                    move_selected = self._get_movement_from_perception(agent, destiny_position)
                    action = (name, 'move', move_selected)
            else:
                param = self._get_movement_from_map(self.dispensers[map_id][block_type], agent)
                param = self._get_available_movement(self.states[name]['perception'], param)
                action = (name, 'move', param)
        else:
            action = self.default_action(name)

        return action

    def _goal_transition_block(self, map_id, agent, action_type):
        name, y, x = agent
        if map_id in self.goals:
            if self.goals[map_id][y, x] <= 4:
                perception_map = self.exploration.get_goal_zone(self.states[name]['perception'])
                goal_cells_in_perception = np.where(perception_map == 100)

                if perception_map[5, 5] == 100:
                    attached = self.states[name]['attached'][0]
                    attached = [attached[1], attached[0]]
                    param = self._get_position_of_block(attached)
                    action = (name, 'detach', param)
                else:
                    # Get into the goal zone by using wavefront algorithm
                    move_selected = self._get_movement_from_perception(agent, goal_cells_in_perception, True)
                    # Perform movement
                    action = (name, 'move', move_selected)

                """
                position_target_cell = self._set_block_in_goal(action_type, map_id, name)
                position_required = [position_target_cell[0] - y, position_target_cell[1] - x]
                print('[GOAL BLOCK] check position required', name, position_required)

                if abs(sum(position_required)) == 1 and (position_required[0] == 0 or position_required[1] == 0):
                    print('DETACHING MODE', position_required)
                    # Try detach: get coordinate from position required, then try detach
                    # if no detach rotate and try again till success the process
                    last_action_result = self.states[name]['perception']['lastActionResult']
                    if last_action_result == 'failed_parameter' or last_action_result == 'failed_target':
                        action = (name, 'rotate', 'cw')
                    else:
                        
                else:
                    # Calculate the distance from n,s,e,w to target possition to decide a movement
                    move_selected = self._get_movement_from_perception(agent, position_required)
                    # Perform movement
                    action = (name, 'move', move_selected)
                    """
            else:
                param = self._get_movement_from_map(self.goals[map_id], agent)
                param = self._get_available_movement(self.states[name]['perception'], param)
                print('[GOAL BLOCK] check param', name, self.goals[map_id][y, x], param)
                action = (name, 'move', param)
        else:
            action = self.default_action(name)

        return action

    def _goal_transition_taskboard(self, map_id, agent):
        name, y, x = agent
        if map_id in self.goals:
            if self.goals[map_id][y, x] < 4:
                perception_map = self.exploration.get_goal_zone(self.states[name]['perception'])
                goal_cells_in_perception = np.where(perception_map == 100)

                # Look up for blocks in the perception
                block_position = None
                entity_presence = False
                for thing in self.states[name]['perception']['things']:
                    if thing['type'] == 'block':
                        block_position = [thing['y'], thing['x']]
                    if thing['type'] == 'entity':
                        print('[ACTION GOALS ASSEMBLE] entity', thing['y'], thing['x'], thing['y'] != 0 or thing['x'] != 0)
                        entity_presence = thing['y'] != 0 or thing['x'] != 0

                print('[ACTION GOALS ASSEMBLE] check entity presence', entity_presence, self.states[name]['perception']['things'])
                if not block_position or entity_presence:
                    if self.goals[map_id][y, x] == 0:
                        # Grid search for the center of the goal zone
                        grid = [[-1, 0, 'n'], [1, 0, 's'], [0, 1, 'e'], [0, -1, 'w']]
                        param = None
                        free_cells = 0
                        while grid:
                            position = grid.pop(0)
                            if perception_map[position[0] + 5, position[1] + 5] == 100:
                                param = position[2]
                            else:
                                free_cells += 1

                        if param and free_cells > 0:
                            action = (name, 'move', param)
                        else:
                            # Wait for interaction with other agents or blocks
                            action = (name, 'skip', None)
                    else:
                        # Get into the goal zone by using wavefront algorithm
                        move_selected = self._get_movement_from_perception(agent, goal_cells_in_perception, True)
                        # Perform movement
                        action = (name, 'move', move_selected)
                else:
                    # Check if agent has an agent attached
                    attached = None
                    for attached_thing in self.states[name]['attached']:
                        attached = abs(sum(attached_thing)) == 1 and (attached_thing[0] == 0 or attached_thing[1] == 0)

                    print('[ACTION GOALS ASSEMBLE] check attached block', attached, self.states[name]['attached'])
                    if not attached:
                        # Walk to the block and attach it
                        print('[ACTION GOALS ASSEMBLE] check block position', block_position)
                        if abs(sum(block_position)) == 1 and (block_position[0] == 0 or block_position[1] == 0):
                            param = self._get_position_of_block(block_position)
                            print('[ACTION GOALS ASSEMBLE] check attach param', param)
                            action = (name, 'attach', param)
                        else:
                            # Get closer to the side of the block by using wavefront algorithm
                            move_selected = self._get_movement_from_perception(agent, block_position)
                            # Perform movement
                            action = (name, 'move', move_selected)
                    elif perception_map[5, 5] == 100:
                        # Grid search for the center of the goal zone
                        grid = [[-1, 0, 'n'], [1, 0, 's'], [0, 1, 'e'], [0, -1, 'w']]
                        param = None
                        free_cells = 0
                        while grid:
                            position = grid.pop(0)
                            if perception_map[position[0] + 5, position[1] + 5] == 100:
                                param = position[2]
                            else:
                                free_cells += 1

                        if param and free_cells > 0:
                            action = (name, 'move', param)
                        else:
                            print('[ACTION GOALS ASSEMBLE SUBMIT]', self.states[name]['task'])
                            if self.states[name]['perception']['lastActionResult'] == 'success':
                                action = (name, 'submit', self.states[name]['task'])
                            else:
                                action = (name, 'rotate', 'cw')
                    else:
                        # Get into the goal zone by using wavefront algorithm
                        move_selected = self._get_movement_from_perception(agent, goal_cells_in_perception, True)
                        # Perform movement
                        action = (name, 'move', move_selected)
            else:
                param = self._get_movement_from_map(self.goals[map_id], agent)
                param = self._get_available_movement(self.states[name]['perception'], param)
                action = (name, 'move', param)
        else:
            action = self.default_action(name)

        return action

    def _get_block_from_dispenser(self, agent):
        perception = self.states[agent]['perception']
        if agent not in self.blocks_attached:
            self.blocks_attached[agent] = {}
            self.blocks_attached[agent]['selected'] = 0
            self.blocks_attached[agent]['available'] = ['n', 's', 'w', 'e']

        if perception['lastAction'] == 'request' and perception['lastActionResult'] == 'success':
            position = perception['lastActionParams'][0]
            action = (agent, 'attach', position)
        else:
            index = self.blocks_attached[agent]['selected']
            self.blocks_attached[agent]['selected'] = (index + 1) % 4
            action = (agent, 'request', self.blocks_attached[agent]['available'][index])

        return action

    def _set_block_in_goal(self, block_type, map_id, agent):
        # Get position of agent with task asigned
        target_agent = None
        for a in self.maps[map_id]['agents']:
            if 'task' in self.states[a[0]]['task']:
                target_agent = a

        # Get position of block in task description
        task_block_position = None
        for task in self.states[target_agent[0]]['tasks']:
            for req in task['requirements']:
                if req['type'] == block_type:
                    task_block_position = (target_agent[1] + req['y'], target_agent[2] + req['x'])

        # Calculate position where the agent has to stop in order to detach block
        target_position = None
        if task_block_position:
            attached = self.states[agent]['attached']

            # Attached elements are not [y, x] objects, they are [x, y] object so lets swap values
            attached = [[a[1], a[0]] for a in attached][0]
            target_position = (task_block_position[0] - attached[0], task_block_position[1] - attached[1])

        return target_position

    def _get_available_cells(self, perception):
        obstacles = perception['terrain']['obstacle'] if 'obstacle' in perception['terrain'] else []
        perception_map = np.matrix(np.zeros((11, 11)))
        perception_map = self._fill_diamond(perception_map)

        # Obstacles in the view has 10 as its value
        for i in range(len(obstacles)):
            perception_map[obstacles[i][1]+5, obstacles[i][0]+5] = 10

        # Check for things in the map
        things = perception['things']
        for thing in things:
            if thing['type'] == 'entity':
                perception_map[thing['y']+5, thing['x']+5] = 10

        # Check if agent has attached elements
        if perception['attached']:
            available_moves = {
                'n': perception_map[4, 5] == 1 and perception_map[4, 4] == 1 and perception_map[4, 6] == 1,
                's': perception_map[6, 5] == 1 and perception_map[6, 4] == 1 and perception_map[6, 6] == 1,
                'w': perception_map[5, 4] == 1 and perception_map[4, 4] == 1 and perception_map[6, 4] == 1,
                'e': perception_map[5, 6] == 1 and perception_map[6, 4] == 1 and perception_map[6, 6] == 1
            }
        else:
            available_moves = {
                'n': perception_map[4, 5] == 1,
                's': perception_map[6, 5] == 1,
                'w': perception_map[5, 4] == 1,
                'e': perception_map[5, 6] == 1
            }

        moves = []
        for i, m in enumerate(available_moves):
            if available_moves[m]:
                moves.append(m)

        # Check failed movements
        if perception['lastActionResult'] == 'failed_path':
            if perception['lastActionParams'][0] in moves:
                moves.remove(perception['lastActionParams'][0])

        return moves

    def _get_available_movement(self, perception, current_movement=None):
        available_params = self._get_available_cells(perception)
        if current_movement and current_movement in available_params:
            return current_movement

        return available_params[np.random.randint(len(available_params))] if len(available_params) > 0 else None

    def _get_movement_from_perception(self, agent, position_required, multiple_target=False):
        name, y, x = agent
        # Create empty map
        empty_map = self.exploration.get_obstacles(self.states[name]['perception'])
        # Update cell, obstacles and things position
        empty_map[empty_map == 0] = np.nan
        empty_map[empty_map == 10] = np.inf
        for thing in self.states[name]['perception']['things']:
            empty_map[thing['y'], thing['x']] = np.nan
        # Transform position required in local values and set to 0
        if multiple_target:
            empty_map[position_required] = 0
        else:
            empty_map[(position_required[0] + 5) % 11, (position_required[1] + 5) % 11] = 0
        # Calculate weight with wavefront for this map
        obstacles = empty_map == np.inf
        # TODO: optimizar _cost_cal para que pare cuando pase por el nivel en el que se encuentra el agente
        self.ensamble_map[name] = self._cost_calc(empty_map, obstacles)
        # Select less-cost position to move in (in local 11x11 perception map)
        possible_moves = [(4, 5, 'n'), (6, 5, 's'), (5, 4, 'w'), (5, 6, 'e')]
        distance = np.inf
        move_selected = None
        for move in possible_moves:
            # Get the closest distance to target position
            if self.ensamble_map[name][move[0], move[1]] < distance:
                distance = self.ensamble_map[name][move[0], move[1]]
                move_selected = move

        return move_selected[2]

    def _cost_calc(self, empty_map, obstacles):
        # Create new map in order to the algorithm calculates the weight
        new_map = np.full(empty_map.shape[:2], np.nan)
        new_map[obstacles] = np.inf

        # Get the position of elements to look for the calculation
        elements = np.where(empty_map == 0)
        new_map[elements] = 0
        elements = list(zip(elements[0], elements[1]))

        queue = reduce(lambda a, b: a + b, [self._get_neighbours(e, 1, new_map.shape[0]) for e in elements])
        unique_neighbours = set({})
        while queue:
            y, x, w = queue.pop(0)
            if np.isnan(new_map[y, x]):
                new_map[y, x] = w

                for neighbour in self._get_neighbours([y, x], w + 1, new_map.shape[0]):
                    key = 10000 + (neighbour[0]*100) + neighbour[1]
                    if key not in unique_neighbours:
                        unique_neighbours.add(key)
                        queue.append(neighbour)

        return new_map

    @staticmethod
    def _get_neighbours(position, weight, module):
        return [
            [(position[0] + 1) % module, position[1], weight],
            [(position[0] - 1) % module, position[1], weight],
            [position[0], (position[1] + 1) % module, weight],
            [position[0], (position[1] - 1) % module, weight],
        ]

    @staticmethod
    def _get_movement_from_map(weight_map, agent):
        _, y, x = agent
        movements = [
            (-1, 0, 'n'),
            (1, 0, 's'),
            (0, -1, 'w'),
            (0, 1, 'e'),
        ]
        min_cost_coords = movements.pop()
        while movements:
            coord = movements.pop()
            curr_y = (coord[0] + y) % 70
            curr_x = (coord[1] + x) % 70
            last_y = (min_cost_coords[0] + y) % 70
            last_x = (min_cost_coords[1] + x) % 70

            if weight_map[curr_y, curr_x] == 0:
                min_cost_coords = coord
                break
            if weight_map[curr_y, curr_x] < weight_map[last_y, last_x]:
                min_cost_coords = coord

        return min_cost_coords[2]

    @staticmethod
    def _fill_diamond(matrix):
        pattern = [10, 1]
        increment = 2
        m = matrix
        for i in range(len(m)):
            init = int(pattern[0]/2)
            finish = int(pattern[0]/2 + pattern[1]) #TODO arreglar error por el cual parece que no se come bien el init:finish
            m[i, init:finish] = 1
            if pattern[0] == 0:
                increment = -2

            pattern[0] -= increment
            pattern[1] += increment

        return m

    @staticmethod
    def _get_position_of_block(position_required):
        possible_moves = [(-1, 0, 'n'), (1, 0, 's'), (0, -1, 'w'), (0, 1, 'e')]
        param = None
        for pos in possible_moves:
            if pos[0] == position_required[0] and pos[1] == position_required[1]:
                param = pos[2]

        return param

