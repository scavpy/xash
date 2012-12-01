#!/usr/bin/env python3
"""
 Open a window and clear it to a specified colour
"""

import pyglet
from pyglet.gl import *
import ctypes
import numpy as np


        
class TWin:
    def __init__(self, *args, **kw):
        try:
            self.bg_colour = kw["bg"]
            del kw["bg"]
        except KeyError:
            self.bg_colour = (0,0,0,1)
        w = self.win = pyglet.window.Window(*args, **kw)
        w.set_handlers(self.on_draw)

    def on_draw(self):
        glClearColor(*self.bg_colour)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)



if __name__ == '__main__':
    win = TWin(200,200,caption="Test",bg=(0.4, 0.2, 0.5, 1.0))
    pyglet.app.run()

