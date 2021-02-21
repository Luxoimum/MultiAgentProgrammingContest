import numpy as np
import matplotlib.pyplot as plt


class AgentState:
    def __init__(self, map_size=(70, 70), vision_radius=5):
        self.global_map = np.zeros(map_size)
        self.position = tuple(int(i/2) for i in map_size)
        self.radius = vision_radius
        self.number_of_renders = 0

    def update_map(self, partial_map):
        y, x = tuple(p - self.radius for p in self.position)
        length = len(partial_map)
        map_shape = self.global_map.shape
        if y + length <= map_shape[0] and x + length <= map_shape[1]:
            self.global_map[y: y+length, x: x+length] = self.global_map[y: y+length, x: x+length] + partial_map

            _map_background = np.zeros(self.global_map.shape)
            plt.pcolormesh(np.arange(_map_background.shape[0]+1),
                           np.arange(_map_background.shape[0]+1),
                           _map_background,
                           cmap='Paired')
            x, y = np.where(np.rot90(self.global_map, 3) != 0)
            area = np.ones(x.size)*15
            plt.scatter(x, y, c='salmon', marker='s', s=area)
            plt.savefig('map' + str(self.number_of_renders) + '.png')
            self.number_of_renders += 1

    def update_position(self, updated_position):
        y, x = updated_position
        movement = {
            '01': [*[i for i in range(1, len(self.global_map))], 0],
            '0-1': [len(self.global_map)-1, *[i for i in range(0, len(self.global_map)-1)]],
            '10': [*[i for i in range(1, len(self.global_map))], 0],
            '-10': [len(self.global_map)-1, *[i for i in range(0, len(self.global_map)-1)]],
        }
        if y == 0:
            self.global_map = self.global_map[:, movement[str(y)+str(x)]]
        else:
            self.global_map = self.global_map[movement[str(y)+str(x)], :]

