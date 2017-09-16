from twisted.internet.protocol import Protocol
from twisted.internet.serialport import SerialPort


class LidarClient(Protocol):
    def __init__(self):
        self.port = None

    # Client methods
    def open(self, *args, **kwargs):
        self.port = SerialPort(self, *args, **kwargs)

    # Callbacks for events
    def connectionMade(self):
        print('Connected to lidar device')

    def connectionLost(self, reason):
        print('Disconnected from lidar device')

    def dataReceived(self, data):
        print('Received data from lidar device: "{}"'.format(data))
