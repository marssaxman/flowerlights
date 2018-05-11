# flowerlights

Animation control code for the FLOWERZ light/metal/fabric sculpture pieces.

Each of the six light modules contains a Raspberry Pi Zero W connected to a
FadeCandy driver, with seven strips of eight WS2812 LEDs each.

Each Pi runs an instance of the FadeCandy 'fcserver' process. The animation
code connects to this server and drives it via Open Pixel Control.

Get the Fadecandy software here:
<https://github.com/scanlime/fadecandy/releases>

