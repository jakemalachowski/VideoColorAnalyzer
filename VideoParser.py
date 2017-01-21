import logging
import numpy
import os
import sys
import subprocess
import time

from PIL import Image, ImageDraw

FFMPEG_BIN = "ffmpeg.exe"
FFPROBE_BIN = "ffprobe.exe"
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


def get_resolution(path):
    out = subprocess.check_output([FFPROBE_BIN, "-v", "error", "-of", "flat=s=_",
        "-select_streams", "v:0", "-show_entries", "stream=height,width", path])

    print(out)
    lines = out.split(b'\n')
    width = lines[0].split(b'=')[1]
    height = lines[1].split(b'=')[1]
    return int(width), int(height)


def get_num_frames(path):
    out = subprocess.check_output([FFPROBE_BIN, "-count_frames",
        "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames",
        "-of", "default=nokey=1:noprint_wrappers=1", "-v", "error", path])
    return int(out)


def get_video_stream(path, bufsize):
    command = [FFMPEG_BIN, '-i', path, '-f', 'image2pipe',
            '-pix_fmt', 'rgb24', '-vcodec', 'rawvideo', '-']

    return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=FNULL,
            bufsize=bufsize)


def get_frame_rate(path):
    out = subprocess.check_output([FFPROBE_BIN, "-v", "0", "-of", "compact=p=0",
        "-select_streams", "0", "-show_entries", "stream=r_frame_rate", path])
    n, d = out.split(b"=")[1].split(b"/")
    return float(n) / float(d)


def get_average_color(raw_frame, width, height):
    frame = numpy.fromstring(raw_frame, dtype='uint8')
    frame = frame.reshape((height, width, 3))
    image = Image.fromarray(frame, 'RGB')

    width, height = image.size

    image = image.resize((int(width / SCALE_FACTOR), int(height / SCALE_FACTOR)), FILTER)

    # create list of pixel's RGB values and their count (stored in color[0])
    colors = image.getcolors(MAX_COLORS)

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
    print("usage: videoparser.py video_file")


if len(sys.argv) != 2:
    usage()
    sys.exit(1)

path = sys.argv[1]
width, height = get_resolution(path)
width = int(width)
height = int(height)
logger.info("video resolution: %dx%d" % (width, height))

bytes_per_frame = width * height * 3

frame_rate = get_frame_rate(path)
logger.info("video frame rate: %f" % frame_rate)

logger.info("counting frames...")
frames = get_num_frames(path)
logger.info("total frames in video: %d" % frames)

out_width = 1920
out_height = 1080
out_frame = 0

# Number of frames to skip to ensure we only sample $out_width frames, so that
# we create the ideal image and don't need to resize it later.
frame_skip = int(frames / float(out_width))

# Declare a blank image and prepare it for drawing
out_image = Image.new("RGB", (out_width, out_height))
out_image_draw = ImageDraw.Draw(out_image, "RGB")

stream = get_video_stream(path, 360 * bytes_per_frame)
current_frame = 0
last_frame = 0
t = time.time()

while True:
    current_frame += 1
    raw_frame = stream.stdout.read(bytes_per_frame)

    if len(raw_frame) == 0:
        logger.info("reached end of video file")
        break

    # Skip frames according to the given sample rate.
    if current_frame % frame_skip != 0:
        continue

    avg_color = get_average_color(raw_frame, width, height)

    out_image_draw.line([(out_frame, 0), (out_frame, out_height)],
            fill="rgb" + str(avg_color))
    out_frame += 1

    now = time.time()
    time_delta = now - t
    frame_delta = current_frame - last_frame
    fps = frame_delta / time_delta
    percent = current_frame / float(frames) * 100

    # Counting frames per second like this is sort-of a lie because we're not
    # processing every frame, but I've used it as a measure for how much
    # improvement each change makes.
    logger.info("[%.2f%%] processing %.2f fps" % (percent, fps))

    last_frame = current_frame
    t = now

out_image.save(path + ".colors.png")
logger.info("File saved at " + path + ".colors.png")