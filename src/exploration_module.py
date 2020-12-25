import numpy as np
import cv2 as cv

class ExplorationModule:
    def __init__(self):
        self.map = np.matrix(np.zeros((10, 10)))
        self.OBSTACLE = 2
        self.ENTITY = 1
        self.movements = ['n', 's', 'w', 'e']
        self.action = self.movements[np.random.randint(4)]
        print(self.action)

    def update_map(self, obstacles=None, things=None, entities=None):
        self.map = np.matrix(np.zeros((10, 10)))
        for i in range(len(obstacles)):
            self.map[obstacles[i][1]+4, obstacles[i][0]+4] = 8

        self.map = cv.GaussianBlur(self.map, (5, 5), 0).astype(int)
        print(self.map)

    def get_action(self):
        if self.map[4, 4] == 0:
            return self.action
        else:
            coords = [self.map[5, 4], self.map[3, 4], self.map[4, 3], self.map[4, 5]]
            options = []
            for i in range(4):
                if coords[i] == 0:
                    options.append(i)

            self.action = self.movements[options[np.random.randint(len(options))]]
            return self.action

