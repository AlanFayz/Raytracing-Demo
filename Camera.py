import glm

import pygame

class Camera:
    def __init__(self, fov: float, aspectRatio: float, nearPlane: float, farPlane: float):
        self.fov, self.aspectRatio, self.nearPlane, self.farPlane = fov, aspectRatio, nearPlane, farPlane

        self.position = glm.vec3(0, 0, 5)
        self.forward  = glm.vec3(0, 0, -1)

        self.movementSpeed = 5
        self.viewSpeed = 1.0

    def Update(self, delta: float) -> bool:
        keys = pygame.key.get_pressed()
        mouseButtons = pygame.mouse.get_pressed()

        if not mouseButtons[0]:
            pygame.event.set_grab(False)
            pygame.mouse.set_visible(True)
            return False

        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)

        moved = False

        up = glm.vec3(0, 1, 0)
        right = glm.normalize(glm.cross(self.forward, up))

        movement = glm.vec3(0)
        if keys[pygame.K_w]:
            movement += self.forward
        if keys[pygame.K_s]:
            movement -= self.forward
        if keys[pygame.K_a]:
            movement -= right
        if keys[pygame.K_d]:
            movement += right
        if keys[pygame.K_q]:
            movement += up
        if keys[pygame.K_e]:
            movement -= up

        if glm.length(movement) > 0:
            self.position += glm.normalize(movement) * self.movementSpeed * delta
            moved = True

        return moved


        
    @property 
    def Projection(self) -> glm.mat4:
        return glm.perspective(glm.radians(self.fov), self.aspectRatio, self.nearPlane, self.farPlane)

    @property
    def View(self) -> glm.mat4:
        worldUp = glm.vec3(0, 1, 0)
        return glm.lookAt(self.position, self.position + self.forward, worldUp)

    @property
    def InverseProjection(self) -> glm.mat4:
        return glm.inverse(self.Projection)
    
    @property
    def InverseView(self) -> glm.mat4:
        return glm.inverse(self.View)