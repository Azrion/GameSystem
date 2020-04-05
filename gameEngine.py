# Imports
from motionTracking import *

# Game settings
backgroundColor = BLACK
inputSize = 50 # Even number required
n_particles = 1
particleSize = 25 # Even number required
particleSpawnRandom = False
particleSpawnPos = [width/2, height/2]
particleSpawnVel = 0 # Between 0 and 1
particleSpawnAngle = 0 # Between 0 and PI*2
particleColor = GREEN
multiTouch = False
inputDrag = 0.5 # Between 0 and 1
inputSpeed = 0.1 # Between 0 and 1
drag = 0.999 # Between 0 and 1
elasticity = 0.75 # Between 0 and 1
gravity = (math.pi, 0.000)
fps = 144


# Pygame Events
def pyEvents(event):
    if event.type == KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            return sys.exit(0)
        if event.type == pygame.QUIT:
            return sys.exit(0)
    else:
        return None


# Combine vectors for movement calculation
def addVectors(angleLength1, angleLength2):
    x = math.sin(angleLength1[0]) * angleLength1[1] + math.sin(angleLength2[0]) * angleLength2[1]
    y = math.cos(angleLength1[0]) * angleLength1[1] + math.cos(angleLength2[0]) * angleLength2[1]
    angle = 0.5 * math.pi - math.atan2(y, x)
    length = math.hypot(x, y)
    return angle, length


# Colliding game object particles
def collide(p1, p2):
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
    def __init__(self, coordinates, velocity, angle, radius, objectColor):
        self.x = coordinates[0]
        self.y = coordinates[1]
        self.velocity = velocity
        self.angle = angle
        self.radius = radius
        self.objectColor = objectColor

    def draw(self, screen):
        pygame.draw.circle(screen, self.objectColor, (int(round(self.x)), int(round(self.y))), self.radius)

    def move(self):
        self.angle, self.velocity = addVectors((self.angle, self.velocity), gravity)
        self.x += math.sin(self.angle) * self.velocity
        self.y -= math.cos(self.angle) * self.velocity
        self.velocity *= drag

    def bounce(self):
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


particlesList = []
input1 = Gameobject([0, 0], 0, 0, inputSize, RED) # Init player input 1
particlesList.append(input1)
skipIdx = 0
if multiTouch:
    input2 = Gameobject([0, 0], 0, 0, inputSize, BLUE) # Init player input 2
    particlesList.append(input2)
    skipIdx = 1
for n in range(n_particles):
    if particleSpawnRandom:
        particleSpawnPos = [random.randint(particleSize, width - particleSize), random.randint(particleSize, height - particleSize)]
        particleSpawnVel = random.random()
        particleSpawnAngle = random.uniform(0, math.pi * 2)
    particle = Gameobject(particleSpawnPos, particleSpawnVel, particleSpawnAngle, particleSize, particleColor) # Init game object particle
    particlesList.append(particle)
