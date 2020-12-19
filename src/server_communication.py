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

    def __connect(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.conf['host'], self.conf['port']))
        self.s.settimeout(5.00)
        self.s.send(json.dumps(self.auth).encode() + end)
        response = None
        while response is None:
            self.buffer += self.s.recv(8192)
            c = self.buffer.find(end)
            if c != -1:
                response = self.buffer[:c].decode()
            self.buffer = b''
        print('[server communication]')
        print(response)

    def __handle_step_connection(self):
        try:
            self.buffer += self.s.recv(8192)
        except NotResponseException:
            pass
        c = self.buffer.find(end)
        if c != -1:
            response = self.buffer[:c].decode()
            print('[server communication]')
            print(response)
            self.buffer = b''
            self.buffer_manager.write_percept(response)

    def connect(self):
        self.__connect()

    def send(self, action):
        self.s.send(json.dumps(action).encode() + end)

    def pol(self):
        while self.buffer_manager.percept_buffer.empty():
            self.__handle_step_connection()

