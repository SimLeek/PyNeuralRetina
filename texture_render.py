#todo: make bundle output that gives one val with all needed data
#todo: take that output from numpy, back into another renderer, and output to screen.
#todo: make a prime texture render with rgba and red where primes are, then add that bundle to numpy & display both

import struct

import ModernGL
import numpy as np
size = 512, 512
ctx = ModernGL.create_standalone_context()

color_rbo = ctx.renderbuffer(size, samples=ctx.max_samples)
depth_rbo = ctx.depth_renderbuffer(size, samples=ctx.max_samples)
fbo = ctx.framebuffer(color_rbo, depth_rbo)

fbo.use()

prog = ctx.program([
    ctx.vertex_shader('''
        #version 330
        in vec2 vert;
        out vec2 tex;
        void main() {
            gl_Position = vec4(vert, 0.0, 1.0);
            tex = vert / 2.0;
        }
    '''),
    ctx.fragment_shader('''
        #version 330
        in vec2 tex;
        out vec4 color;
        void main() {
            float d = pow(distance(vec2(0, 0), tex),.5);
            color = vec4(1-abs(d)/sqrt(.5), 0.0, 0.0, 1.0);
        }
    ''')
])

vbo = ctx.buffer(struct.pack('8f', -1.0, -1.0, -1.0, 1.0, 1.0, -1.0, 1.0, 1.0))
vao = ctx.simple_vertex_array(prog, vbo, ['vert'])

vao.render(ModernGL.TRIANGLE_STRIP)

color_rbo2 = ctx.renderbuffer(size)
depth_rbo2 = ctx.depth_renderbuffer(size)
fbo2 = ctx.framebuffer(color_rbo2, depth_rbo2)
ctx.copy_framebuffer(fbo2, fbo)

img = np.frombuffer(fbo2.read(), np.uint8)
img = np.reshape(img, (512, 512, 3))
#img = img.transpose()
#img.('Fractal.png')

from matplotlib import pyplot as plt
plt.imshow(img, interpolation='nearest')
plt.show()