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
        obstacles = perception['terrain']['obstacle'] if 'obstacle' in perception['terrain'] else []
        goal = perception['terrain']['goal'] if 'goal' in perception['terrain'] else []
        perception_map = np.matrix(np.zeros((11, 11)))
        perception_map = self._fill_diamond(perception_map)

        # Obstacles in the view has 10 as its value
        for obstacle in obstacles:
            perception_map[obstacle[1]+5, obstacle[0]+5] = 10

        # Goal area in the view has 5 as its value
        for gcell in goal:
            perception_map[gcell[1]+5, gcell[0]+5] = 5

        return perception_map

    def get_action(self, perception):
        perception_map = self.get_map(perception)
        # Check for things in the map
        things = perception['things']
        for thing in things:
            if thing['type'] == 'entity':
                perception_map[thing['y']+5, thing['x']+5] = 100

        available_moves = {
            'n': perception_map[4, 5] == 1,
            's': perception_map[6, 5] == 1,
            'w': perception_map[5, 4] == 1,
            'e': perception_map[5, 6] == 1
        }
        # Check if we can continue moving
        if self.last_action in available_moves and available_moves[self.last_action]:
            return self.last_action
        else:
            available_indexes = []
            for i, m in enumerate(available_moves):
                if available_moves[m]:
                    available_indexes.append(i)

            # Set a new random move
            if len(available_indexes) > 0:
                random_index = available_indexes[np.random.randint(len(available_indexes))]
                self.last_action = [m for m in available_moves][random_index]
            else:
                self.last_action = None

            return self.last_action

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
