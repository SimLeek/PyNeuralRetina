import struct
import time

import ModernGL
from PyQt5 import QtCore, QtOpenGL, QtWidgets

from get_webcams import *
import os


class CamInputThread(QtCore.QThread):
    # thanks: https://stackoverflow.com/a/40537178
    sig = QtCore.pyqtSignal(list)
    fps = 60

    def __init__(self,
                 parent # type: QGLWidget
                 ):
        super(CamInputThread, self).__init__(parent)

        self.previous_time = time.time()
        self.current_time = None

        self.sig.connect(parent.update_frames)

        self.cam_list = make_camlist()

    def run(self):
        while True:
            self.current_time = time.time()

            if self.current_time - self.previous_time < 1.0/self.fps: # limit to max fps
                self.wait(1.0/self.fps - (self.current_time - self.previous_time))

            frame_list = capture_cams(self.cam_list)
            self.sig.emit(frame_list)

            self.previous_time = self.current_time

class QGLWidget(QtOpenGL.QGLWidget):
    def __init__(self):
        fmt = QtOpenGL.QGLFormat()
        fmt.setVersion(4, 1)
        fmt.setProfile(QtOpenGL.QGLFormat.CoreProfile)
        fmt.setSampleBuffers(True)

        self.timer = QtCore.QElapsedTimer()
        self.timer.restart()
        super(QGLWidget, self).__init__(fmt, None)
        self.cam_thread = CamInputThread(self)

    #@pyqtSlot(list)
    def update_frames(self,
                      frame_list # type: List[np.ndarray]
                      ):
        self.texture.write(frame_list[0].tobytes())

    def initializeGL(self):
        self.ctx = ModernGL.create_context()
        self.ctx.enable(ModernGL.DEPTH_TEST)

        frame = cv2.imread(os.path.join(os.path.dirname(__file__), 'no_input.jpg'), cv2.IMREAD_COLOR) # type: np.ndarray

        self.texture = self.ctx.texture((frame.shape[0],frame.shape[1]), frame.shape[2], frame.tobytes())

        #self.texture.use()
        file = open('retina.glsl', 'r')
        text = file.read()
        file.close()

        prog = self.ctx.program([
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
            self.ctx.fragment_shader(text),
        ])

        vbo = self.ctx.buffer(struct.pack(
            '24f',
            -1.0, -1.0, 0.0, 1.0,
            -1.0,  1.0, 0.0,  0.0,
             1.0,  1.0,  1.0,  0.0,
             1.0, -1.0,  1.0, 1.0,
            -1.0 , -1.0, 0.0 , 1.0,
             1.0 , 1.0, 1.0, 0.0,

        ))

        self.vao = self.ctx.simple_vertex_array(prog, vbo, ['vert', 'tex_coord'])


        self.cam_thread.start()

    def paintGL(self):
        self.ctx.viewport = (0, 0, self.width(), self.height())
        self.ctx.clear(0.9, 0.9, 0.9)
        self.vao.render()
        self.ctx.finish()
        self.update()


app = QtWidgets.QApplication([])
window = QGLWidget()
#window.move(QtWidgets.QDesktopWidget().rect().center() - window.rect().center())
window.resize(640, 480)
window.show()
app.exec_()