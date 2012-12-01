#!/usr/bin/env python3
"""
 Open a window and clear it to a specified colour.
 Draw a cuboid in the middle with various possible
 shaders applied to it.
"""
import random
import pyglet
from pyglet.gl import *
from pyglet.window import key
import ctypes
from ctypes import byref, cast, POINTER

from shaders import Shader, ShaderProgram
import tnvmesh

SIMPLE_VSHADER = b"""
#version 130
smooth out float brightness;

void main()
{
  vec3 sunlight_direction = normalize(vec3(3.0, 1.0, 7.0));
  float ambient_brightness = 0.3;
  float diffuse_brightness = 0.7 * max(0.0, dot(gl_Normal, sunlight_direction));
  brightness = ambient_brightness + diffuse_brightness;
  gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
  gl_TexCoord[0] = gl_MultiTexCoord0;
}
"""

GRAPHPAPER_FSHADER = b"""
#version 130
uniform vec4 paper = vec4(1.0, 1.0, 0.95, 1.0);
uniform vec4 ink = vec4(0.6, 0.9, 1.0, 1.0);

smooth in float brightness;

void main()
{
   vec2 texgrid = fract(gl_TexCoord[0] * 10.0).st;
   float cmix = smoothstep(0.85,0.95,max(texgrid.s, texgrid.t));
   gl_FragColor = mix(paper, ink, cmix) * brightness;
}
"""

GINGHAM_FSHADER = b"""
#version 130
uniform vec4 paper = vec4(1.0);
uniform vec4 ink = vec4(1.0, 0.6, 0.6, 1.0);

smooth in float brightness;

void main()
{
   vec2 texgrid = fract(gl_TexCoord[0] * 10.0).st;
   float cmix = 0.0;
   if (texgrid.s < 0.5) cmix += 0.5;
   if (texgrid.t < 0.5) cmix += 0.5;
   gl_FragColor = mix(paper, ink, cmix) * brightness;
}
"""

EDGES_FSHADER = b"""
#version 130
uniform vec4 paper = vec4(1.0);
uniform vec4 ink = vec4(0.7, 0.7, 0.7, 1.0);

smooth in float brightness;

void main()
{
   vec2 dists = abs(vec4(0.5) - fract(gl_TexCoord[0])).st;
   float cmix = smoothstep(0.4, 0.5, max(dists.s, dists.t));
   gl_FragColor = mix(paper, ink, cmix) * brightness;
}
"""

class TWin:
    def __init__(self, width, height, *args, **kw):
        try:
            self.bg_colour = kw["bg"]
            del kw["bg"]
        except KeyError:
            self.bg_colour = (0,0,0,1)
        w = self.win = pyglet.window.Window(width, height, *args, **kw)
        self.mesh = tnvmesh.make_cuboid(0.5, 0.5, 0.2)
        vshader = Shader(SIMPLE_VSHADER, GL_VERTEX_SHADER)
        gingham = ShaderProgram(vshader, Shader(GINGHAM_FSHADER))
        graph = ShaderProgram(vshader, Shader(GRAPHPAPER_FSHADER))
        edges = ShaderProgram(vshader, Shader(EDGES_FSHADER))
        self.shaders = [gingham, graph, edges]
        self.shaderindex = 0
        self.angle = 0.0
        self.height = 2.0
        w.set_handlers(self.on_draw, self.on_resize, self.on_key_press)

    @property
    def shadprog(self):
        return self.shaders[self.shaderindex]

    def on_resize(self, w, h):
        """ coord system from -1 to 1 with origin in the middle """
        glViewport(0, 0, w, h)
        glMatrixMode(gl.GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, w / max(1.0, float(h)), 0.5, 100.0)
        glMatrixMode(gl.GL_MODELVIEW)
        return pyglet.event.EVENT_HANDLED

    def on_key_press(self, sym, modifiers):
        """ switch shader programs and colours """
        if sym == key.SPACE:
            self.shaderindex = (self.shaderindex + 1) % len(self.shaders)
        elif sym == key.P:
            paper = [1.0, 1.0, 1.0, 1.0]
            paper[random.randint(0,2)] = 0.5 * random.random() + 0.5
            self.shadprog.set(paper=paper)
        elif sym == key.I:
            ink = [0.5, 0.5, 0.5, 1.0]
            ink[random.randint(0,2)] = random.random()
            self.shadprog.set(ink=ink)
        elif sym == key.LEFT:
            self.angle += 5.0
        elif sym == key.RIGHT:
            self.angle -= 5.0
        elif sym == key.UP:
            self.height += 0.1
        elif sym == key.DOWN:
            self.height -= 0.1

    def on_draw(self):
        glEnable(GL_CULL_FACE)
        glEnable(GL_DEPTH_TEST)
        glClearColor(*self.bg_colour)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        gluLookAt(0.0, -1.5, self.height, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0)
        glRotatef(self.angle, 0.0, 0.0, 1.0)
        self.shadprog.use()
        self.mesh.draw()

if __name__ == '__main__':
    try:
        config = Config(#major_version=3, minor_version=0,
            sample_buffers=1, samples=4)
        win = TWin(200,200,caption="Test",bg=(0.4, 0.2, 0.5, 1.0), resizable=True, config=config)
    except (ValueError, pyglet.window.NoSuchConfigException):
        win = TWin(200,200,caption="Test",bg=(0.4, 0.2, 0.5, 1.0), resizable=True)
        print("Preferred config 3.0 with multisampling failed.")
    pyglet.app.run()

