#!/usr/bin/env python3
"""
 Open a window and clear it to a specified colour.
 Draw a rectangle in the middle with various possible
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
void main()
{
  gl_Position = ftransform();
  gl_TexCoord[0] = gl_MultiTexCoord0;
}
"""

GRAPHPAPER_FSHADER = b"""
uniform vec4 paper = vec4(1.0, 1.0, 0.95, 1.0);
uniform vec4 ink = vec4(0.6, 0.9, 1.0, 1.0);

void main()
{
   vec2 texgrid = fract(gl_TexCoord[0] * 10.0).st;
   if (any(lessThan(texgrid,vec2(0.1))))
      gl_FragColor = ink;
   else
      gl_FragColor = paper;
}
"""

GINGHAM_FSHADER = b"""
uniform vec4 paper = vec4(1.0);
uniform vec4 ink = vec4(1.0, 0.6, 0.6, 1.0);

void main()
{
   vec2 texgrid = fract(gl_TexCoord[0] * 10.0).st;
   float cmix = 0.0;
   if (texgrid.s < 0.5) cmix += 0.5;
   if (texgrid.t < 0.5) cmix += 0.5;
   gl_FragColor = mix(paper, ink, cmix);
}
"""

EDGES_FSHADER = b"""
uniform vec4 paper = vec4(1.0);
uniform vec4 ink = vec4(0.7, 0.7, 0.7, 1.0);

void main()
{
   vec2 dists = abs(vec4(0.5) - fract(gl_TexCoord[0])).st;
   float cmix = smoothstep(0.4, 0.5, max(dists.s, dists.t));
   gl_FragColor = mix(paper, ink, cmix);
}
"""

class Mesh:
    def __init__(self, vertexdata, indices=None, contains_texture=False, primitive=GL_TRIANGLES):
        self.bufs = (GLuint*2)()
        glGenBuffers(2, cast(self.bufs, POINTER(GLuint)))
        vbuf, ibuf = self.bufs
        self.prim = primitive
        T = GLfloat * len(vertexdata)
        data = T(*vertexdata)
        glBindBuffer(GL_ARRAY_BUFFER, vbuf)
        glBufferData(GL_ARRAY_BUFFER, len(data) * 4, byref(data), GL_STATIC_DRAW)
        self.pervertex = 3
        self.vtexture = contains_texture
        if contains_texture:
            self.pervertex = 5
        self.nvertices = len(vertexdata) // self.pervertex
        if indices is None:
            indices = range(self.nvertices)
        self.nindices = len(indices)
        T = GLushort * len(indices)
        idata = T(*indices)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ibuf)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(idata) * 2, byref(idata), GL_STATIC_DRAW)

    def __del__(self):
        glDeleteBuffers(2, cast(self.bufs, POINTER(GLuint)))

    def draw(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.bufs[0])
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.bufs[1])
        stride = 20 if self.vtexture else 0
        glVertexPointer(3, GL_FLOAT, stride, 0)
        if self.vtexture:
            glTexCoordPointer(2, GL_FLOAT, stride, 12)
            glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glEnableClientState(GL_VERTEX_ARRAY)
        glDrawElements(self.prim, self.nindices, GL_UNSIGNED_SHORT, 0)


class TWin:
    def __init__(self, width, height, *args, **kw):
        try:
            self.bg_colour = kw["bg"]
            del kw["bg"]
        except KeyError:
            self.bg_colour = (0,0,0,1)
        w = self.win = pyglet.window.Window(width, height, *args, **kw)
        self.mesh = Mesh(
            (-0.5, -0.5, 0.0, 0.0, 0.0,
              0.5, -0.5, 0.0, 1.0, 0.0,
              0.5,  0.5, 0.0, 1.0, 1.0,
             -0.5,  0.5, 0.0, 0.0, 1.0), contains_texture=True, primitive=GL_QUADS)
#        self.mesh = tnvmesh.make_cuboid(0.5, 0.5, 0.2)
        vshader = Shader(SIMPLE_VSHADER, GL_VERTEX_SHADER)
        gingham = ShaderProgram(vshader, Shader(GINGHAM_FSHADER))
        graph = ShaderProgram(vshader, Shader(GRAPHPAPER_FSHADER))
        edges = ShaderProgram(vshader, Shader(EDGES_FSHADER))
        self.shaders = [gingham, graph, edges]
        self.shaderindex = 0
        w.set_handlers(self.on_draw, self.on_resize, self.on_key_press)

    @property
    def shadprog(self):
        return self.shaders[self.shaderindex]

    def on_resize(self, w, h):
        """ coord system from -1 to 1 with origin in the middle """
        glViewport(0, 0, w, h)
        glMatrixMode(gl.GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
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

    def on_draw(self):
        glClearColor(*self.bg_colour)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glRectf(10, 10, 20, 20)
        self.shadprog.use()
        self.mesh.draw()

if __name__ == '__main__':
    win = TWin(200,200,caption="Test",bg=(0.4, 0.2, 0.5, 1.0), resizable=True)
    pyglet.app.run()

