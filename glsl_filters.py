import numpy as np

from get_webcams import *

import ModernGL
from PyQt5 import QtCore, QtOpenGL, QtWidgets, QtGui
from PyQt5.QtCore import pyqtSlot
import os
import cv2
import time
import struct
import threading


# from https://stackoverflow.com/a/20663028/782170
import argparse
import logging

parser = argparse.ArgumentParser()
parser.add_argument(
    '-d', '--debug',
    help="Print lots of debugging statements",
    action="store_const", dest="loglevel", const=logging.DEBUG,
    default=logging.WARNING,
)
parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    action="store_const", dest="loglevel", const=logging.INFO,
)
args = parser.parse_args()
#logging.basicConfig(level=args.loglevel)

#for now...
logging.basicConfig(level=logging.DEBUG)

class CamInputThread(QtCore.QThread):
    # thanks: https://stackoverflow.com/a/40537178
    sig = QtCore.pyqtSignal(list)
    fps = 60
    retry_seconds = 2.0

    e = threading.Event()

    def __init__(self,
                 parent  # type: QGLWidget
                 ):

        logging.debug("Initializing Cam Input Thread")
        super(CamInputThread, self).__init__(parent)

        self.previous_fps_time = time.time()
        self.previous_cam_retry_time = time.time()
        self.current_fps_time = None
        self.current_cam_retry_time = None

        self.exiting = False

        self.parent = parent

        self.sig.connect(parent.update_frames)

        self.cam_list = make_camlist()
        # todo: handle different resolutions
        # self.cam_list[0].set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        # self.cam_list[0].set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        # self.cam_list[0].set(cv2.CAP_PROP_FPS, 60)

    def fps_limit(self):
        logging.debug("fps_limit entered")
        self.current_fps_time = time.time()
        if (self.current_fps_time - self.previous_fps_time) < (1.0 / self.fps):  # limit to max fps
            print("fps_limit: ", self.current_fps_time)
            self.e.wait(1.0 / self.fps - (self.current_fps_time - self.previous_fps_time))
        self.previous_fps_time = self.current_fps_time

    def cam_retry_limit(self):
        logging.debug("cam_retry_limit entered")
        self.current_cam_retry_time = time.time()
        if (self.current_cam_retry_time - self.previous_cam_retry_time) < (
            1.0 / self.retry_seconds):  # limit to max fps
            print("Retrying cams again in ", self.retry_seconds)
            self.e.wait(1.0 / self.fps - (self.current_cam_retry_time - self.previous_cam_retry_time))
        self.previous_cam_retry_time = self.current_cam_retry_time

    def got_frames(self, frame_list):
        logging.debug("got_frames entered")
        got_them = len(frame_list) != 0

        if not got_them:
            self.cam_retry_limit()
            self.cam_list = make_camlist()

        return got_them

    def set_exiting(self):
        #logging.debug("set_exiting entered")
        self.exiting = True

    def run(self):
        logging.debug("run entered")
        while not self.exiting:
            self.fps_limit()

            frame_list = capture_cams(self.cam_list)

            if (self.got_frames(frame_list)):
                self.sig.emit(frame_list)


class QGLWidget(QtOpenGL.QGLWidget):
    exit_sig = QtCore.pyqtSignal()

    def __init__(self):
        logging.debug("QGLWidget __init__ entered")
        self.tex = []  # type: List[ModernGL.Texture]
        self.set_frame_shapes = []  # type: List[Tuple[int]]
        self.progs = []  # type: List[ModernGL.Program]
        self.barrel_amounts = []
        self.ctx = []  # type: List[ModernGL.Context]
        self.vao = []  # type: List[ModernGL.VertexArray]


        fmt = QtOpenGL.QGLFormat()
        fmt.setVersion(4, 1)
        fmt.setProfile(QtOpenGL.QGLFormat.CoreProfile)
        fmt.setSampleBuffers(True)

        self.timer = QtCore.QElapsedTimer()
        self.timer.restart()
        super(QGLWidget, self).__init__(fmt, None)
        self.cam_thread = CamInputThread(self)

        self.exit_sig.connect(self.cam_thread.set_exiting)

    def keyPressEvent(self, event):
        logging.debug("keyPressEvent entered")
        if type(event) == QtGui.QKeyEvent and not event.isAutoRepeat():
            if event.key() == QtCore.Qt.Key_Escape:
                self.release_gl()
                logging.debug("gl released")
                self.exit_sig.emit()
                logging.debug("exit sig emitted")
                self.close()

    # @pyqtSlot(list)
    def update_frames(self,
                      frame_list  # type: List[np.ndarray]
                      ):
        logging.debug("update_frames entered")
        if all(frame_list[i].shape == self.set_frame_shapes[i] for i in range(len(frame_list))):
            for f in range(len(frame_list)):
                self.tex[f].write(frame_list[f].tobytes())
        else:
            self.release_gl()
            self.init_gl(frame_list)

    def release_gl(self):
        logging.debug("release_gl entered")
        for i in range(len(self.ctx)):
            logging.debug("releasing context " +str(i))
            if not isinstance(self.ctx[i], ModernGL.InvalidObject):
                logging.debug("context was valid")
                self.ctx[i].release()
                logging.debug("context released")
                self.tex[i].release()
                logging.debug("tex released")
                self.progs[i].release()
                logging.debug("progs released")

    def init_gl(self, frames):
        logging.debug("init_gl entered")

        self.tex[:] = []  # type: List[ModernGL.Texture]
        self.set_frame_shapes[:] = []  # type: List[Tuple[int]]
        self.progs[:] = []  # type: List[ModernGL.Program]
        self.barrel_amounts[:] = []
        self.ctx[:] = []  # type: List[ModernGL.Context]
        self.vao[:] = []  # type: List[ModernGL.VertexArray]

        vbo = []

        for frame in frames:
            logging.debug("frame"+str(len(self.ctx)+1) + "entered")
            self.ctx.append(ModernGL.create_context())
            self.ctx[-1].enable(ModernGL.DEPTH_TEST)
            logging.debug("context made")

            vbo.append(self.ctx[-1].buffer(struct.pack(
                '24f',
                -1.0, -1.0, 0.0, 1.0,
                -1.0, 1.0, 0.0, 0.0,
                1.0, 1.0, 1.0, 0.0,
                1.0, -1.0, 1.0, 1.0,
                -1.0, -1.0, 0.0, 1.0,
                1.0, 1.0, 1.0, 0.0,

            )))
            logging.debug("vbo made")

            # todo: allow resetting of tex for different sizes (close and reopen tex)
            self.tex.append(self.ctx[-1].texture((frame.shape[1], frame.shape[0]), frame.shape[2], frame.tobytes()))

            self.set_frame_shapes.append(frame.shape)

            self.tex[-1].use(location = len(self.ctx) - 1)

            logging.debug("tex made")

            self.progs.append(self.ctx[-1].program([
                self.ctx[-1].vertex_shader('''
                            #version 330
                            in vec2 vert;
                            in vec2 tex_coord;
                            out vec2 v_tex_coord;
                            void main() {
                                gl_Position = vec4(vert, 0.0, 1.0);
                                v_tex_coord = tex_coord;
                            }
                        '''),
                self.ctx[-1].fragment_shader('''
                            #version 330
                            uniform sampler2D tex0;
                            uniform sampler2D tex1;
                            uniform float barrel_amount;
                            in vec2 v_tex_coord;
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
                                vec2 new_coord = fisheye(v_tex_coord, barrel_amount);
                                //vec2 new_coord = v_tex_coord;
                                color = vec4( texture(tex%d, new_coord).bgr, 1.0);
    
                            }
                        ''' % (len(self.ctx)-1))
            ]))

            logging.debug("prog made")


            self.progs[-1].uniforms['tex%d'% (len(self.ctx)-1)].value = (len(self.ctx)-1)

            logging.debug("tex set")

            self.barrel_amounts.append(self.progs[-1].uniforms['barrel_amount'])
            self.barrel_amounts[-1].value = 2

            logging.debug("barrel set")

            self.vao.append(self.ctx[-1].simple_vertex_array(self.progs[-1], vbo[-1], ['vert', 'tex_coord']))

            logging.debug("vao made")

    def initializeGL(self):
        logging.debug("initializeGL entered")
        frame = cv2.imread(os.path.join(os.path.dirname(__file__), 'no_input.jpg'),
                           cv2.IMREAD_COLOR)  # type: np.ndarray
        self.init_gl([frame])

        self.cam_thread.start()

    def paintGL(self):
        logging.debug("paintGL entered")
        total_width = 0
        for i in range(len(self.ctx)):
            total_width += self.set_frame_shapes[i][1]

        width_mult = self.width() / total_width

        '''total_height = 0
        for i in range(len(self.ctx)):
            total_height = max(total_height,self.set_frame_shapes[i][0]*width_mult)
        
        height_mult = self.height() / total_height'''

        current_x = 0

        for i in range(len(self.ctx)):
            if not isinstance(self.ctx[i], ModernGL.InvalidObject):
                self.ctx[i].viewport = (current_x, 0, current_x + self.set_frame_shapes[i][1]*width_mult, self.set_frame_shapes[i][0]*width_mult)
                current_x += self.set_frame_shapes[i][1]*width_mult
                self.ctx[i].clear(0.9, 0.9, 0.9, viewport=self.ctx[i].viewport)
                self.vao[i].render()
                self.ctx[i].finish()
            else:
                return

        self.update()


app = QtWidgets.QApplication([])
window = QGLWidget()
# window.move(QtWidgets.QDesktopWidget().rect().center() - window.rect().center())
window.resize(1280, 720)
window.show()
app.exec_()
