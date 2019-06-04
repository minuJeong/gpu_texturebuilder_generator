#version 460

layout(local_size_x=8, local_size_y=8) in;

layout(binding=0) buffer in_buffer
{
    vec4 in_color[];
};

layout(binding=1) buffer out_buffer
{
    vec4 out_color[];
};

uniform float u_time;
uniform uint u_width;
uniform uint u_height;


void main()
{
    uvec2 xy = gl_LocalInvocationID.xy + gl_WorkGroupID.xy * 8;
    uint i = xy.x + xy.y * u_width;

    vec2 uv = vec2(xy / vec2(u_width, u_height));


    out_color[i] = in_color[i] * 0.5;
    out_color[i].w = 1.0;
}
