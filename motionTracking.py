# Imports
import os
import sys
import time
import math
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
fps = 60

# Init camera
if fullHD:
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
else:
    camera = cv2.VideoCapture(0)
camera.set(3, width)
camera.set(4, height)


# Define game object class
class Gameobject:
    def __init__(self, coordinates, velocity, theta, radius, objectColor):
        self.coordinates = coordinates
        self.velocity = velocity
        self.theta = theta
        self.radius = radius
        self.objectColor = objectColor

    def draw(self):
        pygame.draw.circle(screen, self.objectColor, (int(round(self.coordinates[0])), int(round(self.coordinates[1]))), self.radius)

    def move(self):
        self.coordinates[0] += self.velocity * np.cos(self.theta)
        self.coordinates[1] += self.velocity * np.sin(self.theta)


# Define game boundary class
class Boundary:
    def __init__(self, startPoint, endPoint, objectColor, size):
        self.startPoint = startPoint
        self.endPoint = endPoint
        self.objectColor = objectColor
        self.size = size

    def draw(self):
        pygame.draw.line(screen, self.objectColor, self.startPoint, self.endPoint, self.size)


# Define player input class
class Input:
    def __init__(self, coordinates, velocity, theta, radius, objectColor):
        self.coordinates = coordinates
        self.velocity = velocity
        self.theta = theta
        self.radius = radius
        self.objectColor = objectColor
        self.centerColor = None
        self.centerCoordinates = None

    def draw(self):
        pygame.draw.circle(screen, self.objectColor, (int(round(self.coordinates[0])), int(round(self.coordinates[1]))), self.radius)

    def drawCenter(self, centerColor, centerCoordinates):
        self.centerColor = centerColor
        self.centerCoordinates = centerCoordinates
        pygame.draw.circle(screen, self.centerColor, (int(round(self.centerCoordinates[0])), int(round(self.centerCoordinates[1]))), int(round(self.radius/2)))


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
    screen.blit(pygame.transform.scale(screen, (frameWidth, frameHeight)), (0, 0))
    master = None
    minCoordinatesClusterA = [0, 0]
    minCoordinatesClusterB = [0, 0]
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, clusteringIter, clusteringEpsilon) # Define criteria for kmeans

    try:
        while True:
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

            # Render and animate game object
            gameObject.draw()
            gameObject.move()

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
                    distanceListClusterA.append(math.sqrt((gameObject.coordinates[0] - coordinatesClusterA[0]) ** 2 + (gameObject.coordinates[1] - coordinatesClusterA[1]) ** 2))
                    if distanceListClusterA[idx] < distanceListClusterA[idx - 1]:
                        minCoordinatesClusterA = coordinatesClusterA
                    if showContours:
                        pygame.draw.circle(screen, RED, (int(round(coordinatesClusterA[0])), int(round(coordinatesClusterA[1]))), 1) # Render cluster A
                    idx += 1

                idx = 0
                for i in clusterB:
                    coordinatesClusterB = i
                    distanceListClusterB.append(math.sqrt((gameObject.coordinates[0] - coordinatesClusterB[0]) ** 2 + (gameObject.coordinates[1] - coordinatesClusterB[1]) ** 2))
                    if distanceListClusterB[idx] < distanceListClusterB[idx - 1]:
                        minCoordinatesClusterB = coordinatesClusterB
                    if showContours:
                        pygame.draw.circle(screen, BLUE, (int(round(coordinatesClusterB[0])), int(round(coordinatesClusterB[1]))), 1) # Render cluster B
                    idx += 1

                if showCentroid:
                    input1.drawCenter(GOLD, center[0]) # Render centroid cluster A
                    input2.drawCenter(GOLD, center[1]) # Render centroid cluster B

            input1.coordinates = minCoordinatesClusterA
            input1.draw() # Render closest contour point of cluster A to game object
            input2.coordinates = minCoordinatesClusterB
            input2.draw() # Render closest contour point of cluster B to game object

            master = frame2 # Update master

            if displayFrames:
                displayAllFrames([frame0, frame1, frame2, frame3, frame4, frame5])

            clock.tick(fps)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        sys.exit(0)

    except (KeyboardInterrupt, SystemExit):
        pygame.quit() # Close simulator
        camera.release()  # Release camera
        cv2.destroyAllWindows() # Close all windows


if __name__ == '__main__':
    gameObject = Gameobject([50, 50], 3, 0, 50, GREEN) # Init game object
    input1 = Input([0, 0], 3, 0, 50, RED) # Init player input 1
    input2 = Input([0, 0], 3, 0, 50, BLUE) # Init player input 2
    pygame.init()
    clock = pygame.time.Clock()
    main(width, height)
