"""
Physics game engine
"""

# Imports
import sys
import math
import random
from pygame.locals import *
from src.motionTracking import *

# Game settings
backgroundColor = BLACK
inputSize = 50  # Integer required
n_particles = 1
particleSize = 25  # Integer required
particleSpawnRandom = False
particleSpawnPos = [width/2, height/2]
particleSpawnVel = 0  # Between 0 and 1
particleSpawnAngle = 0  # Between 0 and (PI * 2)
particleColor = GREEN
multiTouch = True
inputAngle = 0.5  # Between 0 and 1
inputSpeed = 0.1  # Between 0 and 1
drag = 0.999  # Between 0 and 1
elasticity = 0.75  # Between 0 and 1
gravity = (math.pi, 0.000)
fps = 30


# Spawn game object particles
def spawn(pSpawnPos, pSpawnVel, pSpawnAngle):
    """
    :param pSpawnPos: initial coordinates of spawn position
    :param pSpawnVel: initial spawn velocity
    :param pSpawnAngle: initial spawn angle
    :return: array of generated game object particles and multi touch index
    """
    particlesList = []
    inputA = Gameobject([0, 0], 0, 0, inputSize, RED)  # Init player input A
    particlesList.append(inputA)
    sIdx = 0
    if multiTouch:
        inputB = Gameobject([0, 0], 0, 0, inputSize, BLUE)  # Init player input B
        particlesList.append(inputB)
        sIdx = 1
    for n in range(n_particles):
        if particleSpawnRandom:
            pSpawnPos = [random.randint(particleSize, width - particleSize),
                         random.randint(particleSize, height - particleSize)]
            pSpawnVel = random.random()
            pSpawnAngle = random.uniform(0, math.pi * 2)
        particle = Gameobject(pSpawnPos, pSpawnVel, pSpawnAngle,
                              particleSize, particleColor)  # Init game object particles
        particlesList.append(particle)
    return particlesList, sIdx


# Init pygame
def pyStart():
    """
    :return: pygame screen and clock
    """
    screen = pygame.display.set_mode((width, height), pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.FULLSCREEN)
    pygame.init()
    clock = pygame.time.Clock()
    screen.blit(pygame.transform.scale(screen, (width, height)), (0, 0))
    return screen, clock


# Pygame Events
def pyEvents(event):
    """
    :param event: pygame event
    :return: resulting event effects
    """
    if event.type == KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            return sys.exit(0)
        if event.type == pygame.QUIT:
            return sys.exit(0)
    else:
        return None


# Render and animate game object particles
def render(screen, particles):
    """
    :param screen: pygame screen
    :param particles: array of game object particles
    :return: game object particles coordinates
    """
    screen.fill(backgroundColor)
    particleCoordinates = []

    for i, ptc in enumerate(particles):
        ptc.move()
        ptc.bounce()
        for ptc2 in particles[i + 1:]:
            collide(ptc, ptc2)
        ptc.draw(screen)
        particleCoordinates.append([ptc.x, ptc.y])
    return particleCoordinates


# Calculate closest contour point to closest game object particle
def closestContour(cluster, minCoordinatesCluster, ptcCoordinates, sIdx, minDistance):
    """
    :param cluster: array of clusters' contour coordinates
    :param minCoordinatesCluster: coordinates of the clusters' closest contour point to closest game object particle
    :param ptcCoordinates: coordinates of game object particle
    :param sIdx: multi touch index
    :param minDistance: smallest distance of the clusters' closest contour point to closest game object particle
    :return: coordinates of the clusters' closest contour point to closest game object particle
    """
    distanceListCluster = []
    for i in cluster:
        distanceListCluster.append(math.sqrt((ptcCoordinates[1 + sIdx][0] - i[0]) ** 2 +
                                             (ptcCoordinates[1 + sIdx][1] - i[1]) ** 2))
        if distanceListCluster[-1] < minDistance:
            minDistance = distanceListCluster[-1]
            minCoordinatesCluster = i
    return minCoordinatesCluster


# Update attributes for input
def moveInput(minCoordinatesCluster, particles):
    """
    :param minCoordinatesCluster: coordinates of the clusters' closest contour point to closest game object particle
    :param particles: player input game object
    """
    dx1 = minCoordinatesCluster[0] - particles.x
    dy1 = minCoordinatesCluster[1] - particles.y
    particles.angle = inputAngle * math.pi + math.atan2(dy1, dx1)
    particles.velocity = math.hypot(dx1, dy1) * inputSpeed
    particles.x = minCoordinatesCluster[0]
    particles.y = minCoordinatesCluster[1]


# Combine vectors for movement calculation
def addVectors(angleLength1, angleLength2):
    """
    :param angleLength1: game object coordinate vector
    :param angleLength2: gravity vector
    :return: combined vectors for movement calculation
    """
    x = math.sin(angleLength1[0]) * angleLength1[1] + math.sin(angleLength2[0]) * angleLength2[1]
    y = math.cos(angleLength1[0]) * angleLength1[1] + math.cos(angleLength2[0]) * angleLength2[1]
    angle = 0.5 * math.pi - math.atan2(y, x)
    length = math.hypot(x, y)
    return angle, length


# Colliding game object particles
def collide(p1, p2):
    """
    :param p1: game object particle
    :param p2: game object particle
    """
    dx = p1.x - p2.x
    dy = p1.y - p2.y

    dist = math.hypot(dx, dy)
    if dist < p1.radius + p2.radius:
        tangent = math.atan2(dy, dx)
        angle = 0.5 * math.pi + tangent

        angle1 = 2 * tangent - p1.angle
        angle2 = 2 * tangent - p2.angle
        speed1 = p2.velocity * elasticity
        speed2 = p1.velocity * elasticity

        (p1.angle, p1.velocity) = (angle1, speed1)
        (p2.angle, p2.velocity) = (angle2, speed2)

        p1.x += math.sin(angle)
        p1.y -= math.cos(angle)
        p2.x -= math.sin(angle)
        p2.y += math.cos(angle)


# Define game object class
class Gameobject:
    """
    Interactive objects with the game
    """
    def __init__(self, coordinates, velocity, angle, radius, objectColor):
        self.x = coordinates[0]
        self.y = coordinates[1]
        self.velocity = velocity
        self.angle = angle
        self.radius = radius
        self.objectColor = objectColor

    def draw(self, screen):
        """
        Rendering game object
        :param screen: pygame screen
        """
        pygame.draw.circle(screen, self.objectColor, (int(round(self.x)), int(round(self.y))), self.radius)

    def move(self):
        """
        Calculating game objects' next coordinates to move in
        """
        self.angle, self.velocity = addVectors((self.angle, self.velocity), gravity)
        self.x += math.sin(self.angle) * self.velocity
        self.y -= math.cos(self.angle) * self.velocity
        self.velocity *= drag

    def bounce(self):
        """
        Bouncing game object by hitting game boundaries
        """
        if self.x > width - self.radius:
            self.x = 2 * (width - self.radius) - self.x
            self.angle = - self.angle
            self.velocity *= elasticity

        elif self.x < self.radius:
            self.x = 2 * self.radius - self.x
            self.angle = - self.angle
            self.velocity *= elasticity

        if self.y > height - self.radius:
            self.y = 2 * (height - self.radius) - self.y
            self.angle = math.pi - self.angle
            self.velocity *= elasticity

        elif self.y < self.radius:
            self.y = 2 * self.radius - self.y
            self.angle = math.pi - self.angle
            self.velocity *= elasticity
