#version 460

layout(local_size_x=8, local_size_y=8) in;
layout(binding=0) buffer b_out
{
    vec4 o_col[];
};

uniform float u_time;
uniform uint u_width;
uniform uint u_height;

void main()
{
    uvec2 xy = gl_LocalInvocationID.xy + gl_WorkGroupID.xy * 8;
    uint i = xy.x + xy.y * u_width;

    vec2 wh = vec2(u_width, u_height);
    vec2 uv = vec2(xy) / wh;

    vec3 rgb = vec3(uv, cos(u_time * 0.1) * 0.5 + 0.5);

    o_col[i].xyz = rgb;
    o_col[i].w = 1.0;
}
