import abc


class ServerCommunicationInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'connect') and
                callable(subclass.connect) and
                hasattr(subclass, 'send') and
                callable(subclass.send) and
                hasattr(subclass, 'receive') and
                callable(subclass.receive) or
                NotImplemented)

    @abc.abstractmethod
    def connect(self):
        """Connect to a server"""
        raise NotImplementedError

    @abc.abstractmethod
    def send(self, action: str):
        """Send an action to the server"""
        raise NotImplementedError

    @abc.abstractmethod
    def receive(self):
        """Receive a response from the server"""
        raise NotImplementedError

