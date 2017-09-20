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
    def gcode(self):
        raise RuntimeError()


class LinearMove(CommandBase):
    def __init__(self, **kwargs):
        self._gcode = 'G1'

        if 'xpos' in kwargs:
            self._gcode += ' X{}'.format(kwargs['xpos'])

        if 'ypos' in kwargs:
            self._gcode += ' Y{}'.format(kwargs['ypos'])

        if 'zpos' in kwargs:
            self._gcode += ' Z{}'.format(kwargs['zpos'])

        if 'feedrate' in kwargs:
            self._gcode += ' F{}'.format(kwargs['feedrate'])

        self._gcode += '\n'

    def gcode(self):
        return self._gcode


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
        self.buf_level = 120
        self.state = 'Unknown'

    # Incoming message handlers
    def _handleStartUpMsg(self, version):
        log.info('grbl version {version!r}', version=version)

        self.queryStatus()

    def _handleOkMsg(self):
        log.debug('grbl ok')

        # Pop command off ack queue and update buffer level
        cmd = self.ack_queue.popleft()
        self.buf_level += len(cmd.gcode())

        # Send queued commands if possible
        self._serviceQueue()

        self.handler.responseOk()

    def _handleErrorMsg(self, error):
        log.error('grbl error {error!r}', error=error)

        self.handler.responseError(error)

    def _handleStatusReportMsg(self, data):
        log.debug('grbl status {data!r}', data=data)

        # Parse data
        status = {}
        fields = data.split('|')
        for field in fields[1:]:
            type, value = field.split(':')
            status[type] = value.split(',')

        self.state = fields[0]
        self._serviceQueue()

        if 'MPos' in status:
            position = [float(x) for x in status['MPos']]
            self.handler.positionUpdate(position)

    def _handleMsg(self, msg):
        match = self.startUpMsg.match(msg)
        if match:
            self._handleStartUpMsg(version=match.group(1))
            return

        match = self.respOkMsg.match(msg)
        if match:
            self._handleOkMsg()
            return

        match = self.respErrorMsg.match(msg)
        if match:
            self._handleErrorMsg(error=match.group(1))
            return

        match = self.statusReportMsg.match(msg)
        if match:
            self._handleStatusReportMsg(data=match.group(1))
            return

        log.warn('grbl received unknown message {msg!r}', msg=msg)

    # Send queued messages if there is space in grbl's receive buffer
    def _serviceQueue(self):
        if self.state is 'Unknown':
            return

        if not self.cmd_queue:
            # No commands queued
            return

        gcode = self.cmd_queue[0].gcode()
        if len(gcode) > self.buf_level:
            # Not enough space
            return

        # Send command to grbl
        log.debug('sending gcode to grbl {gcode!r}', gcode=gcode)
        self.port.write(gcode.encode())

        # Update buffer level and move to the ack queue
        self.buf_level -= len(gcode)
        self.ack_queue.append(self.cmd_queue.popleft())

    # Client methods
    def open(self, *args, **kwargs):
        self.port = SerialPort(self, *args, **kwargs)

    def queryStatus(self):
        self.port.write('?'.encode())

    def queueCommand(self, command):
        self.cmd_queue.append(command)
        self._serviceQueue()

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
