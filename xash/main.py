"""

  Xash

  The harsh economics of treasure-based adventuring

"""
import logging
import argparse
import pyglet

def parsesize(wxh):
    """ split WxH at 'x' and int each component """
    return tuple(int(n) for n in wxh.split('x'))

def construct_window(width, height, *args, **kw):
    """ try to construct a window with as high
    quality settings as possible """
    for optdict in [
        dict(major_version=3, minor_version=0,
             sample_buffers=1, samples=4),
        dict(sample_buffers=1, samples=4),
        dict()]:
        try:
            config = pyglet.gl.Config(**optdict)
            win = pyglet.window.Window(
                width, height,
                *args, config=config, **kw)
            return win
        except pyglet.window.NoSuchConfigException:
            pass
    return None

class XashWindow:
    """ container for pyglet Window displaying the game """
    def __init__(self, args):
        try:
            width, height = parsesize(args.size)
        except (ValueError, TypeError) as e:
            logging.error(e)
            width, height = (1024, 768)
        win = construct_window(width, height,
                               fullscreen=args.fullscreen)
        if win is None:
            logging.error("No window")
            raise SystemExit(1)
        self.win = win

def main():
    """ read the command line """
    ap = argparse.ArgumentParser()
    add = ap.add_argument
    add("--fullscreen", action="store_const",
        const=True, default=False)
    add("--size", metavar="WxH", default="1024x768",
        help="window size e.g. 1024x768")
    args = ap.parse_args()
    win = XashWindow(args)
    pyglet.app.run()

