import getopt

from PIL import Image
import subprocess as sp
import numpy
from matplotlib import pyplot
from pathlib import Path
import argparse


def usage():
    print("USAGE: videoparser.py {FILENAME} -f --FRAME {NUMBER OF FRAMES TO SKIP")


def getaveragecolor(file):
    im = Image.open(file)

    size = (100, 100)

    # create list of pixel's RGB values and their count (stored in color[0])
    colors = im.getcolors(1000000)

    im.close()

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

    return Image.new("RGB", size, (int(c1), int(c2), int(c3)))


FFMPEG_BIN = "ffmpeg.exe"

parser = argparse.ArgumentParser(description="Analyze the change in colors of videos over time")
parser.add_argument('-f', "--frames", default=24)
parser.add_argument('--file', dest="FILENAME", required=True )
args = vars(parser.parse_args())

print(args)

FILENAME = args['FILENAME']
if args['frames']:
    FRAME_SKIP_COUNT = int(args['frames'])
print("Frame skip count", FRAME_SKIP_COUNT)


my_file = Path(FILENAME)
if not my_file.is_file():
    raise FileNotFoundError('File was not found', args[0])

command = [FFMPEG_BIN,
           '-i', FILENAME,
          # '-ss', '00:02:22',
           '-f', 'image2pipe',
           '-pix_fmt', 'rgb24',
           '-vcodec', 'rawvideo', '-']

pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=10 ** 8, shell=True)
print(FRAME_SKIP_COUNT)
i = 0
while True:

    # read 1 frame
    raw_image = pipe.stdout.read(1280*720*3)

    if i % FRAME_SKIP_COUNT == 0:
        # transform the byte read into a numpy array
        image = numpy.fromstring(raw_image, dtype='uint8')
        if image.size == 0:
            break
        image = image.reshape((720, 1280, 3))
        # Setup details to trim the borders of the PyPlot figure
        fig = pyplot.figure()
        ax = fig.add_subplot(1, 1, 1)

        # convert numpy array to image
        pyplot.axis('off')
        pyplot.imshow(image, interpolation='nearest')
        extent = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())

        # Save file without borders
        pyplot.savefig("img" + str(i) + ".png", bbox_inches=extent)
        pyplot.close()

        # Get average color of the last saved image
        avgImage = getaveragecolor("img" + str(i) + ".png")

    # throw away the data in the pipe's buffer.
    pipe.stdout.flush()
    i += 1