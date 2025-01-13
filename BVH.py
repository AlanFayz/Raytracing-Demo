import heapq
import sys
from typing import Optional
from collections import deque
import random
import time
import glm
import pygame

from Objects import * 

class BVHNode:
    def __init__(self, boundingVolume: AABB):
        self.boundingVolume = boundingVolume
        self.leafNodes = []

class BVHPrimitive:
    def __init__(self, obj):
        self.bounds = AABB(obj=obj)
        self.centroid = self.bounds.Centroid
        self.object = obj


def CalculateSAH(volumeA: AABB, volumeB: AABB, outerVolume: AABB, 
                 traversalTime: float, objectIntersectTime: float, 
                 objectsA: list, objectsB: list) -> float:
    
    costA = objectIntersectTime * len(objectsA)
    costB = objectIntersectTime * len(objectsB)

    costA *= (volumeA.SurfaceArea / outerVolume.SurfaceArea)
    costB *= (volumeB.SurfaceArea / outerVolume.SurfaceArea)

    return traversalTime + costA + costB

def CalculateSAHL(volumeA: AABB, volumeB: AABB, outerVolume: AABB, 
                 traversalTime: float, objectIntersectTime: float, 
                 objectsALength: int, objectsBLength: int):
    
    costA = objectIntersectTime * objectsALength
    costB = objectIntersectTime * objectsBLength

    costA *= (volumeA.SurfaceArea / outerVolume.SurfaceArea)
    costB *= (volumeB.SurfaceArea / outerVolume.SurfaceArea)

    return traversalTime + costA + costB

def CalculateSAHLowerBound(inheritedCost: float, outerBounds, primtive, primitiveCount) -> float:
    return inheritedCost + (primtive.bounds.SurfaceArea / outerBounds.SurfaceArea) * primitiveCount

class Ray:
    def __init__(self, origin, direction):
        self.origin = origin
        self.direction = glm.normalize(direction)
        copy = glm.vec3(direction)
        copy = [sys.float_info.epsilon if x == 0 else x for x in copy]
        self.directionReciprocal = [1 / x for x in direction]

def RayBoxIntersection(ray: Ray, box: AABB) -> float:
    tminVec = (box.minn - ray.origin) * ray.directionReciprocal
    tmaxVec = (box.maxx - ray.origin) * ray.directionReciprocal

    tmin, tymin, tzmin = tminVec.x, tminVec.y, tminVec.z
    tmax, tymax, tzmax = tmaxVec.x, tmaxVec.y, tmaxVec.z

    if (tmin > tmax):
        tmin, tmax = tmax, tmin
  
    if (tymin > tymax): 
        tymin, tymax = tymax, tymin
 
    if (tmin > tymax) or (tymin > tmax):
        return -1.0
 
    if (tymin > tmin): 
        tmin = tymin

    if (tymax < tmax): 
        tmax = tymax 
  
    if (tzmin > tzmax):
        tzmin, tzmax = tzmax, tzmin
 
    if (tmin > tzmax) or (tzmin > tmax):
        return -1.0 

    if tmin < 0 and tmax < 0:
        return -1.0

    if tmin >= 0:
        return tmin

    return tmax

class BVH:
    def __init__(self):
        self.nodes = [BVHNode(AABB())]
        self.objectData = []
        self.threshold = 3
    
    def Build(self, objects):
        self.nodes.clear()
        self.objectData.clear()

        newObjects = [BVHPrimitive(obj) for obj in objects]

        bounds = AABB()
        for newObj in newObjects:
            bounds.Grow(newObj.bounds)
        
        self.BuildSAH(0, newObjects, bounds)

    def Insert(self, object_):
        primitive = BVHPrimitive(object_)

        self.nodes[0].boundingVolume.Grow(primitive.bounds)

        queue = deque([(0, 0)])
        bestCost = float("inf")

        nodeIndex = -1
    
        while queue:
            nodeIndex, inheritedCost = queue.popleft()            
            cost = CalculateSAHLowerBound(inheritedCost, self.nodes[nodeIndex].boundingVolume, 
                                          primitive, len(self.nodes[nodeIndex].leafNodes) + 1)
            
            if cost > bestCost:
                continue

            bestCost = cost 

            if self._LeftChildExists(nodeIndex):
                queue.append((self._GetLeftNodeIndex(nodeIndex),  inheritedCost + cost))

            if self._RightChildExists(nodeIndex):
                queue.append((self._GetRightNodeIndex(nodeIndex), inheritedCost + cost))
        
        if not self._TryInsert(nodeIndex, primitive):
            self.SplitAndPush(nodeIndex, primitive)

        while nodeIndex != 0:
            nodeIndex = self._GetParentNodeIndex(nodeIndex)
            self.nodes[nodeIndex].boundingVolume.Grow(primitive.bounds)

    def SplitAndPush(self, nodeIndex, primitive=None, primitiveIndex=None):
        if primitiveIndex is None and primitive is not None:
            primitiveIndex = len(self.objectData)
            self.objectData.append(primitive)

        node = self.nodes[nodeIndex]

        if primitive is not None:
            node.boundingVolume.Grow(primitive.bounds)

        axis = node.boundingVolume.MaxDimension

        centroidBounds = AABB()
        if primitive is not None:
            centroidBounds.Grow(primitive.centroid)

        for i in node.leafNodes:
            centroidBounds.Grow(self.objectData[i].centroid)

        bestCost = float("inf")
        bestLeftObjects, bestRightObjects = None, None
        bestBoundsA, bestBoundsB = None, None

        objects = node.leafNodes[:]

        if primitive is not None:
            objects.append(primitiveIndex)

        for i in range(1, 9):
            splitPosition = (centroidBounds.minn[axis] + centroidBounds.maxx[axis]) * (i / 10)

            leftObjects  = [x for x in objects if self.objectData[x].centroid[axis] < splitPosition]
            rightObjects = [x for x in objects if self.objectData[x].centroid[axis] >= splitPosition]

            boundsA = AABB()
            boundsA.GrowFromObjects(leftObjects, key=lambda x: self.objectData[x].bounds)

            boundsB = AABB()
            boundsB.GrowFromObjects(rightObjects, key=lambda x: self.objectData[x].bounds)

            cost = CalculateSAH(boundsA, boundsB, node.boundingVolume, 1, 2, leftObjects, rightObjects)

            if cost < bestCost:
                bestCost = cost
                bestLeftObjects = leftObjects
                bestRightObjects = rightObjects
                bestBoundsA = boundsA
                bestBoundsB = boundsB
        

        leftNode = self._GetLeftNode(nodeIndex)
        rightNode = self._GetRightNode(nodeIndex)

        leftNode.leafNodes.extend(bestLeftObjects)
        leftNode.boundingVolume.Grow(bestBoundsA)

        rightNode.leafNodes.extend(bestRightObjects)
        rightNode.boundingVolume.Grow(bestBoundsB)

        if len(leftNode.leafNodes) >= self.threshold:
            self.SplitAndPush(self._GetLeftNodeIndex(nodeIndex))

        if len(rightNode.leafNodes) >= self.threshold:
            self.SplitAndPush(self._GetRightNodeIndex(nodeIndex))

        node.leafNodes = []  



    def BuildSAH(self, currentNodeIndex, objects, bounds):
        while currentNodeIndex >= len(self.nodes):
            self.nodes.append(BVHNode(AABB()))
        
        node = self.nodes[currentNodeIndex]
        node.boundingVolume = bounds

        if self._TryInsertPrimitives(currentNodeIndex, objects):            
            return 

        centroidBounds = AABB()
        centroidBounds.GrowFromObjects(objects, key=lambda x: x.centroid)

        #decide which axis to split
        axis = centroidBounds.MaxDimension

        # if the axis are the same theres nothing left to split (need to think of a better fix)

        if centroidBounds.minn[axis] == centroidBounds.maxx[axis]:
            start = len(self.objectData)
            
            self.objectData.extend(objects)
            node.leafNodes.extend((i for i in range(start, len(self.objectData))))
            return 

        bestCost = float("inf")
        bestLeftObjects, bestRightObjects = None, None 
        bestBoundsA, bestBoundsB = None, None

        # 0.1 -> 0.8 
        for i in range(1, 9):
            currAxis = (centroidBounds.minn[axis] + centroidBounds.maxx[axis]) * (i / 10)

            leftObjects  = list(filter(lambda x: x.centroid[axis] <  currAxis,  objects))
            rightObjects = list(filter(lambda x: x.centroid[axis] >= currAxis, objects))

            boundsA = AABB()
            boundsA.GrowFromObjects(leftObjects, key=lambda x: x.bounds)

            boundsB = AABB()
            boundsB.GrowFromObjects(rightObjects, key=lambda x: x.bounds)

            cost = CalculateSAH(boundsA, boundsB, bounds, 1, 2, leftObjects, rightObjects)

            if cost < bestCost:
                bestCost = cost 
                bestLeftObjects = leftObjects
                bestRightObjects = rightObjects
                bestBoundsA = boundsA
                bestBoundsB = boundsB

        if bestLeftObjects:
            self.BuildSAH(self._GetLeftNodeIndex(currentNodeIndex), bestLeftObjects, bestBoundsA)
        if bestRightObjects:
            self.BuildSAH(self._GetRightNodeIndex(currentNodeIndex), bestRightObjects, bestBoundsB)


    # if hits will call function with hit function, else miss function
    # ray object function should take in a ray and its object as its two arguments
    # the result should be a tuple containing the minimum distance from the ray 
    # to the object and the user data. if an object is hit the rayHitFunction 
    # is called with user data. the ray miss function should take in the ray back
    # the result of these functions (user choice) is returned

    def TraceRay(self, ray: Ray, rayObjectFunction, rayHitFunction=None, rayMissFunction=None):
        distance = RayBoxIntersection(ray, node[0].boundingVolume)

        if distance < 0:
            if rayMissFunction:
                return rayMissFunction(ray)
            
            return None

        heap = [(distance, 0)]

        minimumDistance = float("inf")
        userData = None

        while heap:
            distance, nodeIndex = heapq.heappop(heap)

            newDistance, newUserData = self._TraceWithinBox(ray, rayObjectFunction, nodeIndex)

            if newDistance < minimumDistance:
                userData = newUserData
                minimumDistance = newDistance
                
            if self._LeftChildExists(nodeIndex):
                child = self._GetLeftNode(nodeIndex)

                distance = RayBoxIntersection(ray, child.boundingVolume)

                if distance >= 0:
                    heapq.heappush(heap, (distance, self._GetLeftNodeIndex(nodeIndex)))
            
            if self._RightChildExists(nodeIndex):
                child = self._GetRightNode(nodeIndex)
                distance = RayBoxIntersection(ray, child.boundingVolume)

                if distance >= 0:
                    heapq.heappush(heap, (distance, self._GetRightNodeIndex(nodeIndex)))
        
        if minimumDistance == float("inf"):
            if rayMissFunction:
                return rayMissFunction(ray)
        else:
            if rayHitFunction:
                return rayHitFunction(userData) 

        return None

    def _TraceWithinBox(self, ray: Ray, rayObjectFunction, nodeIndex: int):
        node = self.nodes[nodeIndex]
        minimumDistance  = float("inf")
        userData = None

        for leaf in node.leafNodes:
            primitive = self.objectData[leaf]
            
            distance, result = rayObjectFunction(ray, primitive.object)

            if distance < minimumDistance:
                minimumDistance = distance
                userData = result

        return (minimumDistance, userData)


    def _GetLeftNodeIndex(self, nodeIndex: int) -> int:
        return 2 * nodeIndex + 1
    
    def _GetRightNodeIndex(self, nodeIndex: int) -> int:
        return 2 * nodeIndex + 2
    
    def _GetParentNodeIndex(self, nodeIndex: int) -> int:
        return (nodeIndex - 1) // 2
    
    def _GetLeftNode(self, nodeIndex: int) -> BVHNode:
        leftNodeIndex = self._GetLeftNodeIndex(nodeIndex)

        while leftNodeIndex >= len(self.nodes):
            self.nodes.append(BVHNode(AABB()))

        return self.nodes[leftNodeIndex]
    
    def _GetRightNode(self, nodeIndex: int) -> BVHNode:
        rightNodeIndex = self._GetRightNodeIndex(nodeIndex)

        while rightNodeIndex >= len(self.nodes):
            self.nodes.append(BVHNode(AABB()))

        return self.nodes[rightNodeIndex]
    
    def _GetParentNode(self, nodeIndex: int) -> Optional[BVHNode]:
        parentNodeIndex = self._GetParentNodeIndex(nodeIndex)

        if parentNodeIndex < 0:
            return None    
        
        return self.nodes[parentNodeIndex]
    
    def _TryInsert(self, nodeIndex, primitive) -> bool:
        node = self.nodes[nodeIndex]

        if len(node.leafNodes) < self.threshold:
            node.leafNodes.append(len(self.objectData))
            self.objectData.append(primitive)
            return True
        
        return False
    
    def _TryInsertPrimitives(self, nodeIndex, primitives) -> bool:
        node = self.nodes[nodeIndex]

        if (len(primitives) + len(node.leafNodes)) <= self.threshold:
            start = len(self.objectData)

            self.objectData.extend(primitives)
            node.leafNodes.extend((i for i in range(start, len(self.objectData))))
            return True 
        
        return False
    
    def _LeftChildExists(self, nodeIndex) -> bool:
        return self._GetLeftNodeIndex(nodeIndex) < len(self.nodes)
    
    def _RightChildExists(self, nodeIndex) -> bool:
        return self._GetRightNodeIndex(nodeIndex) < len(self.nodes)


def DrawAABB(box: AABB, screen, color):
    pygame.draw.rect(screen, color, pygame.Rect(box.minn.x, box.minn.y, box.maxx.x - box.minn.x, box.maxx.y - box.minn.y), 2)

def DrawCircle(circle: Sphere, screen):
    pygame.draw.circle(screen, "#FF000000", (circle.center.x, circle.center.y), circle.radius, 2)

def DrawLine(start: glm.vec3, end: glm.vec3):
    pygame.draw.line(screen, "#00FF0000", glm.vec2(start).to_list(), glm.vec2(end).to_list(), 2)

def DrawRay(ray: Ray, length):
    DrawLine(ray.origin, ray.origin + ray.direction * length)

def RandomVector():
    return glm.vec3(random.randint(0, 1000), random.randint(0, 1000), random.randint(0, 1000))    


if __name__ == "__main__":
    pygame.init()

    WIDTH, HEIGHT = 1200, 800

    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("AABB and Circle Test")

    aabb = AABB(glm.vec3(100, 100, 0), glm.vec3(300, 200, 0)) 

    clock = pygame.time.Clock()

    bvh = BVH()
    primitves = []

    i = 0
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w: 
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    primitves.append(Sphere(glm.vec3(mouse_x, mouse_y, 0), 10, glm.vec3(0, 0, 0), 0.0))
                    bvh.Build(primitves)

        screen.fill("#00000000")
        
        mouse_x, mouse_y = pygame.mouse.get_pos()

        ray = Ray(glm.vec3(mouse_x, mouse_y, 0), glm.vec3(1, -1, 0.0001))

        for node in bvh.nodes:
            if RayBoxIntersection(ray, node.boundingVolume):
                DrawAABB(node.boundingVolume, screen, "#00FFFF00")
            else:
                DrawAABB(node.boundingVolume, screen, "#0000FF00")

            for leaf in node.leafNodes:
                DrawCircle(bvh.objectData[leaf].object, screen)
        
        DrawRay(ray, 1000)
                
        pygame.display.flip()

        clock.tick(60)
