from twisted.logger import Logger
from twisted.internet.protocol import Protocol
from twisted.internet.serialport import SerialPort

log = Logger()


class LidarHandler:
    def distanceUpdate(self, timestamp, dist):
        pass

    def disconnected(self):
        pass


class LidarClient(Protocol):
    def __init__(self, handler):
        self.handler = handler
        self.port = None
        self.buffer = ''

    def _handleMsg(self, msg):
        timestamp, dist = msg.split(',')
        self.handler.distanceUpdate(timestamp, dist)

    # Client methods
    def open(self, *args, **kwargs):
        self.port = SerialPort(self, *args, **kwargs)

    def start(self):
        self.port.write('start\n'.encode())

    def stop(self):
        self.port.write('stop\n'.encode())

    # Callbacks for events
    def connectionMade(self):
        log.info('Connected to lidar device')

    def connectionLost(self, reason):
        log.info('Disconnected from lidar device')
        self.port = None
        self.handler.disconnected()

    def dataReceived(self, data):
        for line in data.decode().splitlines(True):
            self.buffer += line

            if self.buffer.endswith('\n'):
                self.buffer = self.buffer.strip()

                if self.buffer:
                    self._handleMsg(self.buffer)

                self.buffer = ''
