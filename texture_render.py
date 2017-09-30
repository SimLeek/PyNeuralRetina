#todo: take old commit from this repo and build texture renderer from it, 1 per webcam
# todo: take cam input class, and have it give images to glsl bundle
# Todo: have that send an update signal too, to each class that inherits a texture (make a texture msg class?)
#todo: update the renderer upon tex change
#todo: implement rgb hat edge detection
#todo: implement rgb bleeding
#todo: allow bundles to use multiple textures
#todo: feed rgb bleeding back into hat edge detection an only output if a pixel is above bleed enoguh, then increase bleed
#todo: make a prime texture render with rgba and red where primes are, then add that bundle to numpy & display both

import struct

import ModernGL
import numpy as np
import cv2
import os
from typing import Tuple

def get_no_webcam_image(): # type: () -> np.ndarray
    return cv2.imread(os.path.join(os.path.dirname(__file__), 'no_input.jpg'),
                           cv2.IMREAD_COLOR)  # type: np.ndarray

frame = get_no_webcam_image()

class VisionBundle(object):
    pass

class GLSLBundle(VisionBundle):
    def __init__(self, *, context, frame_buffer_1, frame_buffer_2, vertex_array, resolution, program, frag):
        self.context = context  # type: ModernGL.Context
        self.frame_buffer_1 = frame_buffer_1  # type: ModernGL.Framebuffer
        self.frame_buffer_2  = frame_buffer_2  # type: ModernGL.Framebuffer
        self.vertex_array  = vertex_array  # type: ModernGL.VertexArray
        self.resolution = resolution  # type: Tuple[int,int]
        self.program = program  # type: ModernGL.Program
        self.frag = frag  # type: str

        self.texture_in = None  # type: np.ndarray
        pass

    def texture_in_numpy(self, np_array: np.ndarray):
        if self.resolution[0] != np_array.shape[0] and self.resolution[1] != np_array.shape[1]:
            self.resolution = (np_array.shape[0],np_array.shape[1])
            """self.program.release()
            self.program = self.context.program([self.context.vertex_shader('''
                #version 330
                in vec2 vert;
                out vec2 tex_pos;
                void main() {
                    gl_Position = vec4(vert, 0.0, 1.0);
                    tex_pos = vert / 2.0 + vec2(.5, .5);
                }
            '''),
                self.context.fragment_shader(self.frag)
            ])"""

        self.texture_in = self.context.texture((np_array.shape[1], np_array.shape[0]), np_array.shape[2], np_array.tobytes())
        self.texture_in.use()

    @property
    def uniforms(self):
        return self.program.uniforms

    def get_np_image(self):
        self.vertex_array.render(ModernGL.TRIANGLE_STRIP)
        self.context.copy_framebuffer(self.frame_buffer_2, self.frame_buffer_1)
        img = np.frombuffer(self.frame_buffer_2.read(), np.uint8)
        img = np.reshape(img, (self.resolution[0], self.resolution[1], 3))
        return img

    @staticmethod
    def from_fragment_shader(fragment_shader, **named_args):
        size = frame.shape[1], frame.shape[0]
        ctx = ModernGL.create_standalone_context()

        color_rbo = ctx.renderbuffer(size)
        depth_rbo = ctx.depth_renderbuffer(size)
        fbo = ctx.framebuffer(color_rbo, depth_rbo)

        fbo.use()

        prog = ctx.program([
            ctx.vertex_shader('''
                        #version 330
                        in vec2 vert;
                        out vec2 tex_pos;
                        void main() {
                            gl_Position = vec4(vert, 0.0, 1.0);
                            tex_pos = vert / 2.0 + vec2(.5, .5);
                        }
                    '''),
            ctx.fragment_shader(fragment_shader)
        ])

        for name, value in named_args.items():
            prog.uniforms[name].value = value

        vbo = ctx.buffer(struct.pack('8f', -1.0, -1.0, -1.0, 1.0, 1.0, -1.0, 1.0, 1.0))
        vao = ctx.simple_vertex_array(prog, vbo, ['vert'])

        color_rbo2 = ctx.renderbuffer(size)
        depth_rbo2 = ctx.depth_renderbuffer(size)
        fbo2 = ctx.framebuffer(color_rbo2, depth_rbo2)
        # ctx.copy_framebuffer(fbo2, fbo)

        return GLSLBundle(context=ctx, frame_buffer_1=fbo, frame_buffer_2=fbo2, vertex_array=vao, resolution=size,
                          program=prog, frag=fragment_shader)


file = open('retina.glsl', 'r')
text = file.read()
file.close()

ren = GLSLBundle.from_fragment_shader(text)

ren.texture_in_numpy(frame)
img = ren.get_np_image()



frame = frame.swapaxes(0,1)
ren.texture_in_numpy(frame)

img2 = ren.get_np_image()


#img = img.transpose()
#img.('Fractal.png')

from matplotlib import pyplot as plt
plt.imshow(img, interpolation='nearest')
plt.show()
plt.imshow(img2, interpolation='nearest')
plt.show()