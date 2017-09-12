import argparse
from twisted.internet import reactor
from grbl_client import GrblClient
from lidar_client import LidarClient


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--grbl', default='/dev/ttyUSB0')
    parser.add_argument('--lidar', default='/dev/ttyUSB1')

    args = parser.parse_args()

    grbl = GrblClient()
    grbl.open(args.grbl, baudrate='115200')

    #lidar = LidarClient()
    #lidar.open(args.lidar, baudrate='115200')

    reactor.run()
