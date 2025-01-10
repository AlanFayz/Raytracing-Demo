import glm

import pygame

class Camera:
    def __init__(self, fov: float, aspectRatio: float, nearPlane: float, farPlane: float):
        self.fov, self.aspectRatio, self.nearPlane, self.farPlane = fov, aspectRatio, nearPlane, farPlane

        self.position = glm.vec3(0, 0, 5)
        self.forward  = glm.vec3(0, 0, -1)

        self.movementSpeed = 5
        self.viewSpeed = 0.05

        self.yaw, self.pitch = 0, 0

    def Update(self, delta: float) -> bool:
        keys = pygame.key.get_pressed()
        mouseButtons = pygame.mouse.get_pressed()

        if not mouseButtons[0]:
            pygame.event.set_grab(False)
            pygame.mouse.set_visible(True)
            return False

        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)

        deltaMouse = -glm.vec2(pygame.mouse.get_rel()) * self.viewSpeed

        movement = glm.vec3(0)
        moved = False

        worldUp = glm.vec3(0, 1, 0)

        self.yaw += deltaMouse.x  
        self.pitch -= deltaMouse.y  

        self.pitch = glm.clamp(self.pitch, -89, 89)

        #self.forward = glm.vec3(
        #    glm.cos(glm.radians(self.pitch)) * glm.cos(glm.radians(self.yaw)), 
        #    glm.sin(glm.radians(self.pitch)),  
        #    glm.cos(glm.radians(self.pitch)) * glm.sin(glm.radians(self.yaw))
        #)
        #self.forward = glm.normalize(self.forward)

        right = glm.normalize(glm.cross(self.forward, worldUp))
        up = glm.normalize(glm.cross(right, self.forward))

        if glm.length(deltaMouse) > 0:
            moved = True

        if keys[pygame.K_w]:
            movement += self.forward
            moved = True

        if keys[pygame.K_s]:
            movement -= self.forward
            moved = True

        if keys[pygame.K_a]:
            movement -= right
            moved = True

        if keys[pygame.K_d]:
            movement += right
            moved = True

        if keys[pygame.K_q]:
            movement += up
            moved = True 

        if keys[pygame.K_e]:
            movement -= up
            moved = True 

        self.position += movement * self.movementSpeed * delta  

        return moved

        
    @property 
    def Projection(self) -> glm.mat4:
        return glm.perspective(glm.radians(self.fov), self.aspectRatio, self.nearPlane, self.farPlane)

    @property
    def View(self) -> glm.mat4:
        worldUp = glm.vec3(0, 1, 0)
        right   = glm.normalize(glm.cross(self.forward, worldUp))
        up      = glm.normalize(glm.cross(right, self.forward))
        return glm.lookAt(self.position, self.position + self.forward, up)

    @property
    def InverseProjection(self) -> glm.mat4:
        return glm.inverse(self.Projection)
    
    @property
    def InverseView(self) -> glm.mat4:
        return glm.inverse(self.View)