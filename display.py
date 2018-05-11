
class Display:
    def __init__(self, client):
        self._client = client
    # Big grid representing all the pixels Fadecandy knows how to drive.
    # This is a conceptual matrix of 8 strips with 64 pixels each.
    # Our actual hardware only uses 7 strips with 8 pixels each, so the other
    # pixels go unused.
    _raw_pixels = [(0, 0, 0)] * (8 * 64)

    def blit(self):
        self._client.put_pixels(self._raw_pixels)

    def set(self, strip, pixel, it):
        self._raw_pixels[strip * 64 + pixel] = (it.red, it.green, it.blue)

