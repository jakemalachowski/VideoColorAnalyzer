import logging
import numpy
from PIL import Image

# If you want to play around with the constants below, you can use the following
# command to compare your output (provided you have imagemagick installed):
#
#   $ compare -verbose -metric fuzz img1.png img2.png diff.png
#
# The values below seem to be a small trade off in accuracy for a large trade
# off in speed.


# The maximum number of colors you expect per frame. Because we have to allocate
# the memory for these ahead of time, high numbers can be costly. However, if a
# frame has more colors than this number in it, that frame is skipped.
MAX_COLORS = 2 ** 14


class Frame(object):
    def __init__(self, data, width, height):
        self.data = data
        self.width = width
        self.height = height

        self.np = numpy.fromstring(self.data, dtype='uint8')
        self.np = self.np.reshape((self.height, self.width, 3))
        self.image = Image.fromarray(self.np, 'RGB')

    def average_color(self):
        # create list of pixel's RGB values and their count (stored in color[0])
        colors = self.image.getcolors(MAX_COLORS)

        if colors == None:
            logging.warn("frame skipped due to having more colors than we " +
                    "allocated space to count")

            # This results in a black line in the output image.
            return (0, 0, 0)

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

