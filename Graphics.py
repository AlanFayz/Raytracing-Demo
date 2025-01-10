from OpenGL.GL import *

import numpy as np

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

def DestroyBuffer(bufferID):
    glDeleteBuffers(1, [bufferID])

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