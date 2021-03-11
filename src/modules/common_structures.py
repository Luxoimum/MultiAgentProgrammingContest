import numpy as np

class CommonStructures:
    def __init__(self, name):
        self.CONF = {
            "host": "localhost",
            "port": 12300
        }
        self.AUTH = {
            "type": "auth-request",
            "content": {
                "user": name,
                "pw": "1"
            }
        }
        self.ACTION = {
            "type": "action",
            "content": {
                "id": None,
                "type": None,
                "p": None
            }
        }
        self.SKIP_ACTION = {
            "type": "status-request",
            "content": {}
        }
        self.MOVE = 0
        self.SKIP = 1
        self.ATTACH = 2
        self.DETACH = 3
        self.ROTATE = 4
        self.CONNECT = 5
        self.DISCONNECT = 6
        self.REQUEST = 7
        self.SUBMIT = 8
        self.CLEAR = 9
        self.ACCEPT = 10
        self.ACTION_TYPES = [
            "move",
            "skip",
            "attach",
            "detach",
            "rotate",
            "connect",
            "disconnect",
            "request",
            "submit",
            "clear",
            "accept"
        ]

    def get_action_structure(self, id=None, action_type=None, params=None):
        if id is not None and params is not None:
            content = self.ACTION['content']
            content['id'] = id
            content['type'] = action_type
            content['p'] = params
            return self.ACTION
        else:
            return self.SKIP_ACTION


