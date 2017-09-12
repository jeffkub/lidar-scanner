from twisted.internet import reactor, task
from twisted.internet.protocol import Protocol
from twisted.internet.serialport import SerialPort


class GrblClient(Protocol):
    def __init__(self):
        self.port = None
        self.statusTask = task.LoopingCall(self.queryStatus)
        self.buffer = ''

    def _recvMessage(self, msg):
        print('grbl: {}'.format(msg))

    # Client methods
    def open(self, port, *args, **kwargs):
        self.port = SerialPort(self, port, reactor, *args, **kwargs)

        # Start polling servo position
        self.statusTask.start(0.2)

    def queryStatus(self):
        self.port.write('?'.encode())

    # Callbacks for events
    def connectionMade(self):
        print('Connected to grbl device')

    def connectionLost(self, reason):
        print('Disconnected from grbl device')

        # Stop polling servo position
        self.statusTask.stop()

    def dataReceived(self, data):
        for c in data.decode():
            # Skip leading whitespace
            if self.buffer or not c.isspace():
                self.buffer += c

            if self.buffer and c in ['\r', '\n']:
                self._recvMessage(self.buffer.strip())
                self.buffer = ''
