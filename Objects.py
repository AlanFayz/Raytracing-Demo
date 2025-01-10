import numpy as np 
import glm


class Sphere:
    def __init__(self, center: glm.vec3, radius: float, colour: glm.vec3, emission: float):
        self.center = center
        self.colour = colour
        self.radius = radius
        self.emission = emission
    
    @property 
    def Data(self):
        return np.concatenate([self.center.to_list(), self.colour.to_list(), np.array([self.radius]), np.array([self.emission])])
    