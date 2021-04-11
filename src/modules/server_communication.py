import socket
import json
from exceptions.not_response_exception import NotResponseException

end = b'\0'


class ServerCommunication:
    def __init__(self, buffer_manager, conf, auth):
        self.buffer_manager = buffer_manager
        self.conf = conf
        self.auth = auth
        self.s = None
        self.buffer = b''

    def connect(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(10)
        self.s.connect((self.conf['host'], self.conf['port']))
        self.s.send(json.dumps(self.auth).encode() + end)
        response = None
        while response is None:
            self.buffer += self.s.recv(8192)
            c = self.buffer.find(end)
            if c != -1:
                response = self.buffer[:c].decode()
                self.buffer = b''
                print('[server communication]', response)

    def send(self, action):
        try:
            self.s.send(json.dumps(action).encode() + end)
        except NotResponseException:
            return False
        return True

    def receive(self, debug=False):
        response = None
        while not response:
            try:
                self.buffer += self.s.recv(8192)
            except NotResponseException:
                print('[server communication]', 'no response from server')
                pass
            c = self.buffer.find(end)
            if c != -1:
                response = self.buffer[:c].decode()
                self.buffer = b''
                debug and print('[server communication]', 'response', response)
                self.buffer_manager.write_percept(response)

        return response

