from math import prod
from multiprocessing import Pool
import os
import numpy as np 
import glm


class Sphere:
    def __init__(self, center: glm.vec3, radius: float, colour: glm.vec3, emission: float):
        self.center = center
        self.colour = colour
        self.radius = radius
        self.emission = emission
    
    @property
    def Volume(self):
        return (4 / 3) * glm.pi() * self.radius * self.radius * self.radius

    @property 
    def Data(self):
        return np.concatenate([self.center.to_list(), self.colour.to_list(), np.array([self.radius]), np.array([self.emission])])

class AABB:
    def __init__(self, minn: glm.vec3 = None, maxx: glm.vec3 = None, obj = None):
        self.minn = glm.vec3(float('inf'))
        self.maxx = glm.vec3(float('-inf'))

        if minn:
            self.minn = minn
        
        if maxx:
            self.maxx = maxx

        if obj:
            self.Grow(obj)
            
    def Grow(self, obj):
        if isinstance(obj, AABB):
            self.minn = glm.min(self.minn, obj.minn)
            self.maxx = glm.max(self.maxx, obj.maxx)

            return

        if isinstance(obj, Sphere):
            minn = obj.center - glm.vec3(obj.radius)
            maxx = obj.center + glm.vec3(obj.radius)

            self.Grow(AABB(minn, maxx))

            return
        
        if isinstance(obj, glm.vec3):
            self.minn = glm.min(self.minn, obj)
            self.maxx = glm.max(self.maxx, obj)

            return
        
        raise ValueError("wot")

    
    def Shrink(self, obj):
        if isinstance(obj, AABB):
            self.minn = glm.max(self.minn, obj.minn)
            self.maxx = glm.min(self.maxx, obj.maxx)

            return

        if isinstance(obj, Sphere):
            minn = obj.center - glm.vec3(obj.radius)
            maxx = obj.center + glm.vec3(obj.radius)

            self.Shrink(AABB(minn, maxx))

            return
    
    def GrowFromObjects(self, objects, key=lambda x: x):
        for obj in objects:
            self.Grow(key(obj))

    @staticmethod 
    def CreateFromObjects(objects):
        bounds = AABB()
        bounds.GrowFromObjects(objects)
        return bounds 
    
    def ParallelGrowFromObjects(self, objects, key=lambda x: x):
        if len(objects) < 80_000:
            self.GrowFromObjects(objects, key=key)
            return 

        chunkSize = len(objects) // os.cpu_count()
        chunks = [objects[i:i+chunkSize] for i in range(0, len(objects), chunkSize)]
        chunks = [[key(item) for item in chunk] for chunk in chunks]

        with Pool() as pool:
            bounds = pool.map(AABB.CreateFromObjects, chunks)
            self.GrowFromObjects(bounds)

    
    def ShrinkFromObjects(self, objects, key=lambda x: x):
        for obj in objects:
            self.Shrink(key(obj))

    
    def Contains(self, instance) -> bool:
        if isinstance(instance, glm.vec3):
            return not (
                instance.x > self.maxx.x or 
                instance.y > self.maxx.y or 
                instance.z > self.maxx.z or 
                instance.x < self.minn.x or 
                instance.y < self.minn.y or 
                instance.z < self.minn.z
            )       
        
        if isinstance(instance, AABB):
            return not (
                instance.minn.x > self.maxx.x or
                instance.minn.y > self.maxx.y or
                instance.minn.z > self.maxx.z or
                instance.maxx.x < self.minn.x or
                instance.maxx.y < self.minn.y or
                instance.maxx.z < self.minn.z
            )

        return False


    @property    
    def MaxDimension(self):
        diagonal = self.maxx - self.minn

        maximum = max(diagonal)

        if maximum  ==  diagonal.x:
            return 0
        elif maximum == diagonal.y:
            return 1
        
        return 2

    @property
    def Diagonal(self):
        return self.maxx - self.minn

    @property 
    def SurfaceArea(self):
        if not self.Valid:
            return 0

        diagonal = self.maxx - self.minn
        return 2 * (diagonal.x * diagonal.y + diagonal.x * diagonal.z + diagonal.y * diagonal.z)
    
    @property 
    def Valid(self) -> bool:
        return self.minn != glm.vec3(float('inf'))
    
    @property
    def Centroid(self) -> glm.vec3:
        return (self.minn + self.maxx) / 2

    @property 
    def Volume(self) -> float:
        diagonal = self.maxx - self.minn
        return prod(diagonal)

    @property
    def Data(self) -> np.array:
        return np.concatenate([np.array(self.minn.to_list()), np.array(self.maxx.to_list())]).flatten()