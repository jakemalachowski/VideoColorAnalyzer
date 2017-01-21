from concurrent.futures import ThreadPoolExecutor

import os
import logging
import subprocess

from PIL import Image

from frame import Frame


FFMPEG_BIN = "ffmpeg"
FFPROBE_BIN = "ffprobe"
FNULL = open(os.devnull, 'w')


class UnknownCodecError(Exception):
    pass


class Video(object):
    def __init__(self, path):
        self.path = path

        self.codec = self._codec(self.path)
        if self.codec == "unknown":
            raise UnknownCodecError("can't parse video, unkown codec")

        pool = ThreadPoolExecutor(5)

        resolution_future = pool.submit(self._resolution, self.path)
        duration_future = pool.submit(self._duration, self.path)
        frame_rate_future = pool.submit(self._frame_rate, self.path)

        self.width, self.height = resolution_future.result()
        logging.info("video resolution is: %dx%d" % (self.width, self.height))

        self.bytes_per_frame = self.width * self.height * 3

        self.frame_rate = frame_rate_future.result()
        logging.info("frame rate: %.2f" % self.frame_rate)

        self.duration = duration_future.result()

        self.estimated_total_frames = int(self.duration * self.frame_rate)
        logging.info("total frames in video: %d" % self.estimated_total_frames)

        self.proc = self._spawn(self.path)
        logging.info("video stream opened")

        self.current_frame = 0

    def next_frame(self):
        self.current_frame += 1
        data = self.proc.stdout.read(self.bytes_per_frame)

        if len(data) != self.bytes_per_frame:
            return None

        return Frame(data, self.width, self.height, self.current_frame)

    def has_next_frame(self):
        return self.current_frame <= self.estimated_total_frames

    def _resolution(self, path):
        out = subprocess.check_output([FFPROBE_BIN, "-v", "error", "-of",
            "flat=s=_", "-select_streams", "v:0", "-show_entries",
            "stream=height,width", path])

        lines = out.split("\n")
        width = lines[0].split('=')[1]
        height = lines[1].split('=')[1]
        return (int(width), int(height))

    def _duration(self, path):
        out = subprocess.check_output([FFPROBE_BIN, "-i", path, "-show_entries",
           "format=duration", "-v", "error", "-of", "csv=p=0"])

        return float(out)

    def _frame_rate(self, path):
        out = subprocess.check_output([FFPROBE_BIN, "-v", "0", "-of",
            "compact=p=0", "-select_streams", "0", "-show_entries",
            "stream=r_frame_rate", path])
        n, d = out.split("=")[1].split("/")
        return float(n) / float(d)

    def _codec(self, path):
        out = subprocess.check_output([FFPROBE_BIN, "-v", "error",
            "-select_streams", "v:0", "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1", path])

        return out.strip()

    def _spawn(self, path):
        command = [FFMPEG_BIN, '-i', path, '-f', 'image2pipe', '-pix_fmt',
                'rgb24', '-vcodec', 'rawvideo', '-']

        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=FNULL,
                bufsize=self.bytes_per_frame * 300)

