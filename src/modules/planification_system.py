

class PlannerSystem:
    def __init__(self):
        self.maps = {}
        self.dispensers = {}
        self.taskboards = {}
        self.goals = {}
        self.task_assigned = {}
        self.states = {}
        self.default_metas = {
            'is_goal': False,
            'is_task_board': False,
            'are_dispensers': False,
        }
        self.tasks_done = {}
        self.available_tasks = {}
        self.skip = 'skip'
        self.s_b0 = 'b0'
        self.s_b1 = 'b1'
        self.s_b2 = 'b2'
        self.s_taskboard = 'taskboard'
        self.asemble_structure = 'asemble_structure'

    def inflate(self, maps, dispensers, taskboards, goals, states):
        self.maps = maps
        self.dispensers = dispensers
        self.taskboards = taskboards
        self.goals = goals
        self.states = states

    def get_task(self):
        for map_id in self.maps:
            if map_id not in self.available_tasks:
                self.available_tasks[map_id] = [self.s_taskboard]

            # Clean duplicates caused by merges in maps or handle more than one task per team
            duplicates = []
            for agent in self.maps[map_id]['agents']:
                if agent[0] in self.task_assigned:
                    if self.task_assigned[agent[0]] in [self.s_taskboard, self.asemble_structure]:
                        duplicates.append(agent[0])

            max_tasks = len(self.maps[map_id]['agents'])//4
            if len(duplicates) > 1:
                self.available_tasks[map_id] = []
                for agent in self.maps[map_id]['agents']:
                    if agent[0] in duplicates and max_tasks > 0:
                        max_tasks -= 1
                        duplicates.remove(agent[0])
                        # TODO: arreglar esta cagada
                        for t in self.states[agent[0]]['tasks']:
                            if t['name'] == self.states[agent[0]]['task']:
                                selected_task = t
                                self.parse_meta(selected_task, map_id)
                                break
                    else:
                        self.task_assigned[agent[0]] = None

            # Evaluate tasks assigned and assign a new one if needed
            for agent in self.maps[map_id]['agents']:
                # Check if agent has a task assigned
                if agent[0] in self.task_assigned and self.task_assigned[agent[0]]:
                    task_name = self.task_assigned[agent[0]]
                    # If task is completed and store a new task into tasks_available
                    self.evaluate_task(agent[0], map_id, task_name)
                else:
                    self.task_assigned[agent[0]] = None

            # Agents with no task, has to be assigned with a new one depending of the reward stored
            self.assign_task(map_id)

        return self.task_assigned

    def parse_meta(self, meta, map_id):
        # Save the task in self.available_tasks
        for requirement in meta['requirements']:
            if requirement['type'] == 'b0':
                self.available_tasks[map_id].append(self.s_b0)
            if requirement['type'] == 'b1':
                self.available_tasks[map_id].append(self.s_b1)
            if requirement['type'] == 'b2':
                self.available_tasks[map_id].append(self.s_b2)

    def evaluate_task(self, agent, map_id, task_type):
        tasks = {
            'skip': lambda _, __: True,
            'b0': lambda ag, _: len(self.states[ag]['goal']) > 0 and len(self.states[ag]['attached']) == 0,
            'b1': lambda ag, _: len(self.states[ag]['goal']) > 0 and len(self.states[ag]['attached']) == 0,
            'b2': lambda ag, _: len(self.states[ag]['goal']) > 0 and len(self.states[ag]['attached']) == 0,
            'taskboard': lambda ag, _: self.states[ag]['task'],
            'goal': lambda _, m_id: m_id in self.goals,
            'asemble_structure': lambda ag, _: False
        }
        if tasks[task_type](agent, map_id):
            if task_type == self.s_taskboard:
                print('[TASK IN STATE] ', agent, tasks[task_type](agent, map_id))
                # Clean other agents in this map with self.s_taskboard
                # for a in self.maps[map_id]['agents']:
                #     if a[0] in self.task_assigned and self.task_assigned[a[0]] == self.s_taskboard:
                #         self.task_assigned[a[0]] = None
                self.task_assigned[agent] = self.asemble_structure
                selected_task = None
                for t in self.states[agent]['tasks']:
                    if t['name'] == self.states[agent]['task']:
                        selected_task = t
                self.parse_meta(selected_task, map_id)
            elif task_type == self.asemble_structure:
                self.available_tasks[map_id].append(self.s_taskboard)
            else:
                self.task_assigned[agent] = None

    def assign_task(self, map_id):
        agents = [agent for agent in self.maps[map_id]['agents']]
        tasks_left = []
        while self.available_tasks[map_id]:
            t = self.available_tasks[map_id].pop()
            weights = []

            for agent in agents:
                if not self.task_assigned[agent[0]]:
                    if t in [self.s_b0, self.s_b1, self.s_b2]:
                        if map_id in self.dispensers and t in self.dispensers[map_id]:
                            weights.append((self.dispensers[map_id][t][agent[1], agent[2]], agent))
                    if t == self.s_taskboard and map_id in self.taskboards:
                        weights.append((self.taskboards[map_id][agent[1], agent[2]], agent))

            if weights:
                selected_agent = min(weights)
                self.task_assigned[selected_agent[1][0]] = t
                agents.pop(agents.index(selected_agent[1]))
            else:
                tasks_left.append(t)
        for agent in agents:
            if not self.task_assigned[agent[0]]:
                self.task_assigned[agent[0]] = self.skip

        self.available_tasks[map_id] = tasks_left


