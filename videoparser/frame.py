import numpy
from PIL import Image


# To save processing time, you can choose to downsize each frame before
# calculating the average color. A larger scale factor results in faster
# processing.
SCALE_FACTOR = 2 ** 4

# While filter to use when resizing images. The fastest is Image.NEAREST, but
# it's also the least accurate. Image.ANTIALIAS is slowest, but will result in a
# better average. Image.BILINEAR and Image.BICUBIC are good tradeoffs.
FILTER = Image.ANTIALIAS

# The maximum number of colors you expect per frame. Because we have to allocate
# the memory for these ahead of time, high numbers can be costly. However, if a
# frame has more colors than this number in it, that frame is skipped.
MAX_COLORS = 2 ** 10


class Frame(object):
    def __init__(self, data, width, height, number):
        self.data = data
        self.width = width
        self.height = height
        self.number = number

        self.np = numpy.fromstring(self.data, dtype='uint8')
        self.np = self.np.reshape((self.height, self.width, 3))
        self.image = Image.fromarray(self.np, 'RGB')

    def average_color(self):
        resized = self.image.resize((self.width / SCALE_FACTOR, self.height /
            SCALE_FACTOR), FILTER)

        # create list of pixel's RGB values and their count (stored in color[0])
        colors = resized.getcolors(MAX_COLORS)

        if colors == None:
            # TODO
            pass

        count = 0
        c1 = 0
        c2 = 0
        c3 = 0

        # add all the values up and divide by the total number of
        # pixels to get the average rgb value

        for color in colors:
            count += color[0]
            c1 += (color[1][0] * color[0])
            c2 += (color[1][1] * color[0])
            c3 += (color[1][2] * color[0])

        c1 /= count
        c2 /= count
        c3 /= count

        return int(c1), int(c2), int(c3)

