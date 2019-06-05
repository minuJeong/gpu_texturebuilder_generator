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


float sphere(vec3 p, float r)
{
    return length(p) - r;
}

float world(vec3 p)
{
    return sphere(p, 2.0);
}

float raymarch(vec3 o, vec3 r)
{
    float t;
    float d;
    vec3 p;
    for (int i = 0; i < 32; i++)
    {
        p = o + r * t;
        d = world(p);
        t += d;
        if (d < 0.01)
        {
            break;
        }
    }
    return t;
}

void main()
{
    uvec2 xy = gl_LocalInvocationID.xy + gl_WorkGroupID.xy * 8;
    uint i = xy.x + xy.y * u_width;

    vec2 uv = vec2(xy / vec2(u_width, u_height));
    uv = uv * 2.0 - 1.0;

    vec3 rgb = vec3(0.1);

    vec3 o = vec3(0.0, 0.0, -5.0);
    vec3 r = normalize(vec3(uv, 1.0));
    float t = raymarch(o, r);
    float L = 0.0;
    if (t < 1000.0)
    {
        L = 1.0;
        rgb.x = 1.0;
    }

    out_color[i].xyz = rgb;
    out_color[i].z = L;
    out_color[i].x = rgb.x;
    out_color[i].w = 1.0;
}
