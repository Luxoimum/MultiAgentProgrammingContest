import socket
import multiprocessing
import json
from exceptions.not_response_exception import NotResponseException

end = b'\0'


class ServerCommunication(multiprocessing.Process):
    def __init__(self, buffer_manager, conf, auth):
        multiprocessing.Process.__init__(self)
        self.buffer_manager = buffer_manager()
        self.conf = conf
        self.auth = auth
        self.s = None
        self.buffer = b''
        self.__connect()
        while True:
            self.__handle_step_connection()

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

        print(response)

    def __handle_step_connection(self):
        try:
            self.buffer += self.s.recv(8192)
        except NotResponseException:
            pass
        c = self.buffer.find(end)
        if c != -1:
            response = self.buffer[:c].decode()
            print(response)
            self.buffer = b''
            self.buffer_manager.write_percept(response)




