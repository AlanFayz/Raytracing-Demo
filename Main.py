import random
import time
import pygame
from OpenGL.GL import *
import numpy as np
import yaml

import math

from Graphics import *
from ShaderCompiler import *
from Objects import *
from Camera import *

class Application:
    def __init__(self, width: int, height: int, save: str =None):
        pygame.init()

        self.window = pygame.display.set_mode((width, height), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.save = save

        self.shaderProgram = ShaderCompiler.Compile(("Shaders/Launch.glsl", GL_COMPUTE_SHADER))
        self.rasterProgram = ShaderCompiler.Compile(("Shaders/Fragment.glsl", GL_FRAGMENT_SHADER), ("Shaders/Vertex.glsl", GL_VERTEX_SHADER)) 

        self.image = CreateTexture(width, height)
        self.accumulation = CreateTexture(width, height)

        data = np.random.randint(0, np.iinfo(np.uint32).max, (width, height, 1), dtype=np.uint32)
        self.randomNumbers = CreateTexture(width, height, data, GL_R32UI, GL_RED_INTEGER, GL_UNSIGNED_INT)
        self.objects = []

        self.camera = Camera(90, width / height, 0.1, 100.0)

        try:
            with open(save, "r") as file:
                data = yaml.safe_load(file)

                self.objects = [
                    Sphere(
                        glm.vec3(obj["Properties"]["Center"]), 
                        obj["Properties"]["Radius"], 
                        glm.vec3(obj["Properties"]["Colour"]), 
                        obj["Properties"]["Emission"]
                    ) 
                    for obj in data
                ]
        except:
            pass 

        self.rawData = np.array([o.Data for o in self.objects], dtype=np.float32)
        self.dataBuffer = GraphicsBuffer(self.rawData)
        

    def Run(self):
        running = True 
        frameIndex = 1
        delta = 0

        while running:
            start = time.time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.WINDOWRESIZED:
                    DestroyTexture(self.image)
                    DestroyTexture(self.accumulation)

                    self.image = CreateTexture(self.window.get_width(), self.window.get_height())
                    self.accumulation = CreateTexture(self.window.get_width(), self.window.get_height())

                    self.camera = Camera(90, self.window.get_width() / self.window.get_height(), 0.1, 100.0)

                    frameIndex = 1

            if self.camera.Update(delta):
                frameIndex = 1

            self.Compute(frameIndex)
            
            DrawImage(self.rasterProgram, self.image)

            pygame.display.flip()
            end = time.time()
            
            delta = end - start
            frameIndex += 1

    def Compute(self, frameIndex):
        glUseProgram(self.shaderProgram)

        self.dataBuffer.BindUnit(0)

        glBindImageTexture(0, self.image, 0, False, 0, GL_READ_WRITE, GL_RGBA32F)
        glBindImageTexture(1, self.accumulation, 0, False, 0, GL_READ_WRITE, GL_RGBA32F)
        glBindImageTexture(2, self.randomNumbers, 0, False, 0, GL_READ_WRITE, GL_R32UI)

        glUniform1i(glGetUniformLocation(self.shaderProgram, "OutImage"), 0)
        glUniform1i(glGetUniformLocation(self.shaderProgram, "Accumulation"), 1)
        glUniform1i(glGetUniformLocation(self.shaderProgram, "Seeds"), 2)

        iView = self.camera.InverseView
        iProjection = self.camera.InverseProjection

        perFrameData = np.array([
            *np.array(iView).flatten(),            
            *np.array(iProjection).flatten(),      
            self.camera.position.x, 
            self.camera.position.y, 
            self.camera.position.z,             
            random.randint(0, 10000000),          
            len(self.objects),                   
            frameIndex                            
        ], dtype=np.float32) 
        
        perFrameBuffer = GraphicsBuffer(perFrameData, bufferType=GL_UNIFORM_BUFFER)
        perFrameBuffer.BindUnit(1)



        glDispatchCompute(math.ceil(self.window.get_width() / 16), math.ceil(self.window.get_height() / 16), 1)
        glMemoryBarrier(GL_SHADER_IMAGE_ACCESS_BARRIER_BIT)

         

    def Shutdown(self):
        DestroyTexture(self.image)
        DestroyTexture(self.accumulation)
        DestroyTexture(self.randomNumbers)

        with open(self.save, "w") as file:
            l = [ 
                    {  
                        "Properties": {
                            "Center": o.center.to_list(),
                            "Colour": o.colour.to_list(),
                            "Radius": o.radius,
                            "Emission": o.emission
                        }
                    } 

                    for o in self.objects
                ]

            yaml.dump(l, file)
        
        pygame.quit()


if __name__ == "__main__":
    app = Application(800, 600, "save.yaml")
    app.Run()
    app.Shutdown()