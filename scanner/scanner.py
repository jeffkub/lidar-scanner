import argparse
import logging
from twisted.internet import reactor, task
from twisted.logger import globalLogPublisher, STDLibLogObserver
from grbl_client import GrblClient, GrblHandler
from lidar_client import LidarClient


class GrblCallbacks(GrblHandler):
    def responseOk(self):
        pass

    def responseError(self, error):
        pass

    def statusUpdate(self, status):
        pass

    def disconnected(self):
        pollTask.stop()


def pollStatus():
    grbl.queryStatus()


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

    lidar = LidarClient()
    lidar.open(args.lidar, reactor, baudrate='115200')

    pollTask = task.LoopingCall(pollStatus)
    pollTask.start(0.2)

    reactor.run()
