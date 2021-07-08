import numpy as np


class Exploration:
    def __init__(self):
        self.perception_map = np.matrix(np.zeros((11, 11)))
        self.things_map = np.matrix(np.zeros((11, 11)))
        self.map_blur = None
        self.OBSTACLE = 2
        self.ENTITY = 1
        self.movements = ['n', 's', 'w', 'e']
        self.last_action = self.movements[np.random.randint(4)]

    def get_map(self, perception):
        goal = perception['terrain']['goal'] if 'goal' in perception['terrain'] else []
        things = perception['things']
        perception_map = self.get_obstacles(perception)

        # Goal zone and things in the view has 10 as its value
        for thing in things:
            if thing['type'] == 'dispenser':
                perception_map[thing['y']+5, thing['x']+5] = 10

        for i in range(len(goal)):
            perception_map[goal[i][1]+5, goal[i][0]+5] = 10

        return perception_map

    def get_obstacles(self, perception):
        obstacles = perception['terrain']['obstacle'] if 'obstacle' in perception['terrain'] else []
        perception_map = np.matrix(np.zeros((11, 11)))
        perception_map = self._fill_diamond(perception_map)

        # Obstacles in the view has 10 as its value
        for i in range(len(obstacles)):
            perception_map[obstacles[i][1]+5, obstacles[i][0]+5] = 10

        return perception_map

    def get_goal_zone(self, perception):
        goal = perception['terrain']['goal'] if 'goal' in perception['terrain'] else []
        obstacles = perception['terrain']['obstacle'] if 'obstacle' in perception['terrain'] else []
        perception_map = np.matrix(np.zeros((11, 11)))
        perception_map = self._fill_diamond(perception_map)

        # Obstacles in the view has 10 as its value
        for i in range(len(obstacles)):
            perception_map[obstacles[i][1]+5, obstacles[i][0]+5] = 10

        # Goal zone int he view has 100 as its value
        for i in range(len(goal)):
            perception_map[goal[i][1]+5, goal[i][0]+5] = 100

        return perception_map

    def get_available_cells(self, perception):
        perception_map = self.get_obstacles(perception)

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
