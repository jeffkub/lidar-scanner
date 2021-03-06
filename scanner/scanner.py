import argparse
import logging
from twisted.internet import reactor
from twisted.logger import globalLogPublisher, STDLibLogObserver
from grbl_client import GrblClient, GrblHandler, LinearMove
from lidar_client import LidarClient, LidarHandler


class GrblCallbacks(GrblHandler):
    def startup(self, version):
        pass

    def responseOk(self, command):
        pass

    def responseError(self, command, error):
        pass

    def positionUpdate(self, status):
        pass

    def disconnected(self):
        pass


class LidarCallbacks(LidarHandler):
    def distanceUpdate(self, timestamp, dist):
        pass

    def disconnected(self):
        pass


if __name__ == '__main__':
    # Setup logging
    logging.basicConfig()
    logging.root.setLevel(logging.DEBUG)
    globalLogPublisher.addObserver(STDLibLogObserver())

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--grbl', default='/dev/grbl')
    parser.add_argument('--lidar', default='/dev/lidar')

    args = parser.parse_args()

    grbl = GrblClient(GrblCallbacks())
    grbl.open(args.grbl, reactor, baudrate='115200')

    lidar = LidarClient(LidarCallbacks())
    lidar.open(args.lidar, reactor, baudrate='115200')

    grbl.queueCommand(LinearMove(xpos=-90, ypos=90, feedrate=1800))
    grbl.queueCommand(LinearMove(xpos=90, ypos=-90, feedrate=1800))

    lidar.start()

    reactor.run()
