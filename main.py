import progressbar
import sys
import videoparser

from PIL import Image, ImageDraw


def usage():
    print("usage: main.py video_file output.png")


if len(sys.argv) != 3:
    usage()
    sys.exit(1)

# Declare a blank image and prepare it for drawing
out_image = Image.new("RGB", (1920, 1080))
out_image_draw = ImageDraw.Draw(out_image, "RGB")
out_frame = 0

video = videoparser.Video(sys.argv[1], frames_wanted=out_image.width,
        downscale=2 ** 4)

out_path = sys.argv[2]

widgets = [
    progressbar.Percentage(), ' ',
    progressbar.Bar(), ' ',
    progressbar.AdaptiveTransferSpeed(unit="f"), ' ',
    progressbar.ETA()
]

bar = progressbar.ProgressBar(max_value=out_image.width, widgets=widgets)

with bar:
    while True:
        frame = video.next_frame()
        if frame == None:
            break

        out_image_draw.line([(out_frame, 0), (out_frame, out_image.height)],
                fill="rgb" + str(frame.average_color()))
        out_frame += 1

        bar.update(out_frame)

out_image.save(out_path)
