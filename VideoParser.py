import logging
import numpy
import os
import progressbar
import sys
import subprocess
import time

from PIL import Image, ImageDraw

FFMPEG_BIN = "ffmpeg"
FFPROBE_BIN = "ffprobe"
FNULL = open(os.devnull, 'w')

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

logging.basicConfig(format="[%(asctime)s %(name)s %(levelname)s] %(message)s")
logger = logging.getLogger("videoparser")
logger.setLevel(logging.INFO)

class Video(object):
    def __init__(self, path):
        self.path = path

        logger.info("determining video resolution...")
        self.width, self.height = self._resolution(self.path)
        logger.info("video resolution is: %dx%d" % (self.width, self.height))

        self.bytes_per_frame = self.width * self.height * 3

        logger.info("counting frames...")
        self.total_frames = self._total_frames(self.path)
        logger.info("total frames in video: %d" % self.total_frames)

        logger.info("determining framerate...")
        self.frame_rate = self._frame_rate(self.path)
        logger.info("frame rate: %.2f" % self.frame_rate)

        logger.info("opening video stream...")
        self.proc = self._spawn(self.path)
        logger.info("video stream opened")

        self.current_frame = 0

    def next_frame(self):
        self.current_frame += 1
        data = self.proc.stdout.read(self.bytes_per_frame)

        if len(data) != self.bytes_per_frame:
            return None

        return Frame(data, self.width, self.height, self.current_frame)

    def has_next_frame(self):
        return self.current_frame <= self.total_frames

    def _resolution(self, path):
        out = subprocess.check_output([FFPROBE_BIN, "-v", "error", "-of",
            "flat=s=_", "-select_streams", "v:0", "-show_entries",
            "stream=height,width", path])

        lines = out.split("\n")
        width = lines[0].split('=')[1]
        height = lines[1].split('=')[1]
        return (int(width), int(height))

    def _total_frames(self, path):
        out = subprocess.check_output([FFPROBE_BIN, "-count_frames",
            "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames",
            "-of", "default=nokey=1:noprint_wrappers=1", "-v", "error", path])
        return int(out)

    def _frame_rate(self, path):
        out = subprocess.check_output([FFPROBE_BIN, "-v", "0", "-of",
            "compact=p=0", "-select_streams", "0", "-show_entries",
            "stream=r_frame_rate", path])
        n, d = out.split("=")[1].split("/")
        return float(n) / float(d)

    def _spawn(self, path):
        command = [FFMPEG_BIN, '-i', path, '-f', 'image2pipe', '-pix_fmt',
                'rgb24', '-vcodec', 'rawvideo', '-']

        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=FNULL,
                bufsize=self.bytes_per_frame * 300)


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


def usage():
    print("usage: videoparser.py video_file output.png")


if len(sys.argv) != 3:
    usage()
    sys.exit(1)

video = Video(sys.argv[1])
out_path = sys.argv[2]

out_width = 1920
out_height = 1080
out_frame = 0

# Number of frames to skip to ensure we only sample $out_width frames, so that
# we create the ideal image and don't need to resize it later.
frame_skip = int(video.total_frames / float(out_width))

# Declare a blank image and prepare it for drawing
out_image = Image.new("RGB", (out_width, out_height))
out_image_draw = ImageDraw.Draw(out_image, "RGB")

last_frame = None

with progressbar.ProgressBar(max_value=video.total_frames) as bar:
    while video.has_next_frame():
        frame = video.next_frame()

        # Skip frames according to the given sample rate.
        if frame.number % frame_skip != 0:
            continue

        out_image_draw.line([(out_frame, 0), (out_frame, out_height)], fill="rgb" +
                str(frame.average_color()))
        out_frame += 1

        if last_frame == None:
            last_frame = frame
            continue

        bar.update(frame.number)

out_image.save(out_path)
