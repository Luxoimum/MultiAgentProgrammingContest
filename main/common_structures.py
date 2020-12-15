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


