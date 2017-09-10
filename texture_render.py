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

def get_no_webcam_image() -> np.ndarray:
    return cv2.imread(os.path.join(os.path.dirname(__file__), 'no_input.jpg'),
                           cv2.IMREAD_COLOR)  # type: np.ndarray

frame = get_no_webcam_image()

class VisionBundle(object):
    pass

class GLSLBundle(VisionBundle):
    def __init__(self, *, context, frame_buffer_1, frame_buffer_2, vertex_array, resolution, program, frag):
        self.context : ModernGL.Context = context
        self.frame_buffer_1 : ModernGL.Framebuffer = frame_buffer_1
        self.frame_buffer_2 : ModernGL.Framebuffer = frame_buffer_2
        self.vertex_array : ModernGL.VertexArray = vertex_array
        self.resolution : Tuple[int,int]= resolution
        self.program : ModernGL.Program = program
        self.frag : str = frag

        self.texture_in : np.ndarray = None
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

ren = GLSLBundle.from_fragment_shader('''
                #version 330
                uniform sampler2D tex;
                in vec2 tex_pos;
                out vec4 color;
                
                vec2 fisheye(vec2 in_pos, float amount){
                        //from: https://stackoverflow.com/a/6227310

                        vec2 center_xform_vec = vec2(0.5, 0.5);
                        float center_xform_vec_len = length(center_xform_vec);
                        vec2 r = (in_pos - center_xform_vec);
                        float r_len = length(r);
                        vec2 barrel_vec = (r * (1+ amount * r_len * r_len));

                        float barrel_max = (sqrt(1+(720.0/1280.0)*(720.0/1280.0)) * (1+abs(amount)*center_xform_vec_len*center_xform_vec_len));
                        vec2 barrel_norm = barrel_vec/barrel_max + .5;

                        return barrel_norm;
                    }
                
                void main() {
                    //float d = pow(distance(vec2(0, 0), tex_pos),.5);
                    vec2 new_coord = fisheye(tex_pos, 2.0);
                    //color = vec4(1-abs(d)/sqrt(.5), 0.0, 0.0, 1.0);
                    color = vec4( texture(tex, new_coord).bg, 0.5, 1.0);
                }
            ''')

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