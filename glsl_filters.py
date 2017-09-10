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
    sig = QtCore.pyqtSignal(np.ndarray)
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

        self.sig.connect(parent.update_frame)

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
                self.sig.emit(frame_list[0])


class QGLWidget(QtOpenGL.QGLWidget):
    exit_sig = QtCore.pyqtSignal()

    def __init__(self):
        logging.debug("QGLWidget __init__ entered")
        self.tex = None  # type: ModernGL.Texture
        self.set_frame_shape = None  # type: Tuple[int]
        self.progs = None  # type: ModernGL.Program
        self.barrel_amount = int
        self.ctx = None  # type: ModernGL.Context
        self.vao = None  # type: ModernGL.VertexArray


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
    def update_frame(self, frame):
        logging.debug("update_frames entered")
        if frame.shape[0] == self.set_frame_shape[0] and frame.shape[1] == self.set_frame_shape[1]:
            self.tex.write(frame.tobytes())
        else:
            #self.release_gl()
            self.init_gl(frame)

    def release_gl(self):
        logging.debug("release_gl entered")
        if not isinstance(self.ctx, ModernGL.InvalidObject):
            logging.debug("context was valid")
            self.ctx.release()
            logging.debug("context released")
            self.tex.release()
            logging.debug("tex released")
            self.progs.release()
            logging.debug("progs released")

    def init_gl(self, frame):
        logging.debug("init_gl entered")

        self.tex = None  # type: ModernGL.Texture
        self.set_frame_shape = None  # type: Tuple[int]
        self.progs = None  # type: ModernGL.Program
        self.barrel_amount = int
        self.ctx = None  # type: ModernGL.Context
        self.vao = None  # type: ModernGL.VertexArray

        vbo : ModernGL.Buffer = None

        logging.debug("frame entered")
        self.ctx = ModernGL.create_context()
        self.ctx.enable(ModernGL.DEPTH_TEST)
        logging.debug("context made")

        vbo = (self.ctx.buffer(struct.pack(
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
        self.tex = (self.ctx.texture((frame.shape[1], frame.shape[0]), frame.shape[2], frame.tobytes()))

        self.set_frame_shape = (frame.shape)

        self.tex.use()

        logging.debug("tex made")

        self.prog = (self.ctx.program([
            self.ctx.vertex_shader('''
                        #version 330
                        in vec2 vert;
                        in vec2 tex_coord;
                        out vec2 v_tex_coord;
                        void main() {
                            gl_Position = vec4(vert, 0.0, 1.0);
                            v_tex_coord = tex_coord;
                        }
                    '''),
            self.ctx.fragment_shader('''
                        #version 330
                        uniform sampler2D tex;
                        in vec2 v_tex_coord;
                        out vec4 color;

                        void main() {
                            //vec2 new_coord = fisheye(v_tex_coord, barrel_amount);
                            //vec2 new_coord = v_tex_coord;
                            color = vec4( texture(tex, v_tex_coord).bgr, 1.0);

                        }
                    ''' )
        ]))

        logging.debug("prog made")


        #self.prog.uniforms['tex'].value = (0)

        logging.debug("tex set")

        logging.debug("barrel set")

        self.vao = self.ctx.simple_vertex_array(self.prog, vbo, ['vert', 'tex_coord'])

        logging.debug("vao made")

    def initializeGL(self):
        logging.debug("initializeGL entered")
        frame = cv2.imread(os.path.join(os.path.dirname(__file__), 'no_input.jpg'),
                           cv2.IMREAD_COLOR)  # type: np.ndarray
        self.init_gl(frame)

        self.cam_thread.start()

    def paintGL(self):
        logging.debug("paintGL entered")

        frame_width = self.set_frame_shape[1]
        frame_height = self.set_frame_shape[0]

        if not isinstance(self.ctx, ModernGL.InvalidObject):
            self.ctx.viewport = (0, 0, self.set_frame_shape[1], self.set_frame_shape[0])
            self.ctx.clear(0.9, 0.9, 0.9)
            self.vao.render()
            self.ctx.finish()
        else:
            return

        self.update()


app = QtWidgets.QApplication([])
window = QGLWidget()
# window.move(QtWidgets.QDesktopWidget().rect().center() - window.rect().center())
window.resize(1280, 720)
window.show()
app.exec_()
