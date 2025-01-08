import numpy as np
import math

class Vector:
    def __init__(self, data):
        if isinstance(data, Vector):
            self.__data = np.array(data.__data)
        else:
            self.__data = np.array(data, dtype=np.float32)

    def magnitude(self) -> float:
        return np.linalg.norm(self.__data)

    def size(self) -> int:
        return self.__data.size

    def __getitem__(self, index: int) -> float:
        return self.__data[index]

    def __setitem__(self, index: int, value: float):
        self.__data[index] = value

    def __str__(self) -> str:
        return str(self.__data.tolist())

    def __add__(self, other) -> 'Vector':
        if not isinstance(other, Vector):
            raise TypeError("other type should be vector")
        return Vector(self.__data + other.__data)

    def __sub__(self, other) -> 'Vector':
        if not isinstance(other, Vector):
            raise TypeError("other type should be vector")
        return Vector(self.__data - other.__data)

    def __neg__(self) -> 'Vector':
        return Vector(-self.__data)

    def __mul__(self, other) -> 'Vector':
        if isinstance(other, Vector):
            return Vector(self.__data * other.__data)
        elif isinstance(other, (float, int)):
            return Vector(self.__data * other)
        else:
            raise TypeError("other type should be vector or float")

    def __truediv__(self, other) -> 'Vector':
        if isinstance(other, Vector):
            if np.any(other.__data == 0):
                raise ZeroDivisionError("division by zero")
            return Vector(self.__data / other.__data)
        elif isinstance(other, (float, int)):
            if other == 0:
                raise ZeroDivisionError("division by zero")
            return Vector(self.__data / other)
        else:
            raise TypeError("other type should be vector or float")

    def __floordiv__(self, other) -> 'Vector':
        if isinstance(other, Vector):
            if np.any(other.__data == 0):
                raise ZeroDivisionError("division by zero")
            return Vector(self.__data // other.__data)
        else:
            raise TypeError("other type should be vector")

    def getData(self):
        return self.__data.flatten()

def cross2(vector1: Vector, vector2: Vector) -> float:
    if vector1.size() != 2 or vector2.size() != 2:
        raise ValueError("both vectors must have 2 components")
    return vector1[0] * vector2[1] - vector1[1] * vector2[0]


def cross(vector1: Vector, vector2: Vector) -> Vector:
    if vector1.size() != 3 or vector2.size() != 3:
        raise ValueError("both vectors must have 3 components")
    x = vector1[1] * vector2[2] - vector1[2] * vector2[1]
    y = vector1[2] * vector2[0] - vector1[0] * vector2[2]
    z = vector1[0] * vector2[1] - vector1[1] * vector2[0]
    return Vector((x, y, z))

def dot(vector1: Vector, vector2: Vector) -> float:
    if vector1.size() != vector2.size():
        raise ValueError("both vectors must have the same size")
    return np.dot(vector1.__data, vector2.__data)

def normalize(vector: Vector) -> Vector:
    magnitude = vector.magnitude()
    if magnitude == 0.0:
        raise ValueError("cannot normalize a zero vector")
    return Vector(vector.__data / magnitude)

def distance(vector1: Vector, vector2: Vector) -> float:
    difference = vector2 - vector1
    return difference.magnitude()

def lerp(vector: Vector, end: Vector, scale: float) -> Vector:
    return vector + (end - vector) * scale

def clamp(vector: Vector, minn: Vector, maxx: Vector) -> Vector:
    if vector.size() != minn.size() or vector.size() != maxx.size():
        raise ValueError("invalid sizes")
    return Vector(np.clip(vector.__data, minn.__data, maxx.__data))
