#!/usr/bin/env python

# Turn all the lights off: reset.

import opc, time
client = opc.Client('localhost:7890')
pixels = [(0, 0, 0)] * 512

for x in range(1):
	client.put_pixels(pixels)
	time.sleep(0.05)

