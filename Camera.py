import glm

class Camera:
    def __init__(self, fov: float, aspectRatio: float, nearPlane: float, farPlane: float):
        self.perspectiveMatrix = glm.perspective(glm.radians(fov), aspectRatio, nearPlane, farPlane)
        
        self.position = glm.vec3(0.0, 0.0, 0.0)
        self.rotation = glm.vec3(0.0, 0.0, 0.0)
        self.scale = glm.vec3(1.0, 1.0, 1.0)

    def RotationMatrix(self, rotation: glm.vec3) -> glm.mat4:
        return glm.rotate(glm.mat4(1.0), rotation.x, glm.vec3(1, 0, 0)) * \
               glm.rotate(glm.mat4(1.0), rotation.y, glm.vec3(0, 1, 0)) * \
               glm.rotate(glm.mat4(1.0), rotation.z, glm.vec3(0, 0, 1))

    def TranslationMatrix(self, position: glm.vec3) -> glm.mat4:
        return glm.translate(glm.mat4(1.0), position)

    def ScaleMatrix(self, scale: glm.vec3) -> glm.mat4:
        return glm.scale(glm.mat4(1.0), scale)

    def SetPosition(self, *position):
        self.position[0] = position[0]
        self.position[1] = position[1]
        self.position[2] = position[2]
    
    def SetRotation(self, *rotation):
        self.rotation[0] = rotation[0]
        self.rotation[1] = rotation[1]
        self.rotation[2] = rotation[2]
    
    def SetScale(self, *scale):
        self.scale[0] = scale[0]
        self.scale[1] = scale[1]
        self.scale[2] = scale[2]
    
    @property
    def Transform(self) -> glm.mat4:        
        return self.TranslationMatrix(self.position) * self.RotationMatrix(self.rotation) * self.ScaleMatrix(self.scale)

    @property
    def View(self) -> glm.mat4:    
        return glm.inverse(self.Transform)

    @property
    def Projection(self) -> glm.mat4:
        return self.perspectiveMatrix

    @property
    def ViewProjection(self) -> glm.mat4:
        return self.Projection * self.View


