import json
import logging
import os
import subprocess

from PIL import Image

from frame import Frame



class UnknownCodecError(Exception):
    pass


class Video(object):
    # Number of frames to buffer when reading in the raw video from ffmpeg over
    # a pipe.
    BUFFER_NFRAMES = 300

    # What format each pixel should have in the frames we get back from ffmpeg.
    PIX_FMT = "rgb24"

    FFMPEG_BIN = "ffmpeg"
    FFPROBE_BIN = "ffprobe"
    FNULL = open(os.devnull, 'w')

    def __init__(self, path, frames_wanted=None, downscale=None):
        self.path = path

        self.frames_wanted = frames_wanted or self.total_frames
        self.frames_given = 0

        self.downscale = downscale or 1

        self._get_info()

        if self.codec == "unknown":
            raise UnknownCodecError("can't parse video, unkown codec")

        self.proc = self._spawn()

    def next_frame(self):
        # We can only give a positive integer for frame skipping, which means
        # we'll more frames than was asked for. This check is to avoid returning
        # those frames.
        #
        # Given how we calculate this, the number of frames we miss should be no
        # more than the framestep value we pass to ffmpeg later on.
        if self.frames_wanted and self.frames_given >= self.frames_wanted:
            return None

        data = self.proc.stdout.read(self.bytes_per_frame)

        if len(data) != self.bytes_per_frame:
            return None

        self.frames_given += 1
        return Frame(data, self.out_width, self.out_height)

    def _get_info(self):
        out = subprocess.check_output([self.FFPROBE_BIN, "-v", "error", "-of",
            "json", "-select_streams", "v:0", "-show_entries", "stream",
            self.path])

        info = json.loads(out)
        stream = info['streams'][0]

        self.width = int(stream['width'])
        self.height = int(stream['height'])
        self.codec = stream['codec_name']
        self.duration = float(stream['duration'])

        self.out_width = self.width / self.downscale
        self.out_height = self.height / self.downscale

        fr = stream['r_frame_rate']
        a, b = fr.split('/')
        self.frame_rate = float(a) / float(b)

        afr = stream['avg_frame_rate']
        c, d = fr.split('/')
        self.avg_frame_rate = float(c) / float(d)

        self.total_frames = int(stream['nb_frames'])

        # This relies on us using a pixel format of rgb24 in the ffmpeg command.
        # If that changes, the 3 in this equation may be wrong.
        self.bytes_per_frame = self.out_width * self.out_height * 3


    def _spawn(self):
        step = int(float(self.total_frames) / float(self.frames_wanted))

        opts = ['-i', self.path,
                '-f', 'image2pipe',
                '-pix_fmt', self.PIX_FMT,
                '-vcodec', 'rawvideo',
                '-vf', 'framestep=step=%d,scale=iw/%d:-1' % (step,
                    self.downscale)]

        command = [self.FFMPEG_BIN] + opts + ['-']
        return subprocess.Popen(command, stdout=subprocess.PIPE,
                stderr=self.FNULL, bufsize=self.bytes_per_frame *
                self.BUFFER_NFRAMES)

