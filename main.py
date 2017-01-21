import logging
import numpy
import os
import progressbar
import sys
import subprocess
import time
import videoparser

from PIL import Image, ImageDraw

logging.basicConfig(format="[%(asctime)s %(name)s %(levelname)s] %(message)s")
logging.getLogger(__name__).setLevel(logging.INFO)


def usage():
    print("usage: videoparser.py video_file output.png")


if len(sys.argv) != 3:
    usage()
    sys.exit(1)

video = videoparser.Video(sys.argv[1])
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

widgets = [
    progressbar.Percentage(), ' ',
    progressbar.Bar(), ' ',
    progressbar.AdaptiveTransferSpeed(unit="f"), ' ',
    progressbar.ETA()
]

with progressbar.ProgressBar(max_value=video.total_frames, widgets=widgets) as bar:
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
