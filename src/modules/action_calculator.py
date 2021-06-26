import numpy as np


class ActionCalculator:
    def __init__(self):
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
                    actions.append(self._goal_transition(map_id, agent, task))
                elif task in [self.s_b0, self.s_b1, self.s_b2]:
                    if len(self.states[agent[0]]['attached']) > 0:
                        actions.append(self._goal_transition(map_id, agent, task))
                    else:
                        actions.append(self._block_transition(map_id, agent, task))
                else:
                    actions.append(self.default_action(agent[0]))

        return actions

    def default_action(self, agent):
        if agent in self.last_actions:
            action = self.last_actions[agent]
        else:
            available_params = ['n', 's', 'w', 'e']
            action = (agent, 'move', available_params[np.random.randint(len(available_params))])
            self.last_actions[agent] = action

        return action

    def _taskboard_transition(self, map_id, agent):
        name, y, x = agent
        if map_id in self.taskboards:
            if self.taskboards[map_id][y, x] == 1:
                if self.states[name]['tasks']:
                    action = (name, 'accept', self.states[name]['tasks'][0]['name'])
                else:
                    action = (name, 'skip', None)
            else:
                param = self._get_movement(self.taskboards[map_id], agent)
                action = (name, 'move', param)
        else:
            action = self.default_action(name)
        return action

    def _block_transition(self, map_id, agent, block_type):
        name, y, x = agent
        if map_id in self.dispensers and block_type in self.dispensers[map_id]:
            if self.dispensers[map_id][block_type][y, x] == 1:
                action = self._get_block_from_dispenser(name)
            else:
                param = self._get_movement(self.dispensers[map_id][block_type], agent)
                action = (name, 'move', param)
        else:
            action = self.default_action(name)

        return action

    def _goal_transition(self, map_id, agent, action_type):
        name, y, x = agent
        if map_id in self.goals:
            if self.goals[map_id][y, x] == 110:
                if action_type == self.asemble_structure:
                    action = (name, 'submit', self.states[name]['task'])
                else:
                    index = self.blocks_attached[name]['selected']
                    action = (name, 'detach', self.blocks_attached[name]['available'][index])
            else:
                param = self._get_movement(self.goals[map_id], agent)
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

    @staticmethod
    def _get_movement(graph_fire, agent):
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

            if graph_fire[curr_y, curr_x] == 110:
                min_cost_coords = coord
                break
            if graph_fire[curr_y, curr_x] < graph_fire[last_y, last_x]:
                min_cost_coords = coord

        return min_cost_coords[2]



