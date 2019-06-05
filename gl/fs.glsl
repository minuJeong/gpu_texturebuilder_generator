#version 460

layout(binding=1) buffer cs_buffer
{
    vec4 cs_col[];
};

uniform float u_time;
uniform uint u_width;
uniform uint u_height;

in vec2 _uv;
out vec4 color;

float saturate(float x) { return min(max(x, 0.0), 1.0); }
vec2 saturate(vec2 x) { return min(max(x, 0.0), 1.0); }
vec3 saturate(vec3 x) { return min(max(x, 0.0), 1.0); }

void main()
{
    vec3 rgb = vec3(0.0);

    vec2 xy = _uv * 0.5 + 0.5;
    uint i = uint(xy.x * u_width + xy.y * u_width * u_height);
    rgb.z = cs_col[i].z;

    vec3 debug = cs_col[i].xyz;

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

    color.xyz += saturate(debug * 0.1);
}
