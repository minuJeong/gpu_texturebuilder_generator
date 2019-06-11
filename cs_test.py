import moderngl as mg
import numpy as np
import imageio as ii


width, height = 512, 512


def read_shader(path):
    with open(path, 'r') as fp:
        return fp.read()


def serialize_buffer(b):
    data = np.frombuffer(b.read(), np.float32)
    data = np.multiply(data, 255.0)
    data = data.reshape((height, width, 4))
    data = data.astype(np.uint8)
    return data


path = "./gl/cs/cs_test.glsl"
gl = mg.create_standalone_context()

cs = gl.compute_shader(read_shader(path))
if "u_width" in cs:
    cs["u_width"].value = width

if "u_height" in cs:
    cs["u_height"].value = height

size = width * height * 4 * 4
result = gl.buffer(reserve=size)
result.bind_to_storage_buffer(0)

gx, gy = int(width / 8), int(height / 8)

if "u_time" in cs:
    writer = ii.get_writer("output.mp4", fps=60)
    for i in range(400):
        cs["u_time"].value = i % 10000
        cs.run(gx, gy)

        data = serialize_buffer(result)
        writer.append_data(data)
