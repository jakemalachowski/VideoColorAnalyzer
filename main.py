import logging
import numpy
import os
import progressbar
import sys
import subprocess
import time
import videoparser

from PIL import Image, ImageDraw

logging.basicConfig(
        format="[%(asctime)s %(name)s %(levelname)s] %(message)s",
        level=logging.INFO)


def usage():
    print("usage: main.py video_file output.png")


if len(sys.argv) != 3:
    usage()
    sys.exit(1)

video = videoparser.Video(sys.argv[1])
out_path = sys.argv[2]

# Declare a blank image and prepare it for drawing
out_image = Image.new("RGB", (1920, 1080))
out_image_draw = ImageDraw.Draw(out_image, "RGB")
out_frame = 0

# Because the output image is of a fixed size that we know ahead of time, an
# excellent way of saving on processing time is to only process out_image.width
# number of frames. Because we have a single vertical line of colour for each
# pixel in the width of the output image, we only need to analyse that many
# frames in the input video.
#
# This calculation tells out loop below how many frames to skip between frames
# to actually process.
frame_skip = int(video.total_frames / float(out_image.width))

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

        out_image_draw.line([(out_frame, 0), (out_frame, out_image.height)],
                fill="rgb" + str(frame.average_color()))
        out_frame += 1

        bar.update(frame.number)

out_image.save(out_path)
