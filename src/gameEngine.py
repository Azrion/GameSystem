"""
Physics game engine
"""

# Imports
import sys
from pygame.locals import *
from src.motionTracking import *

# Physics settings
inputAngle = 0.5  # Between 0 and 1
inputSpeed = 0.8  # Between 0 and 1
drag = 0.9  # Between 0 and 1
elasticity = 0.75  # Between 0 and 1
gravity = (math.pi, 0.000)
fps = 30


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
    """
    for i, ptc in enumerate(particles):
        ptc.move()
        ptc.bounce()
        for ptc2 in particles[i + 1:]:
            collide(ptc, ptc2)
        ptc.draw(screen)


# Calculate closest contour point to closest game object particle
def closestContour(cluster, ptcCoordinates, distanceRadius, multiTouch):
    """
    :param cluster: array of clusters' contour coordinates
    :param ptcCoordinates: coordinates of game object particle
    :param distanceRadius: distance of both game object particle and input sizes
    :param multiTouch: boolean about enabling multi touch
    :return: coordinates of the clusters' closest contour point to closest game object particle
    """
    minCoordinatesCluster = [0, 0]
    minDistance = float('inf')  # Set initial minimum distance
    distanceListCluster = []
    sIdx = 1
    if multiTouch:
        sIdx = 2
    for i in range(len(ptcCoordinates) - sIdx):
        for j in cluster:
            distanceListCluster.append(math.sqrt((ptcCoordinates[sIdx + i][0] - j[0]) ** 2 +
                                                 (ptcCoordinates[sIdx + i][1] - j[1]) ** 2))
            if minDistance > distanceListCluster[-1] >= distanceRadius:
                minDistance = distanceListCluster[-1]
                minCoordinatesCluster = j
    return minCoordinatesCluster


# Remove n dimensions
def listDimensionRemover(processList, numberOfDimensions):
    """
    :param processList: list array
    :param numberOfDimensions: number of dimensions to flatten
    :return: flattened list by n dimensions
    """
    flat_list = [item for sublist in processList for item in sublist]
    if numberOfDimensions == 1:
        return flat_list
    return listDimensionRemover(flat_list, numberOfDimensions - 1)


# Update attributes for input
def moveInput(minCoordinatesCluster, selected_particle):
    """
    :param minCoordinatesCluster: coordinates of the clusters' closest contour point to closest game object particle
    :param selected_particle: selected game object particle
    """
    dx1 = minCoordinatesCluster[0] - selected_particle.x
    dy1 = minCoordinatesCluster[1] - selected_particle.y
    selected_particle.angle = inputAngle * math.pi + math.atan2(dy1, dx1)
    selected_particle.velocity = math.hypot(dx1, dy1) * inputSpeed


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
    def __init__(self, coordinates, velocity, angle, radius, objectColor, boundaries):
        self.x = coordinates[0]
        self.y = coordinates[1]
        self.velocity = velocity
        self.angle = angle
        self.radius = radius
        self.objectColor = objectColor
        self.boundaries = boundaries

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
        # Right boundary
        if self.x > width - self.radius:
            if self.boundaries[1]:
                self.x = 2 * (width - self.radius) - self.x
                self.angle = - self.angle
                self.velocity *= elasticity

        # Left boundary
        elif self.x < self.radius:
            if self.boundaries[0]:
                self.x = 2 * self.radius - self.x
                self.angle = - self.angle
                self.velocity *= elasticity

        # Top boundary
        if self.y > height - self.radius:
            if self.boundaries[2]:
                self.y = 2 * (height - self.radius) - self.y
                self.angle = math.pi - self.angle
                self.velocity *= elasticity

        # Bottom boundary
        elif self.y < self.radius:
            if self.boundaries[3]:
                self.y = 2 * self.radius - self.y
                self.angle = math.pi - self.angle
                self.velocity *= elasticity
