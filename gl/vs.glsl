#version 460

uniform uint u_width;
uniform uint u_height;

in vec2 in_pos;

out float _aspect;
out vec2 _uv;

void main()
{
    _aspect = float(u_width) / float(u_height);
    vec2 uv = in_pos;
    _uv = uv;
    uv.y *= _aspect;
    gl_Position = vec4(uv, 0.0, 1.0);
}
