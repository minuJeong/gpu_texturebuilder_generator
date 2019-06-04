#version 460

in vec2 _uv;
out vec4 color;

float saturate(float x) { return min(max(x, 0.0), 1.0); }

float sphere(vec3 p, float r)
{
    return length(p) - r;
}

float world(vec3 p)
{
    float d;

    vec3 q = p - vec3(0.0, 0.0, 0.0);
    float r = 2.0;
    float s1 = sphere(q, r);

    d = s1;
    return d;
}

float raymarch(vec3 o, vec3 r)
{
    vec3 p;
    float t;
    float d;

    for (int i = 0; i < 64; i++)
    {
        p = o + r * t;
        d = world(p);
        if (d < 0.002)
        {
            break;
        }
        t += d;
    }
    return t;
}

vec3 normal_at(vec3 p)
{
    vec2 e = vec2(0.002, 0.0);
    return normalize(world(p) - vec3(
        world(p - e.xyy),
        world(p - e.yxy),
        world(p - e.yyx)
    ));
}

void main()
{
    vec3 light_pos = vec3(-1.0, 10.0, -2.0);

    vec3 o = vec3(0.0, 0.0, -5.0);
    vec3 r = normalize(vec3(_uv, 1.0));

    vec3 rgb = vec3(_uv * 0.5 +0.5, 0.0);
    float t = raymarch(o, r);
    if (t < 100.0)
    {
        vec3 P = o + r * t;
        vec3 N = normal_at(P);
        vec3 L = normalize(P - light_pos);

        float ndl = dot(N, L);
        ndl = saturate(ndl);
        rgb.xyz = ndl.xxx;
    }

    color = vec4(rgb, 1.0);
}
