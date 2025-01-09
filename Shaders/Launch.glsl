#version 450

layout (local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

layout(rgba32f, binding = 0) uniform image2D OutImage;
layout(rgba32f, binding = 1) uniform image2D Accumulation;

uniform int ObjectCount;
uniform int FrameIndex;
uniform uint Seed;

#define FLT_MAX 3.4028235e+38
#define UINT_MAX 0xFFFFFFFF

layout(std430, binding = 0) buffer MyBuffer 
{
    float data[];
};

#include "Ray.glsl"

Sphere GetSphere(int index) 
{
    int realIndex = 8 * index;

    Sphere sphere; 
    sphere.Center   = vec3(data[realIndex], data[realIndex + 1], data[realIndex + 2]);
    sphere.Color    = vec3(data[realIndex + 3], data[realIndex + 4], data[realIndex + 5]);
    sphere.Radius   = data[realIndex + 6];
    sphere.Emission = data[realIndex + 7];

    return sphere;
}

uint PCGHash(uint seed)
{
	uint state = seed * 747796405u + 2891336453u;
    uint word = ((state >> ((state >> 28u) + 4u)) ^ state) * 277803737u;
    return (word >> 22u) ^ word;
}

float GenFloat(inout uint seed, float min, float max)
{
    seed = PCGHash(seed);
    return min + ((float(seed) / float(UINT_MAX)) * (max-min));
}

vec3 RandomVector(inout uint seed)
{
    return vec3(GenFloat(seed, -1.0, 1.0), GenFloat(seed, -1.0, 1.0), GenFloat(seed, -1.0, 1.0));
}

void main() 
{
    ivec2 id = ivec2(gl_GlobalInvocationID.xy);

    if(FrameIndex == 1)
    {
        imageStore(Accumulation, id, vec4(0));  
    }

    int bounceCount = 50;

    vec3 coord  = vec3(id.x, id.y, 1.0);
    coord  /= vec3(imageSize(OutImage), 1.0);

    vec3 skyColor = vec3(0.03, coord.y / 10, 0.03);
    vec3 light = vec3(0.0, 0.0, 0.0);
    vec3 color = vec3(1.0, 1.0, 1.0);

    coord   = coord * 2 - 1;
    coord.z = -1.0;

    float aspectRatio = imageSize(OutImage).x / imageSize(OutImage).y;
    coord.x *= aspectRatio;

    RayPayload ray;

    ray.Origin = vec3(0, 0, 0);
    ray.Direction = normalize(coord);
    ray.Distance = FLT_MAX;
    ray.SphereIndex = -1;
    ray.Intersected = false;

    uint currentSeed = Seed;

    for(int bounce = 0; bounce < bounceCount; bounce++)
    {
        for(int i = 0; i < ObjectCount; i++)
        {
            RayPayload test = RaySphereTest(ray, GetSphere(i), i);

            if(!test.Intersected)
            {
                continue;
            }

            if (test.Distance < ray.Distance)
            {
                ray = test;
            }
        }

        if (ray.Intersected)
        {
            Sphere sphere = GetSphere(ray.SphereIndex);

            color *= sphere.Color;
            light += sphere.Color * sphere.Emission;

            ray.Origin  = ray.Origin + ray.Direction * ray.Distance;
            ray.Origin += ray.Normal * 0.001;

            ray.Direction = normalize(RandomVector(currentSeed) + ray.Normal);
            ray.Intersected = false;
            ray.Distance = FLT_MAX;

            continue;
        }

        break;
    }


    light += skyColor * color;


    vec4 newColor = imageLoad(Accumulation, id) + vec4(light, 1.0);
    imageStore(Accumulation, id, newColor);  
    imageStore(OutImage, id, newColor / FrameIndex);  
}
