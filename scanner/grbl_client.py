import re
from twisted.internet import reactor, task
from twisted.internet.protocol import Protocol
from twisted.internet.serialport import SerialPort


class GrblClient(Protocol):
    startUpMsg = re.compile(r'^Grbl (\S*)')
    respOkMsg = re.compile(r'^ok$')
    respErrorMsg = re.compile(r'^error:(.*)$')
    statusReportMsg = re.compile(r'^<(\S*)>$')

    def __init__(self):
        self.port = None
        self.statusTask = task.LoopingCall(self.queryStatus)
        self.buffer = ''

    def _handleStatusReportMsg(self, msg):
        print('grbl: status "{}"'.format(msg))

    def _handleMsg(self, msg):
        match = self.startUpMsg.match(msg)
        if match:
            print('grbl: version {}'.format(match.group(1)))
            return

        match = self.respOkMsg.match(msg)
        if match:
            return

        match = self.respErrorMsg.match(msg)
        if match:
            print('grbl: error "{}"'.format(match.group(1)))
            return

        match = self.statusReportMsg.match(msg)
        if match:
            self._handleStatusReportMsg(match.group(1))
            return

        print('grbl: received unknown message "{}"'.format(msg))

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
        for line in data.decode().splitlines(True):
            self.buffer += line

            if self.buffer.endswith(('\r', '\n')):
                self.buffer = self.buffer.strip()

                if self.buffer:
                    self._handleMsg(self.buffer)

                self.buffer = ''
