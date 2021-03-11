import numpy as np


class Exploration:
    def __init__(self):
        self.map = np.matrix(np.zeros((11, 11)))
        self.obstacles_map = np.matrix(np.zeros((11, 11)))
        self.things_map = np.matrix(np.zeros((11, 11)))
        self.map_blur = None
        self.OBSTACLE = 2
        self.ENTITY = 1
        self.movements = ['n', 's', 'w', 'e']
        self.action = self.movements[np.random.randint(4)]

    def get_map(self, perception):
        obstacles = perception['terrain']['obstacle'] if 'obstacle' in perception['terrain'] else []
        things = perception['things']
        prev_map = np.matrix(np.zeros((11, 11)))
        prev_map = self._fill_diamond(prev_map)

        # obstacles in the view has 10 as its value
        for i in range(len(obstacles)):
            prev_map[obstacles[i][1]+5, obstacles[i][0]+5] = 10



        is_equal = None
        prev_map_mask = prev_map > 1
        if np.any(prev_map_mask):
            ignore_entities_mask1 = self.obstacles_map[prev_map_mask] < 100
            ignore_entities_mask2 = prev_map[prev_map_mask] < 100
            is_equal = np.array_equal(self.obstacles_map[prev_map_mask][ignore_entities_mask1], prev_map[prev_map_mask][ignore_entities_mask2])

        if not is_equal:
            self.obstacles_map[:] = prev_map[:]

        # entities in the view has 100 as its value
        for thing in things:
            if thing['type'] == 'entity':
                if thing['x'] != 0 or thing['y'] != 0:
                    prev_map[thing['y']+5, thing['x']+5] = 100

        self.map = prev_map

        return self.obstacles_map if not is_equal else []

    def get_action(self):
        grid_in_front = {
            'n': self.map[4, 5],
            's': self.map[6, 5],
            'w': self.map[5, 4],
            'e': self.map[5, 6]
        }

        if grid_in_front[self.action] == 1:
            return self.action
        else:
            coords = [self.map[4, 5], self.map[6, 5], self.map[5, 4], self.map[5, 6]]
            options = []
            for i in range(4):
                if coords[i] == 1:
                    options.append(i)

            self.action = self.movements[options[np.random.randint(len(options))]]
            return self.action

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
