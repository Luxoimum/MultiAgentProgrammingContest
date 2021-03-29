import numpy as np


class AgentState:
    def __init__(self, map_size=(70, 70), agents=None):
        self.map_size = map_size
        self.agent_state = {
            'states': {},
            'maps': {}
        }
        if agents:
            for agent in agents:
                self.add_agent_state(agent)

    @property
    def maps(self):
        return self.agent_state['maps']

    @property
    def states(self):
        return self.agent_state['states']

    def add_agent_state(self, agent_name):
        self.agent_state['maps'][agent_name] = {
            'map_id': 'map_' + agent_name,
            'map': np.zeros(self.map_size),
            'y': int(self.map_size[0]/2),
            'x': int(self.map_size[1]/2)
        }
        self.agent_state['states'][agent_name] = {}

    def try_synchronize_map(self, agent_name, shared_map_to_merge, position):
        # roll map to merge with
        shared_map_to_merge = np.roll(shared_map_to_merge, position[0], axis=0)
        shared_map_to_merge = np.roll(shared_map_to_merge, position[1], axis=1)

        mask = shared_map_to_merge > 0

        self.agent_state['maps'][agent_name][mask] = shared_map_to_merge[mask]

    def update_position(self, agent_name, updated_position):
        y, x = updated_position
        self.agent_state['maps'][agent_name]['y'] = (self.agent_state['maps'][agent_name]['y'] + y) % 70
        self.agent_state['maps'][agent_name]['x'] = (self.agent_state['maps'][agent_name]['x'] + x) % 70

    def update_map(self, agent_name, partial_map):
        map_shape = self.agent_state['maps'][agent_name]['map'].shape
        padding = map_shape[0]-len(partial_map)

        y = self.agent_state['maps'][agent_name]['y'] - 5
        x = self.agent_state['maps'][agent_name]['x'] - 5
        map_padded = np.pad(partial_map, ((0, padding), (0, padding)), mode='constant')
        map_padded = np.roll(map_padded, y, axis=0)
        map_padded = np.roll(map_padded, x, axis=1)

        mask = map_padded > 0

        self.agent_state['maps'][agent_name]['map'][mask] = map_padded[mask]

    def merge_maps(self, current, target, current_position, target_position):
        current_map = self.agent_state['maps'][current]['map']
        target_map = self.agent_state['maps'][target]['map']
        # Check if both agents are in the same perception
        self.try_synchronize_map(current_map, target_map, target_position)
        # First of all store old position
        old_target_y = self.agent_state['maps'][target]['y']
        old_target_x = self.agent_state['maps'][target]['x']
        ols_map_id = self.agent_state['maps'][target]['map_id']
        # Next update target agent
        self.agent_state['maps'][target]['y'] = (self.agent_state['maps'][current]['y'] + current_position[0]) % 70
        self.agent_state['maps'][target]['x'] = (self.agent_state['maps'][current]['x'] + current_position[1]) % 70
        self.agent_state['maps'][target]['map_id'] = self.agent_state['maps'][current]['map_id']
        self.agent_state['maps'][target]['map'] = self.agent_state['maps'][current]['map']
        # Subtract old position the new one
        old_target_y = old_target_y - self.agent_state['maps'][target]['y']
        old_target_x = old_target_x - self.agent_state['maps'][target]['x']
        # Then search agents with old map_id and substitute for new one and new position
        for agent in self.agent_state['maps']:
            if self.agent_state['maps'][agent]['map_id'] == ols_map_id:
                self.agent_state['maps'][agent]['y'] = (self.agent_state['maps'][agent]['y'] - old_target_y) % 70
                self.agent_state['maps'][agent]['x'] = (self.agent_state['maps'][agent]['x'] - old_target_x) % 70
                self.agent_state['maps'][agent]['map_id'] = self.agent_state['maps'][current]['map_id']
                self.agent_state['maps'][agent]['map'] = self.agent_state['maps'][current]['map']
