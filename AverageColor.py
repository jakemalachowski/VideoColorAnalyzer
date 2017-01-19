from pathlib import Path

from PIL import Image


def averagecolorfromfile(file):

    file = Path(file)
    if not file.is_file():
        raise FileNotFoundError('File was not found', file)

    im = Image.open(file)

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

    return int(c1), int(c2), int(c3)


def averagecolorfromimage(image):

    # create list of pixel's RGB values and their count (stored in color[0])
    colors = image.getcolors(1000000)

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