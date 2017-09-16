from twisted.logger import Logger
from twisted.internet.protocol import Protocol
from twisted.internet.serialport import SerialPort

log = Logger()


class LidarClient(Protocol):
    def __init__(self):
        self.port = None

    # Client methods
    def open(self, *args, **kwargs):
        self.port = SerialPort(self, *args, **kwargs)

    # Callbacks for events
    def connectionMade(self):
        log.info('Connected to lidar device')

    def connectionLost(self, reason):
        log.info('Disconnected from lidar device')

    def dataReceived(self, data):
        log.info('Received data from lidar device {data!r}', data=data)
