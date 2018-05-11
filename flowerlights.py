#!/usr/bin/env python2

import argparse
import opc
import time
from display import Display
from bloom import Flower


def main(servers, verbose):
    # Add the default port number to any server names which lack one.
    servers = [(s if ':' in s else s + ':7890') for s in servers]
    # Connect to each server and store the connection object.
    clients = [opc.Client(s) for s in servers]
    # Generate the animation state.
    displays = [Display(c) for c in clients]
    start_time = time.clock()
    flowers = [Flower(start_time, verbose) for d in displays]

    # as long as we have a supply of electrons, we will use them to make photons
    last_time = start_time
    while True:
        now_time = time.clock()
        # don't bother to update more often than 100 Hz
        if now_time - last_time < 0.01:
            continue
        for f, d in zip(flowers, displays):
            f.render(now_time, d)
            d.blit()
            f.grow(now_time)
        last_time = now_time


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('servers', nargs='*', default=['localhost'])
    parser.add_argument('--verbose', '-v', default=False, action='store_true')
    main(**vars(parser.parse_args()))

