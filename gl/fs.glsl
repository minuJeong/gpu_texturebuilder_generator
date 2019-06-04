#version 460

in vec2 _uv;
out vec4 color;

float saturate(float x) { return min(max(x, 0.0), 1.0); }

void main()
{
    vec3 rgb = vec3(0.0, 0.0, 0.0);

    rgb.xy = _uv * 0.5 + 0.5;

    color = vec4(rgb, 1.0);
}
