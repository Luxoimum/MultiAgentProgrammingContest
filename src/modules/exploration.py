import numpy as np
import json

class Exploration:
    def __init__(self):
        self.map = np.matrix(np.zeros((11, 11)))
        self.map_blur = None
        self.OBSTACLE = 2
        self.ENTITY = 1
        self.movements = ['n', 's', 'w', 'e']
        self.action = self.movements[np.random.randint(4)]
        print(self.action)

    def get_map(self, perception):
        obstacles = perception['terrain']['obstacle'] if 'obstacle' in perception['terrain'] else []
        things = perception['things']
        prev_map = np.matrix(np.zeros((11, 11)))

        for i in range(len(obstacles)):
            prev_map[obstacles[i][1]+5, obstacles[i][0]+5] = 1

        for thing in things:
            if thing['type'] == 'entity':
                if thing['x'] != 0 or thing['y'] != 0:
                    prev_map[thing['y']+5, thing['x']+5] = 2

        is_equal = None

        if np.count_nonzero(prev_map) > 0:
            is_equal = np.array_equal(self.map, prev_map)

        if not is_equal:
            self.map = prev_map

        return self.map if not is_equal else []

    def get_action(self):
        grid_in_front = {
            'n': self.map[4, 5],
            's': self.map[6, 5],
            'w': self.map[5, 4],
            'e': self.map[5, 6]
        }

        if grid_in_front[self.action] == 0:
            return self.action
        else:
            coords = [self.map[4, 5], self.map[6, 5], self.map[5, 4], self.map[5, 6]]
            options = []
            for i in range(4):
                if coords[i] == 0:
                    options.append(i)

            self.action = self.movements[options[np.random.randint(len(options))]]
            return self.action

