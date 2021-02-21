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

    def analize(self, perception):
        obstacles = perception['terrain']['obstacle'] if 'obstacle' in perception['terrain'] else []
        things = perception['things']

        self._update_map(obstacles, things)

    def _update_map(self, obstacles, things):
        self.map = np.matrix(np.zeros((11, 11)))

        for i in range(len(obstacles)):
            self.map[obstacles[i][1]+5, obstacles[i][0]+5] = -1

        for thing in things:
            if thing['type'] == 'entity':
                if thing['x'] != 0 or thing['y'] != 0:
                    self.map[thing['y']+5, thing['x']+5] = -1

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

