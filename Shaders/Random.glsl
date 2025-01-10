#ifndef RANDOM 
#define RANDOM 

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

vec3 RandomHemisphereVector(vec3 normal, uint seed)
{
    vec3 randomVec = normalize(RandomVector(seed)); 
    return dot(randomVec, normal) > 0.0 ? randomVec : -randomVec; 
}

#endif