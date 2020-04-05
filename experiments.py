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
#camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
camera = cv2.VideoCapture(0)
width = 1920
height = 1080
camera.set(3, width)
camera.set(4, height)
time.sleep(0.5)
gaussianBlurKSize = (21, 21)
thresholdValue = 10
thresholdMaxValue = 255
erodingIter = 4
dilatingIter = 8
displayFrames = False

# Game settings
clock = pygame.time.Clock()
screen = pygame.display.set_mode((width, height), pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.FULLSCREEN)
backgroundColor = BLACK
fps = 30


# Define game object class
class Rigidbody:
    def __init__(self, coordinates, velocity, theta, radius, objectColor):
        self.x = coordinates[0]
        self.y = coordinates[1]
        self.velocity = velocity
        self.theta = theta
        self.radius = radius
        self.objectColor = objectColor

    def draw(self):
        pygame.draw.circle(screen, self.objectColor, (int(round(self.x)), int(round(self.y))), self.radius)

    def move(self):
        self.x += self.velocity * np.cos(self.theta)
        self.y += self.velocity * np.sin(self.theta)


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
    minCoordinatesA = [0, 0]
    minCoordinatesB = [0, 0]
    minDistanceA = float('inf')
    minDistanceB = float('inf')
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)  # Define criteria for kmeans

    try:
        while True:
            screen.fill(backgroundColor)

            (grabbed, frame0) = camera.read() # Grab a frame
            # End of feed
            if not grabbed:
                break

            frame1 = cv2.cvtColor(frame0, cv2.COLOR_BGR2GRAY) # Gray frame
            frame2 = cv2.GaussianBlur(frame1, gaussianBlurKSize, 0) # Blur frame

            # Initialize master
            if master is None:
                master = frame2
                continue

            frame3 = cv2.absdiff(master, frame2)  # Delta frame
            frame4 = cv2.threshold(frame3, thresholdValue, thresholdMaxValue, cv2.THRESH_BINARY)[1] # Threshold frame

            # Dilate the thresholded image to fill in holes
            kernel = np.ones((2, 2), np.uint8)
            frame5 = cv2.erode(frame4, kernel, iterations=erodingIter)
            frame5 = cv2.dilate(frame5, kernel, iterations=dilatingIter)

            # Render  game object
            rigidbody.draw()

            # Find contours on thresholded image
            nada, contours, nada = cv2.findContours(frame5.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            distanceListA = []
            distanceListB = []

            if len(contours) != 0:
                groupedListXY = []

                for i in contours:
                    for j in range(len(i)):
                        coordinates = i[j][0]
                        groupedListXY.append(coordinates)

                groupedListXY = np.float32(groupedListXY)
                ret, label, center = cv2.kmeans(groupedListXY, 2, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS) # Apply kmeans
                clusterA = groupedListXY[label.ravel() == 0] # Cluster Input A
                clusterB = groupedListXY[label.ravel() == 1] # Cluster Input B

            if len(clusterA) != 0:
                for i in clusterA:
                    coordinates = i
                    distanceListA.append(math.sqrt((rigidbody.x - coordinates[0]) ** 2 + (rigidbody.y - coordinates[1]) ** 2))
                    pygame.draw.circle(screen, RED, coordinates, 1, 0) # Render cluster A
                    if distanceListA[-1] < minDistanceA:
                        minDistanceA = distanceListA[-1]
                        minCoordinatesA = coordinates
                pygame.draw.circle(screen, RED, minCoordinatesA, 50, 0) # Render cluster A closest Point
                minDistanceA = float('inf')
            pygame.draw.circle(screen, GOLD, (int(round(center[0][0])), int(round(center[0][1]))), 25)  # Render centroid cluster A

            if len(clusterB) != 0:
                for i in clusterB:
                    coordinates = i
                    distanceListB.append(math.sqrt((rigidbody.x - coordinates[0]) ** 2 + (rigidbody.y - coordinates[1]) ** 2))
                    pygame.draw.circle(screen, BLUE, coordinates, 1, 0) # Render cluster B
                    if distanceListB[-1] < minDistanceB:
                        minDistanceB = distanceListB[-1]
                        minCoordinatesB = coordinates
                pygame.draw.circle(screen, BLUE, minCoordinatesB, 50, 0) # Render cluster B closest Point
                minDistanceB = float('inf')
            pygame.draw.circle(screen, GOLD, (int(round(center[1][0])), int(round(center[1][1]))), 25)  # Render centroid cluster B

            # Update master
            master = frame2

            # Display frames
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
        camera.release() # Release camera
        cv2.destroyAllWindows() # Close all windows


if __name__ == '__main__':
    rigidbody = Rigidbody([width/2, height/2], 3, 0, 50, GREEN) # Init game object
    pygame.init()
    main(width, height)
