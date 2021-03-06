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
        map_shape = self.global_map.shape
        padding = map_shape[0]-len(partial_map)
        map_padded = np.pad(partial_map, ((0, padding), (0, padding)), mode='constant')
        map_padded = np.roll(map_padded, y, axis=0)
        map_padded = np.roll(map_padded, x, axis=1)
        mask = map_padded > 0
        self.global_map[mask] = map_padded[mask]

        plt.imshow(self.global_map, interpolation='nearest')
        plt.savefig('map' + str(self.number_of_renders) + '.png')
        self.number_of_renders += 1

    def update_position(self, updated_position):
        y, x = updated_position
        prev_y, prev_x = self.position
        self.position = tuple((prev_y + y, prev_x + x))

