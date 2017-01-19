from PIL import Image, ImageDraw
import subprocess as sp
import numpy
from pathlib import Path
import argparse
import AverageColor


def usage():
    print("USAGE: videoparser.py {FILENAME} -f --FRAME {NUMBER OF FRAMES TO SKIP")


FFMPEG_BIN = "ffmpeg.exe"

parser = argparse.ArgumentParser(description="Analyze the change in colors of videos over time")
parser.add_argument('-f', "--frames", dest="FRAMESKIPCOUNT", default=24)
parser.add_argument('--file', dest="FILENAME", required=True)
args = vars(parser.parse_args())

print(args)
FRAME_SKIP_COUNT = args['FRAMESKIPCOUNT']
FILENAME = args['FILENAME']
if args['FRAMESKIPCOUNT']:
    FRAME_SKIP_COUNT = int(args['FRAMESKIPCOUNT'])
print("Frame skip count", FRAME_SKIP_COUNT)


my_file = Path(FILENAME)
if not my_file.is_file():
    raise FileNotFoundError('File was not found', args['FILENAME'])

command = [FFMPEG_BIN,
           '-i', FILENAME,
           # '-ss', '00:02:00',
           '-f', 'image2pipe',
           '-pix_fmt', 'rgb24',
           '-vcodec', 'rawvideo', '-']

pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=10 ** 8, shell=True)
i = 0
pos = 0
finalImage = Image.new("RGB", (20000, 1000))
finalImageDraw = ImageDraw.Draw(finalImage, "RGB")

while True:
    # read 1 frame
    raw_image = pipe.stdout.read(1280*720*3)

    if i % FRAME_SKIP_COUNT == 0:
        # transform the byte read into a numpy array
        image = numpy.fromstring(raw_image, dtype='uint8')
        if image.size == 0:
            # Reached the end of the video
            break
        image = image.reshape((720, 1280, 3))
        img = Image.fromarray(image, 'RGB')

        avgColor = AverageColor.averagecolorfromimage(img)
        finalImageDraw.line([(pos, 0), (pos, 1000)], fill="rgb" + str(avgColor))
        pos += 1
    # throw away the data in the pipe's buffer.
    pipe.stdout.flush()
    i += 1

finalImage = finalImage.crop([0, 0, pos, 1000])
finalImage.save(FILENAME + " - color.png")
