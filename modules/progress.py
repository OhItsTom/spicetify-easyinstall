# Based on https://github.com/kennethreitz-archive/clint/blob/master/clint/textui/progress.py
from __future__ import absolute_import

import sys
import time

STREAM = sys.stderr

BAR_TEMPLATE = '%s[%s%s] %i/%i - %s\r'
MILL_TEMPLATE = '%s %s %i/%i\r'

DOTS_CHAR = '.'
BAR_FILLED_CHAR = '#'
BAR_EMPTY_CHAR = ' '
MILL_CHARS = ['|', '/', '-', '\\']

# How long to wait before recalculating the ETA
ETA_INTERVAL = 1
# How many intervals (excluding the current one) to calculate the simple moving
# average
ETA_SMA_WINDOW = 9


class Bar(object):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.done()
        return False  # we're not suppressing exceptions

    def __init__(self, label='', width=32, hide=None, empty_char=BAR_EMPTY_CHAR,
                 filled_char=BAR_FILLED_CHAR, expected_size=None, every=1):
        if len(label) > 24 and "." in label:
            ext = label[label.rfind("."):]
            label = label[:24-len(ext)-2] + ".." + ext
        self.label = label
        self.width = width
        self.hide = hide
        # Only show bar in terminals by default (better for piping, logging etc.)
        if hide is None:
            try:
                self.hide = not STREAM.isatty()
            except AttributeError:  # output does not support isatty()
                self.hide = True
        self.empty_char =    empty_char
        self.filled_char =   filled_char
        self.expected_size = expected_size
        self.every =         every
        self.start =         time.time()
        self.ittimes =       []
        self.eta =           0
        self.etadelta =      time.time()
        self.etadisp =       self.format_time(self.eta)
        self.last_progress = 0
        if (self.expected_size):
            self.show(0)

    def show(self, progress, count=None):
        if count is not None:
            self.expected_size = count
        if self.expected_size is None:
            raise Exception("expected_size not initialized")
        self.last_progress = progress
        if (time.time() - self.etadelta) > ETA_INTERVAL:
            self.etadelta = time.time()
            self.ittimes = \
                self.ittimes[-ETA_SMA_WINDOW:] + \
                    [-(self.start - time.time()) / (progress+1)]
            self.eta = \
                sum(self.ittimes) / float(len(self.ittimes)) * \
                (self.expected_size - progress)
            self.etadisp = self.format_time(self.eta)
        if not self.hide and (
            (
                (progress % self.every) == 0
                or (progress == self.expected_size)  # True every "every" updates
            )
        ):   # And when we're done
            # STREAM.write(BAR_TEMPLATE % (
            #     self.label, self.filled_char * x,
            #     self.empty_char * (self.width - x), progress,
            #     self.expected_size, self.etadisp))
            BAR_TEMPLATE = '%-4s - %s [%s%s] %-24s\r'
            percent = f"{int(progress/self.expected_size*100)}%"
            x = int(self.width * progress / self.expected_size)
            STREAM.write(BAR_TEMPLATE % (
                percent, self.etadisp,
                self.filled_char * x,
                self.empty_char * (self.width - x),
                self.label[:24]))
            STREAM.flush()

    def done(self):
        self.elapsed = time.time() - self.start
        elapsed_disp = self.format_time(self.elapsed)
        if not self.hide:
            # Print completed bar with elapsed time
            # STREAM.write(BAR_TEMPLATE % (
            #     self.label, self.filled_char * self.width,
            #     self.empty_char * 0, self.last_progress,
            #     self.expected_size, elapsed_disp))
            BAR_TEMPLATE = '%-4s - %s [%s%s] %-24s\r'
            percent = "100%"
            STREAM.write(BAR_TEMPLATE % (
                percent, self.etadisp,
                self.filled_char * self.width,
                self.empty_char * (self.width - self.width),
                self.label[:24]))
            STREAM.write('\n')
            STREAM.flush()

    def format_time(self, seconds):
        return time.strftime('%M:%S', time.gmtime(seconds))


def bar(it, label='', width=32, hide=None, empty_char=BAR_EMPTY_CHAR,
        filled_char=BAR_FILLED_CHAR, expected_size=None, every=1):
    """Progress iterator. Wrap your iterables with it."""

    count = len(it) if expected_size is None else expected_size

    with Bar(label=label, width=width, hide=hide, empty_char=empty_char,
             filled_char=filled_char, expected_size=count, every=every) \
            as bar:
        for i, item in enumerate(it):
            yield item
            bar.show(i + 1)
