from multiprocessing import Queue


class BufferManager:
    def __init__(self):
        self.percept_buffer = Queue()
        self.action_buffer = Queue()

    def read_percept(self):
        return self.percept_buffer.get(True) if not self.percept_buffer.empty() else None

    def write_percept(self, percept):
        self.percept_buffer.put(percept, True)

    def read_action(self):
        return self.action_buffer.get(True) if not self.action_buffer.empty() else None

    def write_action(self, action):
        self.action_buffer.put(action, True)

