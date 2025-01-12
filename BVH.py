
from collections import deque
from os import utime
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
    



class BVH:
    def __init__(self):
        self.nodes = [BVHNode(AABB())]
        self.objectData = []
        self.threshold = 2
    
    def Build(self, objects):
        self.nodes.clear()
        self.objectData.clear()

        newObjects = [BVHPrimitive(obj) for obj in objects]

        bounds = AABB()
        for newObj in newObjects:
            bounds.Grow(newObj.bounds)
        
        self.BuildSAH(0, newObjects, bounds)

    def BuildSAH(self, currentNodeIndex, objects, bounds):
        self.nodes.extend([BVHNode(AABB()) for _ in range(max(currentNodeIndex - len(self.nodes) + 1, 0))])
        
        node = self.nodes[currentNodeIndex]
        node.boundingVolume = bounds

        if len(objects) <= self.threshold:
            start = len(self.objectData)
            
            self.objectData.extend(objects)
            node.leafNodes.extend((i for i in range(start, len(self.objectData))))
            return 


        # tuple(surface area heurstic, volumeA, volumeB)

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
            self.BuildSAH(2 * currentNodeIndex + 1, bestLeftObjects, bestBoundsA)
        if bestRightObjects:
            self.BuildSAH(2 * currentNodeIndex + 2, bestRightObjects, bestBoundsB)

        
def DrawAABB(box: AABB, screen):
    pygame.draw.rect(screen, "#0000FF00", pygame.Rect(box.minn.x, box.minn.y, box.maxx.x - box.minn.x, box.maxx.y - box.minn.y), 2)

def DrawCircle(circle: Sphere, screen):
    pygame.draw.circle(screen, "#FF000000", (circle.center.x, circle.center.y), circle.radius, 2)

def RandomVector():
    return glm.vec3(random.randint(0, 1000), random.randint(0, 1000), random.randint(0, 1000))


def printNode(value, index, level):
    print(f"Value: {value}, Index: {index}, Level {level}")
    
def Bfs(tree: BVH, function):
    if not tree.nodes:
        return

    queue = deque([(tree.nodes[0], 0)])  
    level = 0 
    
    while queue:
        levelSize = len(queue)  
        
        for i in range(levelSize):
            value, index = queue.popleft()
            function(value, index, level, i) 

            leftNode = index * 2 + 1
            rightNode = index * 2 + 2

            if leftNode < len(tree.nodes):
                queue.append((tree.nodes[leftNode], leftNode))

            if rightNode < len(tree.nodes):
                queue.append((tree.nodes[rightNode], rightNode))

        level += 1


if __name__ == "__main__":
    pygame.init()

    WIDTH, HEIGHT = 1200, 800


    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("AABB and Circle Test")

    aabb = AABB(glm.vec3(100, 100, 0), glm.vec3(300, 200, 0)) 

    clock = pygame.time.Clock()

    bvh = BVH()

    objects = []


    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()


            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w: 
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    objects.append(Sphere(glm.vec3(mouse_x, mouse_y, 0), 30, glm.vec3(0, 0, 0), 0.0))
                    bvh.Build(objects[:])
            

        screen.fill("#00000000")

        for node in bvh.nodes:
            DrawAABB(node.boundingVolume, screen)
    
        for circle in bvh.objectData:
            DrawCircle(circle.object, screen)


        pygame.display.flip()

        clock.tick(60)
