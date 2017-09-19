import collections
import re
from twisted.logger import Logger
from twisted.internet.protocol import Protocol
from twisted.internet.serialport import SerialPort

log = Logger()


class GrblHandler:
    def responseOk(self):
        pass

    def responseError(self, error):
        pass

    def positionUpdate(self, mpos):
        pass

    def disconnected(self):
        pass


class CommandBase:
    def format(self):
        pass


class LinearMove(CommandBase):
    def __init__(self, **kwargs):
        self.params = kwargs

    def format(self):
        command = 'G1'

        if 'xpos' in self.params:
            command += ' X{}'.format(self.params['xpos'])

        if 'ypos' in self.params:
            command += ' Y{}'.format(self.params['ypos'])

        if 'zpos' in self.params:
            command += ' Z{}'.format(self.params['zpos'])

        if 'feedrate' in self.params:
            command += ' F{}'.format(self.params['feedrate'])

        return command


class GrblClient(Protocol):
    startUpMsg = re.compile(r'^Grbl (\S*)')
    respOkMsg = re.compile(r'^ok$')
    respErrorMsg = re.compile(r'^error:(.*)$')
    statusReportMsg = re.compile(r'^<(.*)>$')

    def __init__(self, handler):
        self.handler = handler
        self.port = None
        self.buffer = ''
        self.cmd_queue = collections.deque()
        self.ack_queue = collections.deque()

    def _handleStatusReportMsg(self, data):
        # Parse data
        status = {}
        fields = data.split('|')
        for field in fields[1:]:
            type, value = field.split(':')
            status[type] = value.split(',')

        if 'MPos' in status:
            position = [float(x) for x in status['MPos']]
            self.handler.positionUpdate(position)

    def _handleMsg(self, msg):
        match = self.startUpMsg.match(msg)
        if match:
            version = match.group(1)
            log.info('grbl version {version!r}', version=version)
            return

        match = self.respOkMsg.match(msg)
        if match:
            log.debug('grbl ok')
            self.handler.responseOk()
            return

        match = self.respErrorMsg.match(msg)
        if match:
            error = match.group(1)
            log.error('grbl error {error!r}', error=error)
            self.handler.responseError(error)
            return

        match = self.statusReportMsg.match(msg)
        if match:
            data = match.group(1)
            log.debug('grbl status {msg!r}', msg=msg)
            self._handleStatusReportMsg(data)
            return

        log.warn('grbl received unknown message {msg!r}', msg=msg)

    # Client methods
    def open(self, *args, **kwargs):
        self.port = SerialPort(self, *args, **kwargs)

    def queryStatus(self):
        self.port.write('?'.encode())

    def queueCommand(self, command):
        self.cmd_queue.append(command)

    # Callbacks for events
    def connectionMade(self):
        log.info('Connected to grbl device')

    def connectionLost(self, reason):
        log.info('Disconnected from grbl device')
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
