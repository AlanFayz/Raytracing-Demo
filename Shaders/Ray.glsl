#ifndef RAY 
#define RAY 

struct Sphere
{
    vec3 Center;
    vec3 Color;
    float Radius;
    float Emission;
};

struct RayPayload
{
    vec3  Origin;
    vec3  Direction;
    vec3  Normal;
    float Distance;
    int   SphereIndex;
    bool  Intersected;
};

RayPayload RaySphereTest(in RayPayload inPayload, Sphere sphere, int sphereIndex)
{
    RayPayload payload;

    payload.Intersected = false;

    vec3 oc = inPayload.Origin - sphere.Center;

    float a = dot(inPayload.Direction, inPayload.Direction);
    float b = 2 * dot(inPayload.Direction, oc);
    float c = dot(oc, oc) - sphere.Radius * sphere.Radius;

    float discriminant = (b * b) - (4 * a * c);

    if (discriminant < 0)
    {
        return payload;
    }

    float root1 =  (-b + sqrt(discriminant)) / (2*a);
    float root2  = (-b - sqrt(discriminant)) / (2*a);

    if (root1 < 0 && root2 < 0)
    {
        return payload;
    }

    payload.Intersected = true;


    if(root1 >= 0 && root2 >= 0)
    {
        payload.Distance = min(root1, root2);
    }
    else
    {
        payload.Distance = max(root1, root2);
    } 

    payload.SphereIndex = sphereIndex;

    payload.Origin = inPayload.Origin;
    payload.Direction = inPayload.Direction;

    vec3 newOrigin = payload.Origin + payload.Direction * payload.Distance;
    payload.Normal = newOrigin - sphere.Center;
    payload.Normal = normalize(payload.Normal);

    return payload;
}


#endif