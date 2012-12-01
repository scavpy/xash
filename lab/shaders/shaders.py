"""

Simplistic Shader and ShaderProgram objects

"""

from pyglet.gl import *
from ctypes import cast, byref, POINTER, c_char_p, c_char, create_string_buffer

class GLobject:
    def intval(self, param):
        res = GLint(0)
        self.get_int_fn(self.id, param, byref(res))
        return res.value

    def infolog(self):
        length = self.intval(GL_INFO_LOG_LENGTH)
        if length:
            buf = create_string_buffer(length)
            self.get_info_log_fn(self.id, length, None, buf)
            return buf.value
        return ''

class Shader(GLobject):
    get_int_fn = glGetShaderiv
    get_info_log_fn = glGetShaderInfoLog

    def __init__(self, source, shadertype=GL_FRAGMENT_SHADER):
        self.id = glCreateShader(shadertype)
        self.source = source
        sourceptr = c_char_p(source)
        glShaderSource(self.id, 1, cast(byref(sourceptr), POINTER(POINTER(c_char))), None)
        glCompileShader(self.id)
        self.status = bool(self.intval(GL_COMPILE_STATUS))
        self.log = self.infolog()
        if not self.status:
            raise RuntimeError(self.log)

class ShaderProgram(GLobject):
    get_int_fn = glGetProgramiv
    get_info_log_fn = glGetProgramInfoLog

    def __init__(self, *shaders):
        self.id = glCreateProgram()
        for shader in shaders:
            glAttachShader(self.id, shader.id)
        glLinkProgram(self.id)
        self.status = bool(self.intval(GL_LINK_STATUS))
        self.log = self.infolog()
        if not self.status:
            raise RuntimeError(self.log)
        self.uniforms = {}

    def use(self):
        glUseProgram(self.id)

    def set(self, **uniforms):
        for name, val in uniforms.items():
            num = self.uniforms.get(name)
            if num is None:
                nbuf = create_string_buffer(name.encode("ascii"))
                num = glGetUniformLocation(self.id, cast(nbuf, POINTER(c_char)))
                self.uniforms[name] = num
            glUniform4f(num, *val)
