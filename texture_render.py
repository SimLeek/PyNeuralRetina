#todo: make bundle output that gives one val with all needed data
#todo: take that output from numpy, back into another renderer, and output to screen.
#todo: make a prime texture render with rgba and red where primes are, then add that bundle to numpy & display both

import struct

import ModernGL
import numpy as np
import cv2
import os

def get_no_webcam_image():
    # type: () -> np.ndarray
    return cv2.imread(os.path.join(os.path.dirname(__file__), 'no_input.jpg'),
                           cv2.IMREAD_COLOR)  # type: np.ndarray

frame = get_no_webcam_image()

class RenderBundle():
    def __init__(self, *, context, frame_buffer_1, frame_buffer_2, vertex_array, resolution):
        self.context = context
        self.frame_buffer_1 = frame_buffer_1
        self.frame_buffer_2 = frame_buffer_2
        self.vertex_array = vertex_array
        self.resolution = resolution
        pass

    def get_np_image(self):
        self.vertex_array.render(ModernGL.TRIANGLE_STRIP)
        self.context.copy_framebuffer(self.frame_buffer_2, self.frame_buffer_1)
        img = np.frombuffer(self.frame_buffer_2.read(), np.uint8)
        img = np.reshape(img, (self.resolution[1], self.resolution[0], 3))
        return img

def frag_to_render_bundle(*, frag):
    # type: (str) -> RenderBundle
    size = frame.shape[1], frame.shape[0]
    ctx = ModernGL.create_standalone_context()

    color_rbo = ctx.renderbuffer(size, samples=ctx.max_samples)
    depth_rbo = ctx.depth_renderbuffer(size, samples=ctx.max_samples)
    fbo = ctx.framebuffer(color_rbo, depth_rbo)

    fbo.use()

    prog = ctx.program([
        ctx.vertex_shader('''
                #version 330
                in vec2 vert;
                out vec2 tex_pos;
                void main() {
                    gl_Position = vec4(vert, 0.0, 1.0);
                    tex_pos = vert / 2.0;
                }
            '''),
        ctx.fragment_shader(frag)
    ])

    vbo = ctx.buffer(struct.pack('8f', -1.0, -1.0, -1.0, 1.0, 1.0, -1.0, 1.0, 1.0))
    vao = ctx.simple_vertex_array(prog, vbo, ['vert'])

    color_rbo2 = ctx.renderbuffer(size)
    depth_rbo2 = ctx.depth_renderbuffer(size)
    fbo2 = ctx.framebuffer(color_rbo2, depth_rbo2)
    #ctx.copy_framebuffer(fbo2, fbo)

    return RenderBundle(context=ctx, frame_buffer_1=fbo, frame_buffer_2=fbo2, vertex_array=vao, resolution=size)

ren = frag_to_render_bundle(frag = '''
                #version 330
                uniform sampler2D tex;
                in vec2 tex_pos;
                out vec4 color;
                void main() {
                    float d = pow(distance(vec2(0, 0), tex_pos),.5);
                    //color = vec4(1-abs(d)/sqrt(.5), 0.0, 0.0, 1.0);
                    color = vec4( texture(tex, tex_pos).bgr, 1.0);
                }
            ''')

img = ren.get_np_image()


#img = img.transpose()
#img.('Fractal.png')

from matplotlib import pyplot as plt
plt.imshow(img, interpolation='nearest')
plt.show()