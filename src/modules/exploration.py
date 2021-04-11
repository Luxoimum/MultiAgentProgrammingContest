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
        things = perception['things']
        perception_map = np.matrix(np.zeros((11, 11)))
        perception_map = self._fill_diamond(perception_map)

        # Obstacles in the view has 10 as its value
        for i in range(len(obstacles)):
            perception_map[obstacles[i][1]+5, obstacles[i][0]+5] = 10

        # Check for useful things in the map
        # for thing in things:
        #    if thing['type'] == 'dispenser':
        #        perception_map[thing['y']+5, thing['x']+5] = 50 + int(thing['details'][1])

        # Check if perception_map is not empty
        #perception_map_mask = perception_map > 1
        #if np.any(perception_map_mask):
        #    # Check if perception_map and last_map are equals
        #    is_equal = np.array_equal(
        #        self.perception_map[perception_map_mask],
        #        perception_map[perception_map_mask]
        #    )
        #    if not is_equal:
        #        self.perception_map[:] = perception_map[:]
        #        return self.perception_map

        return perception_map

    def get_action(self, perception, last_action):
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
        if last_action in available_moves and available_moves[last_action]:
            return last_action
        else:
            moves = []
            for i, m in enumerate(available_moves):
                if available_moves[m]:
                    moves.append(m)

            # Set a new random move
            random_move = np.random.randint(len(moves))
            return moves[random_move]

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
