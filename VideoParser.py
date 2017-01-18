from PIL import Image
import subprocess as sp
import numpy
from matplotlib import pyplot

def getaveragecolor(file):
    im = Image.open(file)

    size = (1000, 1000)

    # create list of pixel's RGB values and their count (stored in color[0])
    colors = im.getcolors(1000000)

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

    print(c1, c2, c3)
    return Image.new("RGB", size, (int(c1), int(c2), int(c3)))


FFMPEG_BIN = "ffmpeg.exe"

command = [FFMPEG_BIN,
           '-i', "Im_an_Albatraoz.mp4",
           '-f', 'image2pipe',
           '-pix_fmt', 'rgb24',
           '-vcodec', 'rawvideo', '-']

pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=10 ** 8, shell=True)
i = 0
while True:

    # read 420*360*3 bytes (= 1 frame)
    raw_image = pipe.stdout.read(1280*720*3)

    if i % 24 == 0:
        # transform the byte read into a numpy array
        image = numpy.fromstring(raw_image, dtype='uint8')
        image = image.reshape((720, 1280, 3))
        # convert numpy array to image
        pyplot.imshow(image, interpolation='nearest')
        # Save file without borders
        pyplot.axis('off')
        pyplot.savefig("img" + str(i) + ".png", bbox_inches='tight', pad_inches=0, transparent=True)
        # Get average color of the last saved image
        avgImage = getaveragecolor("img" + str(i) + ".png")

    # throw away the data in the pipe's buffer.
    pipe.stdout.flush()
    i += 1

