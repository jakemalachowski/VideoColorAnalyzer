from PIL import Image, ImageDraw
import subprocess as sp
import numpy
from pathlib import Path
import argparse
import AverageColor


def usage():
    print("USAGE: videoparser.py {FILENAME} -f --FRAME {NUMBER OF FRAMES TO SKIP")

# Get the arguments from the command line and assign them to variables
parser = argparse.ArgumentParser(description="Analyze the change in colors of videos over time")
parser.add_argument('-f', "--frames", dest="FRAMESKIPCOUNT", default=24)
parser.add_argument('--file', dest="FILENAME", required=True)
args = vars(parser.parse_args())

FRAME_SKIP_COUNT = args['FRAMESKIPCOUNT']
FILENAME = args['FILENAME']
if args['FRAMESKIPCOUNT']:
    FRAME_SKIP_COUNT = int(args['FRAMESKIPCOUNT'])
print("Frame skip count", FRAME_SKIP_COUNT)

# Make sure the file is valid
my_file = Path(FILENAME)
if not my_file.is_file():
    raise FileNotFoundError('File was not found', args['FILENAME'])

# Run the command to start the FFMPEG library
FFMPEG_BIN = "ffmpeg.exe"

command = [FFMPEG_BIN,
           '-i', FILENAME,
           '-f', 'image2pipe',
           '-pix_fmt', 'rgb24',
           '-vcodec', 'rawvideo', '-']

# Open pipe to start receiving pixel data
pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=10 ** 8, shell=True)
# i is for processing every 'FRAME_SKIP_COUNT'th element
i = 0
# pos is to hold the position to draw the next line
pos = 0

# TODO: Calculate the number of frames to base the height and width
width = 20000
height = 1000
# Declare a blank image and prepare it for drawing
finalImage = Image.new("RGB", (20000, height))
finalImageDraw = ImageDraw.Draw(finalImage, "RGB")

while True:
    # read 1 frame
    raw_image = pipe.stdout.read(1280*720*3)

    if i % FRAME_SKIP_COUNT == 0:
        # transform the byte read into a numpy array
        image = numpy.fromstring(raw_image, dtype='uint8')
        if image.size == 0:
            # No more data, reached the end of the video
            break
        # Put the data into an image for processing (Can this be skipped to improve performance?)
        image = image.reshape((720, 1280, 3))
        img = Image.fromarray(image, 'RGB')

        avgColor = AverageColor.averagecolorfromimage(img)
        # Draw a line
        finalImageDraw.line([(pos, 0), (pos, height)], fill="rgb" + str(avgColor))
        pos += 1
    # throw away the data in the pipe's buffer.
    pipe.stdout.flush()
    i += 1

# Crop the image and save it
finalImage = finalImage.crop([0, 0, pos, 1000])
finalImage.save(FILENAME + " - color.png")
