"""
 Simple mesh object

 Contains:
 * A buffer of floats, holding interleaved attribute data.
   This will always include vertex data but might also have texture coords and
   normals.
 * Some pieces of mesh that can be drawn.

 Pieces consist of:
 * A buffer of indices into the attribute buffer.
 * A primitive type (usually GL_TRIANGLES) to be used to render the
   shape.

"""
from pyglet.gl import *
from ctypes import byref, cast, POINTER
from math import sin, cos, pi
from functools import partial

class TNVMesh:
    def __init__(self, vertexdata, order='V', pieces=None):
        self.order = order
        self.vbuf = GLuint(0)
        glGenBuffers(1, byref(self.vbuf))
        self.stride = 0
        self.enables = []
        offset = 0
        # calculate total size of data for each vertex
        sizes = {"T":8, "U":8,
                 "V":12, "N":12}
        array_types = {"V":GL_VERTEX_ARRAY,
                       "T":GL_TEXTURE_COORD_ARRAY,
                       "U":GL_TEXTURE_COORD_ARRAY,
                       "N":GL_NORMAL_ARRAY}
        texture_units = {"T":GL_TEXTURE0, "U":GL_TEXTURE1}
        self.stride = sum(sizes[c] for c in order)
        # calculate offset in interleaved data for each array
        offsets = {}
        for c in order:
            offsets[c] = offset
            offset += sizes[c]
        assert self.stride == offset
        # build a list of functions to call before drawing
        def addfun(*args):
            self.enables.append(partial(*args))
        for k in sizes:
            used = k in order
            enableDisable = glEnableClientState if used else glDisableClientState
            if k in texture_units:
                # specify which texture array we are talking about
                addfun(glClientActiveTexture, texture_units[k])
            if used:
                if k == 'V':
                    addfun(glVertexPointer, 3, GL_FLOAT, self.stride, offsets[k])
                elif k == 'T':
                    addfun(glTexCoordPointer, 2, GL_FLOAT, self.stride, offsets[k])
                elif k == 'U': # second set of texture coords
                    addfun(glTexCoordPointer, 2, GL_FLOAT, self.stride, offsets[k])
                elif k == 'N':
                    addfun(glNormalPointer, GL_FLOAT, self.stride, offsets[k])
            addfun(enableDisable, array_types[k]) # enable or disable array

        data = (GLfloat*len(vertexdata))()
        for i,f in enumerate(vertexdata):
            data[i] = f
        glBindBuffer(GL_ARRAY_BUFFER, self.vbuf)
        glBufferData(GL_ARRAY_BUFFER, len(data) * 4, byref(data), GL_STATIC_DRAW)
        self.nvertices = (len(vertexdata) * 4) // self.stride
        self.pieces = {}
        if pieces:
            self.pieces.update(pieces)

    def __del__(self):
        glDeleteBuffers(1, byref(self.vbuf))

    def add_piece(self, name, piece):
        self.pieces[name] = piece

    def draw(self, pieces=None):
        if pieces is None:
            todraw = self.pieces.values()
        else:
            todraw = [self.pieces[k] for k in pieces if k in self.pieces]
        if not todraw:
            return
        glBindBuffer(GL_ARRAY_BUFFER, self.vbuf)
        glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
        try:
            for f in self.enables:
                f()
            for p in todraw:
                p.draw()
        finally:
            glPopClientAttrib()

class TNVPiece:
    def __init__(self, indices, primitive=GL_TRIANGLES):
        self.prim = primitive
        self.ibuf = GLuint(0)
        glGenBuffers(1, byref(self.ibuf))
        data = (GLushort*len(indices))()
        for i,j in enumerate(indices):
            data[i] = j
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ibuf)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, len(indices)*2, byref(data), GL_STATIC_DRAW)
        self.nindices = len(indices)

    def __del__(self):
        glDeleteBuffers(1, byref(self.ibuf))

    def draw(self):
        """ only makes sense inside TNVMesh.draw() where array buffer has been bound """
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ibuf)
        glDrawElements(self.prim, self.nindices, GL_UNSIGNED_SHORT, 0)



def make_cuboid(dx, dy, dz):
    """ make a TNVMesh with a single piece called "cuboid" made of GL_QUADS 
      centered on the origin, with width 2*dx, length 2*dy, height 2*dz.

      Texture coords 0 are scaled with the cuboid size
      Texture coords 1 are 0-1 on each face regardless of size
    """
    order = 'VNT'
    vdata = [
    #Vx   Vy   Vz  Nx  Ny  Nz Ts Tt
    -dx, -dy, -dz,  0, -1,  0, 0, 0, # front
     dx, -dy, -dz,  0, -1,  0, 1, 0,
     dx, -dy,  dz,  0, -1,  0, 1, 1,
    -dx, -dy,  dz,  0, -1,  0, 0, 1,
     dx, -dy, -dz,  1,  0,  0, 0, 0, # right
     dx,  dy, -dz,  1,  0,  0, 1, 0,
     dx,  dy,  dz,  1,  0,  0, 1, 1,
     dx, -dy,  dz,  1,  0,  0, 0, 1,
     dx,  dy, -dz,  0,  1,  0, 0, 0, # back
    -dx,  dy, -dz,  0,  1,  0, 1, 0,
    -dx,  dy,  dz,  0,  1,  0, 1, 1,
     dx,  dy,  dz,  0,  1,  0, 0, 1,
    -dx,  dy, -dz, -1,  0,  0, 0, 0, # left
    -dx, -dy, -dz, -1,  0,  0, 1, 0,
    -dx, -dy,  dz, -1,  0,  0, 1, 1,
    -dx,  dy,  dz, -1,  0,  0, 0, 1,
    -dx, -dy,  dz,  0,  0,  1, 0, 0, # top
     dx, -dy,  dz,  0,  0,  1, 1, 0,
     dx,  dy,  dz,  0,  0,  1, 1, 1,
    -dx,  dy,  dz,  0,  0,  1, 0, 1,
    -dx,  dy, -dz,  0,  0, -1, 0, 0, # bottom
     dx,  dy, -dz,  0,  0, -1, 1, 0,
     dx, -dy, -dz,  0,  0, -1, 1, 1,
    -dx, -dy, -dz,  0,  0, -1, 0, 1
    ]
    QUAD_CUBOID_PIECE = TNVPiece(range(24), GL_QUADS)
    return TNVMesh(vdata, order, dict(cuboid=QUAD_CUBOID_PIECE))

