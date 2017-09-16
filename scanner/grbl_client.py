import re
from twisted.internet.protocol import Protocol
from twisted.internet.serialport import SerialPort


class GrblHandler:
    def responseOk(self):
        pass

    def responseError(self, error):
        pass

    def statusUpdate(self, status):
        pass

    def disconnected(self):
        pass


class GrblClient(Protocol):
    startUpMsg = re.compile(r'^Grbl (\S*)')
    respOkMsg = re.compile(r'^ok$')
    respErrorMsg = re.compile(r'^error:(.*)$')
    statusReportMsg = re.compile(r'^<(\S*)>$')

    def __init__(self, handler):
        self.handler = handler
        self.port = None
        self.buffer = ''

    def _handleStatusReportMsg(self, msg):
        print('grbl: status "{}"'.format(msg))
        status = None
        self.handler.statusUpdate(status)

    def _handleMsg(self, msg):
        match = self.startUpMsg.match(msg)
        if match:
            print('grbl: version {}'.format(match.group(1)))
            return

        match = self.respOkMsg.match(msg)
        if match:
            self.handler.responseOk()
            return

        match = self.respErrorMsg.match(msg)
        if match:
            print('grbl: error "{}"'.format(match.group(1)))
            self.handler.responseError(match.group(1))
            return

        match = self.statusReportMsg.match(msg)
        if match:
            self._handleStatusReportMsg(match.group(1))
            return

        print('grbl: received unknown message "{}"'.format(msg))

    # Client methods
    def open(self, *args, **kwargs):
        self.port = SerialPort(self, *args, **kwargs)

    def queryStatus(self):
        self.port.write('?'.encode())

    # Callbacks for events
    def connectionMade(self):
        print('Connected to grbl device')

    def connectionLost(self, reason):
        print('Disconnected from grbl device')
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
