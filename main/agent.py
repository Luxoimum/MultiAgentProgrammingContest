from server_communication import ServerCommunication
from buffer_manager import BufferManager
from common_structures import CommonStructures


class Agent:
    def __init__(self, name):
        self.bm = BufferManager
        self.cm = CommonStructures(name)
        self.sc = ServerCommunication(buffer_manager=self.bm, conf=self.cm.CONF, auth=self.cm.AUTH)
        while True:
            response = self.bm.read_percept()
            if response is not None:
                print(response)


Agent("agentA2")

