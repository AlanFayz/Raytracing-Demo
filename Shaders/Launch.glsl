#version 450

layout (local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

layout(rgba32f, binding = 0) uniform image2D OutImage;
layout(rgba32f, binding = 1) uniform image2D Accumulation;

#define FLT_MAX 3.4028235e+38
#define UINT_MAX 0xFFFFFFFF

layout(std430, binding = 0) buffer ObjectData 
{
    float data[];
};

layout(binding = 1) uniform PerFrame
{
    mat4 InverseView;
    mat4 InverseProjection;
    vec3 CameraPosition;
    float Seed;
    float ObjectCount;
    float FrameIndex;
};

#include "Ray.glsl"
#include "Random.glsl"

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


void main() 
{
    ivec2 id = ivec2(gl_GlobalInvocationID.xy);

    if(FrameIndex == 1)
    {
        imageStore(Accumulation, id, vec4(0));  
    }


    int bounceCount = 3;

    vec3 coord  = vec3(id.x, id.y, 1.0);
    coord  /= vec3(imageSize(OutImage), 1.0);

    float col = 1.0 - coord.y;
    col = min(col + 0.3, 1.0);
    vec3 skyColor = vec3(col, col, col * 1.8);

    vec3 light = vec3(0.0, 0.0, 0.0);
    vec3 color = vec3(1.0, 1.0, 1.0);

    coord   = coord * 2 - 1;
    coord.z = -1.0;

    vec4 target = InverseProjection * vec4(coord.x, coord.y, 1.0, 1.0);
    target.xyz /= target.w; 
    
    vec3 rayDirection = normalize((InverseView * vec4(target.xyz, 0.0)).xyz);

    RayPayload ray;

    ray.Origin = CameraPosition;
    ray.Direction = rayDirection;
    ray.Distance = FLT_MAX;
    ray.SphereIndex = -1;
    ray.Intersected = false;

    uint currentSeed = uint(Seed);
    bool calculateDiffuse = false;

    for(int bounce = 0; bounce < bounceCount; bounce++)
    {
        for(int i = 0; i < int(ObjectCount); i++)
        {
            Sphere sphere = GetSphere(i);

            RayPayload test = RaySphereTest(ray, sphere, i);

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

            light += sphere.Color * color * sphere.Emission;
            color *= sphere.Color;

            ray.Origin  = ray.Origin + ray.Direction * ray.Distance;
            ray.Origin += ray.Normal * 0.0001;
            ray.Direction = normalize(RandomHemisphereVector(ray.Normal, currentSeed));
            
            ray.Intersected = false;
            ray.Distance = FLT_MAX;

            calculateDiffuse = true;

            continue;
        }

        break;
    }

    float cosTheta = 1.0; 
    
    if (calculateDiffuse)
    {
        cosTheta = max(dot(ray.Normal, ray.Direction), 0.0);
    }

    light += skyColor * color * cosTheta;

    vec4 newColor = imageLoad(Accumulation, id) + vec4(light, 1.0);
    
    imageStore(Accumulation, id, newColor);  
    imageStore(OutImage, id, newColor / FrameIndex);  
}
