import os
import time

import numpy as np
import moderngl as mg
import imageio as ii

from PyQt5 import QtWidgets
from PyQt5.QtCore import QThread
from PyQt5.QtCore import pyqtSignal
from PyQt5.Qt import Qt
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# global consts: do not change during runtime
width, height = 512, 512


def log(*arg):
    """
    wraps built-in print for additional extendability
    """

    context = str(*arg)
    print("[Texture Builder] {}".format(context))


class FSEventHandler(FileSystemEventHandler):
    """
    simple file system event handler for watchdog observer calls callback on mod
    """

    def __init__(self, callback):
        super(FSEventHandler, self).__init__()
        self.callback = callback

    def on_modified(self, e):
        return self.callback()


class WatchDog(QThread):
    """
    watching ./gl directory, on modified, call given bark_callback
    running on separated thread
    """

    bark = pyqtSignal()

    def __init__(self, bark_callback):
        super(WatchDog, self).__init__()
        self.ehandler = FSEventHandler(self.on_watch)
        self.bark.connect(bark_callback)

    def on_watch(self):
        self.bark.emit()

    def run(self):
        """
        start oberserver in another separated thread, and WatchDog thread only monitors it
        """

        observer = Observer()
        observer.schedule(self.ehandler, "./gl", True)
        observer.start()
        observer.join()


class GLUtil(object):
    """
    some utility methods
    """

    @classmethod
    def screen_vao(cls, gl, program):
        """
        generate simplest screen filling quad
        """

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
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.watchdog = WatchDog(self.recompile)
        self.watchdog.start()

    def get_filepath(self, template):
        i = 0
        file_name = template.format(i)
        while os.path.exists(file_name):
            i += 1
            file_name = template.format(i)
        return file_name

    def build_prog(self, gl):
        """
        .
        """

        prog = gl.program(
            vertex_shader=GLUtil.shader("./gl/vs.glsl"),
            fragment_shader=GLUtil.shader("./gl/fs.glsl"),
        )
        u_time = None
        u_width = None
        u_height = None
        if "u_time" in prog:
            u_time = prog["u_time"]

        if "u_width" in prog:
            u_width = prog["u_width"]

        if "u_height" in prog:
            u_height = prog["u_height"]

        return prog, [u_time, u_width, u_height]

    def build_cs(self, gl):
        """
        simple compute shader run after screen rendering
        """

        cs = gl.compute_shader(GLUtil.shader("./gl/cs/cs.glsl"))

        u_time = None
        u_width = None
        u_height = None
        if "u_time" in cs:
            u_time = cs["u_time"]

        if "u_width" in cs:
            u_width = cs["u_width"]

        if "u_height" in cs:
            u_height = cs["u_height"]

        buf_in = gl.buffer(reserve=width * height * 4 * 4)
        buf_in.bind_to_storage_buffer(0)

        buf_out = gl.buffer(reserve=width * height * 4 * 4)
        buf_out.bind_to_storage_buffer(1)

        return cs, [u_time, u_width, u_height], [buf_in, buf_out]

    def recompile(self):
        """
        called everytime any files under gl directory changes
        """

        self.vaos = []
        try:
            self.program, uniforms = self.build_prog(self.gl)
            self.u_time, self.u_width, self.u_height = uniforms
            vao = GLUtil.screen_vao(self.gl, self.program)
            self.vaos.append(vao)

            self.compute, uniforms, buffers = self.build_cs(self.gl)
            self.u_cstime, self.u_cswidth, self.u_csheight = uniforms
            self.buf_in, self.buf_out = buffers

            if self.u_width:
                self.u_width.value = width

            if self.u_cswidth:
                self.u_cswidth.value = width

            if self.u_height:
                self.u_height.value = height

            if self.u_csheight:
                self.u_csheight.value = height

            self.gx, self.gy = int(width / 8), int(height / 8)
            self.update_uniform_time()

            log("[Renderer] shader recompiled.")

        except Exception as e:
            log(e)

    def initializeGL(self):
        """
        called only once when start
        """

        self.gl = mg.create_context()

        self.recompile()

        self.to_capture = False
        self.to_record = False
        self.capture_texture = self.gl.texture((width, height), 4, dtype="f4")
        capture_framebuffer = self.gl.framebuffer([self.capture_texture])
        self.capture_scope = self.gl.scope(capture_framebuffer)
        self.recording = None

        self.to_capture_buffer_in = False
        self.to_capture_buffer_out = False

    def update_uniform_time(self):
        t = time.time() % 1000
        if self.u_time:
            self.u_time.value = t

        if self.u_cstime:
            self.u_cstime.value = t

    def paintGL(self):
        """
        called every frame
        """

        # update screen
        self.update_uniform_time()
        for vao in self.vaos:
            vao.render()

        # copy screen frame to buffer
        if self.buf_in:
            cur_framebuffer = self.gl.detect_framebuffer()
            cur_framebuffer.read_into(
                self.buf_in, None, 4, dtype="f4"
            )

        # run frame compute shader
        self.compute.run(self.gx, self.gy)

        # save to png
        if self.to_capture:
            with self.capture_scope:
                self.vao.render()

            dst = self.get_filepath("./capture_{}.png")
            data = GLUtil.serialize_buffer(self.capture_texture)
            ii.imwrite(dst, data)
            log("captured!")

            self.to_capture = False

        # init save to video
        if self.to_record:
            with self.capture_scope:
                self.vao.render()

            if not self.recording:
                log("start recording..")
                dst = self.get_filepath("./capture_{}.mp4")
                self.recording = ii.get_writer(dst, fps=30)
            data = GLUtil.serialize_buffer(self.capture_texture)
            self.recording.append_data(data)

        # close save to video
        else:
            if self.recording:
                self.recording.close()
                log("finished recording!")
            self.recording = None

        if self.to_capture_buffer_in:
            dst = self.get_filepath("./buf_in_{}.png")
            data = GLUtil.serialize_buffer(self.buf_in)
            ii.imwrite(dst, data)
            self.to_capture_buffer_in = False

            log("buf_in captured")

        if self.to_capture_buffer_out:
            dst = self.get_filepath("./buf_out_{}.png")
            data = GLUtil.serialize_buffer(self.buf_out)
            ii.imwrite(dst, data)
            self.to_capture_buffer_out = False

            log("buf_out captured")

        # force update frame
        self.update()

    def keyPressEvent(self, e):
        """
        left ctrl: start/stop recording on press/release
        """

        k = e.key()

        # left ctrl
        if k == 16777249:
            self.to_record = True

    def keyReleaseEvent(self, e):
        """
        space bar: capture frame buffer
        z: capture buf_in buffer
        x: capture buf_out buffer
        left ctrl: start/stop recording on press/release
        """

        k = e.key()

        # space bar
        if k == 32:
            self.to_capture = True

        # z
        elif k == 90:
            self.to_capture_buffer_in = True

        # x
        elif k == 88:
            self.to_capture_buffer_out = True

        # left ctrl
        elif k == 16777249:
            self.to_record = False

        # undefined
        else:
            log("undefined key pressed: {}".format(k))


def main():
    app = QtWidgets.QApplication([])
    renderer = Renderer()
    renderer.show()
    app.exec()


if __name__ == "__main__":
    main()
