

class BufferManager:
    def __init__(self):
        self.percept_buffer = []
        self.action_buffer = []

    def read_percept(self):
        return self.percept_buffer[-1]

    def write_percept(self, percept):
        self.percept_buffer.append(percept)

    def read_action(self):
        return self.action_buffer[-1]

    def write_action(self, action):
        self.action_buffer.append(action)

