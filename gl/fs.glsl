#version 460

uniform float u_time;

in vec2 _uv;
out vec4 color;

float saturate(float x) { return min(max(x, 0.0), 1.0); }

void main()
{
    vec3 rgb = vec3(0.0);

    float c = length(_uv);
    c = pow(c, sin(u_time * 4.0) * 0.5 + 0.5) * 4.0;
    vec2 cs = vec2(cos(c), sin(c));
    vec2 ruv = mat2(
        cs.x, -cs.y, cs.y, cs.x
    ) * _uv;

    vec2 tile = ruv * 12.0;
    tile = mod(tile, 1.0);
    rgb.xy = tile;

    color = vec4(rgb, 1.0);
}
