# Flowerz bloom light animation algorithm V2.
# Copyright (C) 2015-2018 Mars Saxman. All rights reserved.

import time
import random
import math
TWO_PI = math.pi * 2.0

# all the magic numbers that shape the randomness live here
BASE_HUE_DRIFT_SECONDS = 60.0
BASE_SATURATION = 0.5
MAX_PETAL_LIFE_SECONDS = 5.0 * 60.0
MIN_PETAL_LIFE_SECONDS = 0.1


class Color:
    def __init__(self, h, s, v):
        self.hue = h
        self.saturation = s
        self.value = v
        self.red, self.green, self.blue = self._hsv_to_rgb(h, s, v)

    def _hsv_to_rgb(self, h, s, v):
        # Inputs range 0..1, outputs range 0..255
        if s == 0.0:
            v *= 255
            return [v, v, v]
        i = int(h * 6.0)
        f = (h * 6.0) - i
        p = int(255 * (v * (1.0 - s)))
        q = int(255 * (v * (1.0 - s * f)))
        t = int(255 * (v * (1.0 - s * (1.0 - f))))
        v *= 255
        i %= 6
        if i == 0:
            return [v, t, p]
        if i == 1:
            return [q, v, p]
        if i == 2:
            return [p, v, t]
        if i == 3:
            return [p, q, v]
        if i == 4:
            return [t, p, v]
        if i == 5:
            return [v, p, q]

    def __str__(self):
        return "HSV(" + \
            str(int(self.hue * 360)) + "," + \
            str(int(self.saturation * 100.0)) + "%," + \
            str(int(self.value * 100.0)) + "%)"


class Petal:
    # One component of a flower animation.
    # Each petal has an orientation, a number of lobes, min and max amplitudes,
    # and a period.
    def __init__(self, t, energy):
        hue = random.random()
        saturation = random.triangular(0.0, 1.0, 0.6)
        value = random.triangular(0.0, 1.0, 0.5)
        self.color = Color(hue, saturation, value)
        # multiplier for the sine function defining the petal shape
        self.lobes = random.randint(1, 7)
        # starting position of the petal's rotation (constant added to sin)
        self.angle = random.uniform(0, TWO_PI)
        # multiplier for the time value applied to the sine function, defining
        # rotation speed
        self.period = random.lognormvariate(0.0, 1.0)
        # flip the sign of the time multiplier, so that half the petals rotate
        # clockwise and half rotate counterclockwise
        self.period *= random.choice([-1, 1])
        # how sharp is the transition from active to inactive at the edge of
        # the petal sine curve?
        self.slope = random.gauss(0.0, 3.0)
        # at what time will this petal begin to affect the flower?
        self.begin_time = t
        # at what time will this petal stop affecting its flower? This is very
        # closely related to energy level: higher energy yields quicker change,
        # lower energy sticks around longer. Absolute max lifetime is capped to
        # keep the animation from getting stuck.
        # Energy level ranges from 0 (low) to 1 (high). At minimum energy, we
        # want maximum lifetime range. As energy level rises, we will truncate
        # the range of possibilities, driving petal lifetimes shorter.
        life = min(random.expovariate(math.pow(energy, 2.0)), 180.0)
        self.end_time = t + life

    def render(self, theta, radius, t):
        # how opaque is the petal at this location and time?
        # a sine function tells us how far the petal stretches from the center
        # at this particular angle. The petals rotate slowly over time.
        angle = self.angle + t / (self.period * TWO_PI)
        crest = (math.sin(theta * self.lobes + angle) + 1.0) / 2.0
        distance = crest - radius
        strength = (math.tanh(distance * self.slope) + 1.0) / 2.0
        return strength * self.fade(t)

    def is_dead(self, t):
        # petals last a while, then fade away, to be replaced by fresh ones
        return t >= self.end_time

    def fade(self, t):
        # how strong should this petal be at this moment in its life?
        # a petal will bloom up quickly, last a while, then fade out quickly
        dist = min(t - self.begin_time, self.end_time - t)
        fadein = 1.0 - math.exp(-math.fabs(dist * math.e))
        return fadein if t >= self.begin_time and t < self.end_time else 0.0


class Flower:
    # A flower animation projects onto a display over time.
    # A flower sits at half brightness, with a fixed hue, half saturated;
    # the hue drifts over time at a slow, steady rate.
    # Over this we apply "petals", wave functions that modulate the base color.
    # The interactions of these functions produce the animation effect.
    # Petals limit themselves to the flower's current energy level.
    # The flower's energy level waxes and wanes over time.
    def __init__(self, t, verbose):
        energy = 1.0
        self.begin_time = t
        self.verbose = verbose
        three_minutes = 3.0 * 60.0
        self.cycle_length = random.random() * three_minutes + three_minutes
        self.petals = [
            Petal(t, energy),
            Petal(t, energy),
            Petal(t, energy),
            Petal(t, energy),
            Petal(t, energy)]

    def render(self, t, display):
        # Calculate the current state of the flower and render to the display.
        for strip in range(7):
            for pixel in range(8):
                # Convert strip/pixel into cylindrical coordinate space and
                # compute the animation function for that coordinate. We will
                # pretend that there are two invisible pixels at the beginning
                # of the strip, to account for the space occupied by the
                # controller board and wire bundle.
                theta = strip / 7. * math.pi * 2.0
                radius = (pixel + 1.0) / 8.0
                light = self._calc(theta, radius, t)
                display.set(strip, pixel, light)

    def _calc(self, theta, radius, t):
        # Compute the HSV color of the flower at this location and time.
        # The base hue completes a circuit once per minute.
        light = Color(t / BASE_HUE_DRIFT_SECONDS % 1.0, BASE_SATURATION, 0)
        # Modulate the base color with each of the petals in turn.
        for petal in self.petals:
            strength = petal.render(theta, radius, t)
            light = self._modapply(light, petal.color, strength)
        return light

    def _modapply(self, base, layer, strength):
        # modulate the base color toward the layer color on each axis according
        # to the strength parameter, asymptotically, then return the result.
        # hue is funky since it wraps around; the other axes don't.
        if abs(layer.hue - base.hue) <= 0.5:
            # Move the base hue toward our hue by the strength
            hue = base.hue + (layer.hue - base.hue) * strength
        elif layer.hue < base.hue:
            hue = (base.hue + ((layer.hue + 1.0) - base.hue) * strength) % 1.0
        elif layer.hue > base.hue:
            bh = base.hue + 1.0
            hue = (bh + (layer.hue - bh) * strength) % 1.0
        else:
            # Wraparound case: drawing the base up over the top
            hue = (base.hue + (layer.hue + 1.0 - base.hue) * strength) % 1.0
        sat = base.saturation + (layer.saturation - base.saturation) * strength
        val = base.value + (layer.value - base.value) * strength
        return Color(hue, sat, val)

    def grow(self, t):
        # the flower ebbs and flows, oscillating between high-energy and
        # low-energy states; this is its cycle length. What is the current
        # energy level?
        elapsed = t - self.begin_time
        cycle_pos = elapsed / self.cycle_length * TWO_PI
        energy = math.pow((1.0 + math.cos(cycle_pos)) / 2.0, 2.0)
        for i, petal in enumerate(self.petals):
            if petal.is_dead(t):
                self.petals[i] = Petal(t, energy)
                if self.verbose:
                    self.printle(t, energy)

    def printle(self, t, energy):
        print "TIME(" + str(t) + "), ENERGY(" + str(energy) + ")"
        print "cycle_length: " + str(self.cycle_length)
        print "petals:"
        for i, petal in enumerate(self.petals):
            print "petal[" + str(i) + "]:"
            print "\tcolor: " + str(petal.color)
            print "\tlobes: " + str(petal.lobes)
            print "\tangle: " + str(int(petal.angle / TWO_PI * 360))
            print "\tperiod: " + str(petal.period)
            print "\tslope: " + str(petal.slope)
            print "\tbegin_time: " + str(petal.begin_time)
            print "\tend_time: " + str(petal.end_time)
        print "="
