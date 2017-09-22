import collections
from enum import Enum
import re
from twisted.internet import task
from twisted.internet.protocol import Protocol
from twisted.internet.serialport import SerialPort
from twisted.logger import Logger

log = Logger()


class GrblState(Enum):
    Unknown = 'Unknown'
    Idle = 'Idle'
    Run = 'Run'
    Hold = 'Hold'
    Jog = 'Jog'
    Alarm = 'Alarm'
    Door = 'Door'
    Check = 'Check'
    Home = 'Home'
    Sleep = 'Sleep'


class GrblHandler:
    def startup(self, version):
        pass

    def responseOk(self, command):
        pass

    def responseError(self, command, error):
        pass

    def positionUpdate(self, mpos):
        pass

    def disconnected(self):
        pass


class CommandBase:
    def gcode(self):
        raise RuntimeError()


class LinearMove(CommandBase):
    def __init__(self, xpos=None, ypos=None, zpos=None, feedrate=None):
        self._gcode = 'G1'

        if xpos is not None:
            self._gcode += ' X{}'.format(xpos)

        if ypos is not None:
            self._gcode += ' Y{}'.format(ypos)

        if zpos is not None:
            self._gcode += ' Z{}'.format(zpos)

        if feedrate is not None:
            self._gcode += ' F{}'.format(feedrate)

        self._gcode += '\n'

    def gcode(self):
        return self._gcode


class GrblClient(Protocol):
    start_up_msg = re.compile(r'^Grbl (\S*)')
    resp_ok_msg = re.compile(r'^ok$')
    resp_error_msg = re.compile(r'^error:(.*)$')
    status_report_msg = re.compile(r'^<(.*)>$')

    def __init__(self, handler):
        self.handler = handler
        self.port = None
        self.poll_task = task.LoopingCall(self.queryStatus)
        self.buffer = ''
        self.cmd_queue = collections.deque()
        self.ack_queue = collections.deque()
        self.buf_level = 120
        self.state = GrblState.Unknown

    # Incoming message handlers
    def _handleStartUpMsg(self, version):
        log.info('grbl version {version!r}', version=version)

        self.handler.startup(version)

    def _handleOkMsg(self):
        log.debug('grbl ok')

        # Pop command off ack queue and update buffer level
        cmd = self.ack_queue.popleft()
        self.buf_level += len(cmd.gcode())

        # Send queued commands if possible
        self._serviceQueue()

        self.handler.responseOk(cmd)

    def _handleErrorMsg(self, error):
        log.error('grbl error {error!r}', error=error)

        # Pop command off ack queue and update buffer level
        cmd = self.ack_queue.popleft()
        self.buf_level += len(cmd.gcode())

        # Send queued commands if possible
        self._serviceQueue()

        self.handler.responseError(cmd, error)

    def _handleStatusReportMsg(self, data):
        log.debug('grbl status {data!r}', data=data)

        # Parse data
        status = {}
        fields = data.split('|')
        for field in fields[1:]:
            type, value = field.split(':')
            status[type] = value.split(',')

        self.state = GrblState(fields[0])
        self._serviceQueue()

        if 'MPos' in status:
            position = [float(x) for x in status['MPos']]
            self.handler.positionUpdate(position)

    def _handleMsg(self, msg):
        match = self.start_up_msg.match(msg)
        if match:
            self._handleStartUpMsg(version=match.group(1))
            return

        match = self.resp_ok_msg.match(msg)
        if match:
            self._handleOkMsg()
            return

        match = self.resp_error_msg.match(msg)
        if match:
            self._handleErrorMsg(error=match.group(1))
            return

        match = self.status_report_msg.match(msg)
        if match:
            self._handleStatusReportMsg(data=match.group(1))
            return

        log.warn('grbl received unknown message {msg!r}', msg=msg)

    # Send queued messages if there is space in grbl's receive buffer
    def _serviceQueue(self):
        if self.state is GrblState.Unknown:
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

        # TODO: Re-init class variables

        # Start polling status
        self.poll_task.start(0.2)

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
        self.poll_task.stop()
        self.handler.disconnected()

    def dataReceived(self, data):
        for line in data.decode().splitlines(True):
            self.buffer += line

            if self.buffer.endswith('\n'):
                self.buffer = self.buffer.strip()

                if self.buffer:
                    self._handleMsg(self.buffer)

                self.buffer = ''
