#!/usr/bin/env python2

import argparse
import opc
import time


def main(servers):
    for s in servers:
        # Add the default port number to any server names which lack one.
        client = opc.Client(s if ':' in s else s + ':7890')
        # Turn all the lights off: reset.
        pixels = [(0, 0, 0)] * 512
        for x in range(1):
            client.put_pixels(pixels)
            time.sleep(0.05)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('servers', nargs='*', default=['localhost'])
    main(**vars(parser.parse_args()))
