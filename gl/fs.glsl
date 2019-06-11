#version 460

layout(binding=0) buffer cs_buffer_in
{
    vec4 csin_col[];
};

layout(binding=1) buffer cs_buffer_out
{
    vec4 csout_col[];
};

uniform float u_time;
uniform uint u_width;
uniform uint u_height;

in float _aspect;
in vec2 _uv;
out vec4 color;

float saturate(float x) { return min(max(x, 0.0), 1.0); }
vec2 saturate(vec2 x) { return min(max(x, 0.0), 1.0); }
vec3 saturate(vec3 x) { return min(max(x, 0.0), 1.0); }

vec2 R(vec2 x, float a)
{
    float c = cos(a);
    float s = sin(a);
    return mat2(c, -s, s, c) * x;
}

void main()
{
    vec3 rgb = vec3(0.0);

    vec2 xy = _uv * 0.5 + 0.5;
    xy *= vec2(u_width, u_height);
    xy.x -= u_width / 2;
    uint i = uint(xy.x + xy.y * u_width);
    vec3 csrgb = csout_col[i].xyz;

    vec2 ruv = _uv;
    ruv.x /= u_width / u_height;
    float a = length(_uv) * 0.5;
    // a = log2(a);
    float b = mod(u_time, 3.141593 * 2.0);

    float angle = b - a;
    ruv.xy = R(ruv.xy, angle);

    vec2 tile = ruv * 2.0;
    tile = mod(tile, 1.0);
    rgb.xy = tile;
    rgb.z = 1.0 - (rgb.x + rgb.y);

    rgb = saturate(rgb);
    color = vec4(rgb, 1.0);
}
