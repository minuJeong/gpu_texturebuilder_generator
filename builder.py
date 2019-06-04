import os

import numpy as np
import moderngl as mg
import imageio as ii

from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


width, height = 512, 512


class FSEventHandler(FileSystemEventHandler):
    def __init__(self, callback):
        super(FSEventHandler, self).__init__()
        self.callback = callback

    def on_modified(self, e):
        return self.callback()


class WatchDog(QThread):
    bark = pyqtSignal()

    def __init__(self):
        super(WatchDog, self).__init__()
        self.ehandler = FSEventHandler(self.on_watch)

    def on_watch(self):
        self.bark.emit()

    def run(self):
        observer = Observer()
        observer.schedule(self.ehandler, "./gl", True)
        observer.start()
        observer.join()


class GLUtil(object):
    @classmethod
    def screen_vao(cls, gl, program):
        vbo = [
            -1.0, -1.0,
            +1.0, -1.0,
            -1.0, +1.0,
            +1.0, +1.0,
        ]
        vbo = np.array(vbo).astype(np.float32)
        vbo = [(gl.buffer(vbo), "2f", "in_pos")]

        ibo = [0, 1, 2, 1, 2, 3]
        ibo = np.array(ibo).astype(np.int32)
        ibo = gl.buffer(ibo)

        vao = gl.vertex_array(program, vbo, ibo)
        return vao

    @classmethod
    def shader(cls, path, **karg):
        context = None
        with open(path, 'r') as fp:
            context = fp.read()

        for k, v in karg.items():
            context = context.replace(k, v)

        lines = []
        for line in context.splitlines():
            if line.startswith("#include "):
                lines.append(GLUtil.shader(line.split(" ")[1]))
                continue

            lines.append(line)

        return context

    @classmethod
    def serialize_buffer(cls, gl_buffer):
        data = gl_buffer.read()
        data = np.frombuffer(data, dtype=np.float32)
        data = np.multiply(data, 255.0)
        data = data.reshape((width, height, 4))
        data = data.astype(np.uint8)
        return data


class Renderer(QtWidgets.QOpenGLWidget):
    def __init__(self):
        super(Renderer, self).__init__()
        self.setMinimumSize(width, height)
        self.setMaximumSize(width, height)

        self.watchdog = WatchDog()
        self.watchdog.bark.connect(self.recompile)
        self.watchdog.start()

    def get_filepath(self, template):
        i = 0
        file_name = template.format(i)
        while os.path.exists(file_name):
            i += 1
            file_name = template.format(i)
        return file_name

    def build_prog(self, gl):
        prog = gl.program(
            vertex_shader=GLUtil.shader("./gl/vs.glsl"),
            fragment_shader=GLUtil.shader("./gl/fs.glsl"),
        )
        return prog

    def recompile(self):
        try:
            self.program = self.build_prog(self.gl)
            self.vao = GLUtil.screen_vao(self.gl, self.program)
            print("shader recompiled.")
        except Exception as e:
            print(e)

    def initializeGL(self):
        self.gl = mg.create_context()
        self.program = self.build_prog(self.gl)
        self.vao = GLUtil.screen_vao(self.gl, self.program)

        self.to_capture = False
        self.to_record = False
        self.capture_texture = self.gl.texture((width, height), 4, dtype="f4")
        capture_framebuffer = self.gl.framebuffer([self.capture_texture])
        self.capture_scope = self.gl.scope(capture_framebuffer)
        self.recording = None

    def paintGL(self):
        # update screen
        self.vao.render()

        # save to png
        if self.to_capture:
            with self.capture_scope:
                self.vao.render()

            dst = self.get_filepath("./capture_{}.png")
            data = GLUtil.serialize_buffer(self.capture_texture)
            ii.imwrite(dst, data)
            print("captured!")

            self.to_capture = False

        # init save to video
        if self.to_record:
            with self.capture_scope:
                self.vao.render()

            if not self.recording:
                print("start recording..")
                dst = self.get_filepath("./capture_{}.mp4")
                self.recording = ii.get_writer(dst)
            data = GLUtil.serialize_buffer(self.capture_texture)
            self.recording.append_data(data)

        # close save to video
        else:
            if self.recording:
                self.recording.close()
                print("finished recording!")
            self.recording = None

        # force update frame
        self.update()

    def keyPressEvent(self, e):
        k = e.key()

        if k == 16777249:
            self.to_record = True

    def keyReleaseEvent(self, e):
        k = e.key()

        if k == 32:
            self.to_capture = True

        elif k == 16777249:
            self.to_record = False

        else:
            print("undefined key pressed: {}".format(k))


def main():
    app = QtWidgets.QApplication([])
    renderer = Renderer()
    renderer.show()
    app.exec()


if __name__ == "__main__":
    main()
