import random
import sys
import time
import pygame
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
import numpy as np

from Vector import *

class Sphere:
    def __init__(self, center: Vector, radius: float, colour: Vector, emission: float):
        self.center = center
        self.colour = colour
        self.radius = radius
        self.emission = emission
    
    @property 
    def data(self):
        return np.concatenate([self.center.getData(), self.colour.getData(), np.array([self.radius]), np.array([self.emission])])

def CreateTexture(width, height):
    textureID = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, textureID)

    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, width, height, 0, GL_RGBA, GL_FLOAT, None)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

    return textureID

def DestroyTexture(textureID):
    glDeleteTextures(1, [textureID])

def CreateBuffer(data=None, usage=GL_STATIC_DRAW):
    if data is not None:
        size = data.nbytes
    else:
        size = 0
    
    bufferID = glGenBuffers(1)
    
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, bufferID)
    
    if data is not None:
        glBufferData(GL_SHADER_STORAGE_BUFFER, size, data, usage)
    else:
        glBufferData(GL_SHADER_STORAGE_BUFFER, size, None, usage)
    
    glBindBuffer(GL_SHADER_STORAGE_BUFFER, 0)

    return bufferID

def DrawImage(rasterProgram, image):
    vertices = np.array([
        -1.0, -1.0, 0.0, 0.0,  
         1.0, -1.0, 1.0, 0.0,  
         1.0,  1.0, 1.0, 1.0,  
        -1.0,  1.0, 0.0, 1.0   
    ], dtype=np.float32)

    indices = np.array([
        0, 1, 2,  # First triangle
        0, 2, 3   # Second triangle
    ], dtype=np.uint32)

    vao = glGenVertexArrays(1)
    glBindVertexArray(vao)

    vbo = glGenBuffers(1)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)

    glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(2 * 4))
    glEnableVertexAttribArray(1)

    ebo = glGenBuffers(1)
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

    glUseProgram(rasterProgram)

    glBindTextureUnit(0, image)

    glUniform1i(glGetUniformLocation(rasterProgram, "Image"), 0)

    glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

    glBindVertexArray(0)


def Main():
    shaderProgram = None
    rasterProgram = None 

    pygame.init()
    screen = pygame.display.set_mode((800, 600), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)

    with open("shader.glsl", "r") as file:
        code = file.read()

        computeShader = compileShader(code, GL_COMPUTE_SHADER)
        shaderProgram = compileProgram(computeShader)

    with open("fragment.glsl") as fragment:
        fragmentCode = fragment.read()
        fragmentShader = compileShader(fragmentCode, GL_FRAGMENT_SHADER)

        with open("vertex.glsl") as vertex:
            vertexCode = vertex.read()
            vertexShader = compileShader(vertexCode, GL_VERTEX_SHADER)

            rasterProgram = compileProgram(fragmentShader, vertexShader)
    
    
    texture = CreateTexture(800, 600)  
    accumulation = CreateTexture(800, 600)

    Run(shaderProgram, rasterProgram, texture, accumulation, screen)

    pygame.quit()


def Compute(computeProgram, texture, accumulation, width, height, nObjects, frameIndex, buffer=None):
    seed = random.randint(0, 0xFFFFFFFF)
    
    glUseProgram(computeProgram)


    if buffer:
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, buffer)

    glBindImageTexture(0, texture, 0, False, 0, GL_READ_WRITE, GL_RGBA32F)
    glBindImageTexture(1, accumulation, 0, False, 0, GL_READ_WRITE, GL_RGBA32F)

    glUniform1i(glGetUniformLocation(computeProgram, "OutImage"), 0)
    glUniform1i(glGetUniformLocation(computeProgram, "Accumulation"), 1)

    glUniform1i(glGetUniformLocation(computeProgram, "ObjectCount"),  nObjects)
    glUniform1i(glGetUniformLocation(computeProgram, "FrameIndex"),  frameIndex)
    glUniform1ui(glGetUniformLocation(computeProgram, "Seed"),  seed)


    glDispatchCompute(math.ceil(width / 16), math.ceil(height / 16), 1)
    glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

def Run(computeProgram, rasterProgram, texture, accumulation, window):
    running = True

    objects = []
    objects.append(Sphere(Vector((-30, 40, -70)), 30,    Vector((1,1,1)), 0.01))
    objects.append(Sphere(Vector((-1, 0, -5)),    2,     Vector((245, 66, 182)) / 255, 0.05)) 
    objects.append(Sphere(Vector((3.5, -0.5, -5)),  1.75, Vector((66, 179, 245)) / 255, 0))
    objects.append(Sphere(Vector((0, -998, -100)), 1000, Vector((0.7, 0.5, 0.6)), 0.01))

    data = np.array([o.data for o in objects], dtype=np.float32)

    buffer = CreateBuffer(data)

    frameIndex = 1

    while running:
        start = time.time()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.WINDOWRESIZED:
                DestroyTexture(texture)
                DestroyTexture(accumulation)
                texture = CreateTexture(window.get_width(), window.get_height())
                accumulation = CreateTexture(window.get_width(), window.get_height())

                frameIndex = 1

            if event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()

                if keys[pygame.K_w]:
                    objects[3].center += Vector((0.0, 0.1, 0.0))

                    data = np.array([o.data for o in objects], dtype=np.float32)
                    buffer = CreateBuffer(data)

                    frameIndex = 1

                if keys[pygame.K_s]:
                    objects[3].center -= Vector((0.0, 0.1, 0.0))

                    data = np.array([o.data for o in objects], dtype=np.float32)
                    buffer = CreateBuffer(data)

                    frameIndex = 1


        Compute(computeProgram, texture, accumulation, window.get_width(), window.get_height(), len(objects), frameIndex, buffer)
        DrawImage(rasterProgram, texture)
        
        pygame.display.flip()
        end = time.time()

        print(f"frame took: {end - start}s")

        frameIndex += 1


if __name__ == "__main__":
    Main()
