# Imports
import os
import sys
import time
import math
import random
import numpy as np
import cv2
import pygame
from pygame.locals import *

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (210, 210, 210)
RED = (255, 0, 0)
GREEN = (20, 255, 140)
BLUE = (0, 0, 255)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)

# Camera Settings
fullHD = False
width = 1920
height = 1080
time.sleep(0.5)
gaussianBlurKSize = (21, 21)
thresholdValue = 10
thresholdMaxValue = 255
erodingIter = 4
dilatingIter = 8
clusteringIter = 10
clusteringEpsilon = 1.0
showContours = True
showCentroid = True
displayFrames = False

# Game settings
screen = pygame.display.set_mode((width, height), pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.FULLSCREEN)
backgroundColor = BLACK
inputSize = 50
n_particles = 5
particleSize = 20
particleSpawnRandom = True
particleSpawnPos = [50, 50]
particleSpawnVel = 1
particleSpawnAngle = 1
particleColor = GREEN
drag = 0.999
elasticity = 0.75
gravity = (math.pi, 0.002)
fps = 144

# Init camera
if fullHD:
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
else:
    camera = cv2.VideoCapture(0)
camera.set(3, width)
camera.set(4, height)


# Combine vectors for movement calculation
def addVectors(angleLength1, angleLength2):
    x = math.sin(angleLength1[0]) * angleLength1[1] + math.sin(angleLength2[0]) * angleLength2[1]
    y = math.cos(angleLength1[0]) * angleLength1[1] + math.cos(angleLength2[0]) * angleLength2[1]
    angle = 0.5 * math.pi - math.atan2(y, x)
    length = math.hypot(x, y)
    return angle, length


# Find particle from input interaction
def findParticle(ptc, x, y):
    for p in ptc:
        if math.hypot(p.x-x, p.y-y) <= p.radius:
            return p
    return None


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
        self.centerColor = None
        self.centerX = None
        self.centerY = None

    def draw(self):
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

    def drawCenter(self, centerColor, centerCoordinates):
        self.centerColor = centerColor
        self.centerX = centerCoordinates[0]
        self.centerY = centerCoordinates[1]
        pygame.draw.circle(screen, self.centerColor, (int(round(self.centerX)), int(round(self.centerY))), int(round(self.radius/2)))


# Display frames
def displayAllFrames(frame):
    cv2.imshow("Frame0: Raw", frame[0])
    cv2.imshow("Frame1: Gray", frame[1])
    cv2.imshow("Frame2: Blur", frame[2])
    cv2.imshow("Frame3: Delta", frame[3])
    cv2.imshow("Frame4: Threshold", frame[4])
    cv2.imshow("Frame5: Dialated", frame[5])


# Game simulator
def main(frameWidth, frameHeight):
    pygame.init()
    clock = pygame.time.Clock()
    screen.blit(pygame.transform.scale(screen, (frameWidth, frameHeight)), (0, 0))
    selectedParticle = None
    master = None
    minCoordinatesClusterA = [0, 0]
    minCoordinatesClusterB = [0, 0]
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, clusteringIter, clusteringEpsilon) # Define criteria for kmeans

    try:
        while True:
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        sys.exit(0)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouseX, mouseY = pygame.mouse.get_pos()
                    selectedParticle = findParticle(particles, mouseX, mouseY)
                elif event.type == pygame.MOUSEBUTTONUP:
                    selectedParticle = None

            if selectedParticle:
                (mouseX, mouseY) = pygame.mouse.get_pos()
                dx = mouseX - selectedParticle.x
                dy = mouseY - selectedParticle.y
                selectedParticle.angle = 0.5 * math.pi + math.atan2(dy, dx)
                selectedParticle.velocity = math.hypot(dx, dy) * 0.1

            screen.fill(backgroundColor)

            (grabbed, frame0) = camera.read()  # Grab a frame
            # End of feed
            if not grabbed:
                break

            frame1 = cv2.cvtColor(frame0, cv2.COLOR_BGR2GRAY)  # Gray frame
            frame2 = cv2.GaussianBlur(frame1, gaussianBlurKSize, 0)  # Blur frame

            # Initialize master
            if master is None:
                master = frame2
                continue

            frame3 = cv2.absdiff(master, frame2)  # Delta frame
            frame4 = cv2.threshold(frame3, thresholdValue, thresholdMaxValue, cv2.THRESH_BINARY)[1]  # Threshold frame

            # Dilate the thresholded image to fill in holes
            kernel = np.ones((2, 2), np.uint8)
            frame5 = cv2.erode(frame4, kernel, iterations=erodingIter)
            frame5 = cv2.dilate(frame5, kernel, iterations=dilatingIter)

            # Find contours on thresholded image
            nada, contours, nada = cv2.findContours(frame5.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if len(contours) != 0:
                groupedListXY = []
                distanceListClusterA = []
                distanceListClusterB = []

                for i in contours:
                    for j in range(len(i)):
                        coordinates = i[j][0]
                        groupedListXY.append(coordinates)

                groupedListXY = np.float32(groupedListXY)
                ret, label, center = cv2.kmeans(groupedListXY, 2, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS) # Apply kmeans
                clusterA = groupedListXY[label.ravel() == 0]
                clusterB = groupedListXY[label.ravel() == 1]

                idx = 0
                for i in clusterA:
                    coordinatesClusterA = i
                    distanceListClusterA.append(math.sqrt((particles[2].x - coordinatesClusterA[0]) ** 2 + (particles[2].y - coordinatesClusterA[1]) ** 2))
                    if distanceListClusterA[idx] < distanceListClusterA[idx - 1]:
                        minCoordinatesClusterA = coordinatesClusterA
                    if showContours:
                        pygame.draw.circle(screen, RED, (int(round(coordinatesClusterA[0])), int(round(coordinatesClusterA[1]))), 1) # Render cluster A
                    idx += 1

                idx = 0
                for i in clusterB:
                    coordinatesClusterB = i
                    distanceListClusterB.append(math.sqrt((particles[2].x - coordinatesClusterB[0]) ** 2 + (particles[2].y - coordinatesClusterB[1]) ** 2))
                    if distanceListClusterB[idx] < distanceListClusterB[idx - 1]:
                        minCoordinatesClusterB = coordinatesClusterB
                    if showContours:
                        pygame.draw.circle(screen, BLUE, (int(round(coordinatesClusterB[0])), int(round(coordinatesClusterB[1]))), 1) # Render cluster B
                    idx += 1

                if showCentroid:
                    particles[0].drawCenter(GOLD, center[0]) # Render centroid cluster A
                    particles[1].drawCenter(GOLD, center[1]) # Render centroid cluster B

            # Render and animate game object
            for i, ptc in enumerate(particles):
                if i == 0:
                    ptc.x, ptc.y = minCoordinatesClusterA # Update position for input 1
                if i == 1:
                    ptc.x, ptc.y = minCoordinatesClusterB # Update position for input 2
                ptc.move()
                ptc.bounce()
                for ptc2 in particles[i + 1:]:
                    collide(ptc, ptc2)
                ptc.draw()

            master = frame2 # Update master

            if displayFrames:
                displayAllFrames([frame0, frame1, frame2, frame3, frame4, frame5])

            clock.tick(fps)
            pygame.display.flip()

    except (KeyboardInterrupt, SystemExit):
        pygame.quit() # Close simulator
        camera.release()  # Release camera
        cv2.destroyAllWindows() # Close all windows


# Main function
if __name__ == '__main__':
    particles = []
    input1 = Gameobject([0, 0], 0, 0, inputSize, RED)  # Init player input 1
    input2 = Gameobject([0, 0], 0, 0, inputSize, BLUE)  # Init player input 2
    particles.append(input1)
    particles.append(input2)
    for n in range(n_particles):
        if particleSpawnRandom:
            particleSpawnPos = [random.randint(particleSize, width - particleSize), random.randint(particleSize, height - particleSize)]
            particleSpawnVel = random.random()
            particleSpawnAngle = random.uniform(0, math.pi * 2)
        particle = Gameobject(particleSpawnPos, particleSpawnVel, particleSpawnAngle, particleSize, particleColor) # Init game object particle
        particles.append(particle)
    main(width, height)
