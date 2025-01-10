import os
from typing import Tuple
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram, ShaderProgram


class ShaderCompiler:
    @staticmethod
    def Compile(*shaders: Tuple[str, int]) -> ShaderProgram:
        shaderIDs = [
            compileShader(ShaderCompiler.RecursiveShaderRead(filename), shaderType) 
            for filename, shaderType in shaders
        ]

        return compileProgram(*shaderIDs)

    @staticmethod
    def RecursiveShaderRead(fileName: str, seenFiles: list = None) -> str:
        if not seenFiles:
            seenFiles = []

        absolutePath = ""
        code = ""

        try:
            with open(fileName, "r") as file:
                code = file.read()
                absolutePath = os.path.abspath(file.name)

        except FileNotFoundError:
            if not seenFiles:
                raise FileNotFoundError(f"file '{fileName}' could not be located.")
            
            parent = os.path.join(os.path.dirname(seenFiles[-1]), fileName)
            
            try:
                with open(parent, "r") as file:
                    code = file.read()
                    absolutePath = os.path.abspath(file.name)

            except FileNotFoundError:
                raise FileNotFoundError(f"file '{fileName}' could not be located.")
                
        
        if absolutePath in seenFiles:
            raise Error(f"recursive inclusion with file '{absolutePath}'")
        
        seenFiles.append(absolutePath)

        index = code.find("#include")

        while index > -1:
            first = code.find("\"", index)

            if first == -1:
                raise ValueError(f"missing opening \" after #include in {fileName}")

            second = code.find("\"", first + 1)

            if second == -1:
                raise ValueError(f"missing closing \" after #include in {fileName}")

            newFileName = code[first + 1:second]

            includedCode = ShaderCompiler.RecursiveShaderRead(newFileName, seenFiles[:])

            includeDirective = code[index:second + 1]  
            code = code.replace(includeDirective, includedCode)

            index = code.find("#include", index + len(includedCode))

        return code
    
    