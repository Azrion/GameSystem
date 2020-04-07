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
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

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
resolutionAutodetect = True
resolution = "FullHD"
gaussianBlurKSize = (31, 31) # Odd number required
thresholdValue = 20
thresholdMaxValue = 255
erodingIter = 4
dilatingIter = 8
clusteringIter = 10
clusteringEpsilon = 1.0
showContours = True
showCentroid = True
centroidSize = 25 # Integer required
displayFrames = False

# Setting resolutions
if resolution == "FullHD":
    width, height = 1920, 1080
elif resolution == "HD":
    width, height = 1280, 720
elif resolution == "SD":
    width, height = 1024, 576


# Init camera
def cameraStart():
    if resolutionAutodetect:
        camera = cv2.VideoCapture(0)
    else:
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return camera


# Manipulate images
def imageProcessing(camera, master):
    (grabbed, frame0) = camera.read() # Grab a frame
    if not grabbed: # End of feed
        return None, None, None, None, 'break'

    frame1 = cv2.cvtColor(frame0, cv2.COLOR_BGR2GRAY) # Gray frame
    frame2 = cv2.GaussianBlur(frame1, gaussianBlurKSize, 0) # Blur frame

    # Initialize master
    if master is None:
        master = frame2
        return master, None, None, None, 'continue'

    frame3 = cv2.absdiff(master, frame2) # Delta frame
    frame4 = cv2.threshold(frame3, thresholdValue, thresholdMaxValue, cv2.THRESH_BINARY)[1] # Threshold frame

    # Dilate the thresholded image to fill in holes
    kernel = np.ones((2, 2), np.uint8)
    frame5 = cv2.erode(frame4, kernel, iterations=erodingIter)
    frame5 = cv2.dilate(frame5, kernel, iterations=dilatingIter)

    # Find contours on thresholded image
    contours, hierarchy = cv2.findContours(frame5.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    master = frame2  # Update master
    frames = [frame0, frame1, frame2, frame3, frame4, frame5] # Collect frames
    return master, contours, hierarchy, frames, 'None'


# Init cluster parameters
def clusterParams(multiTouch):
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                clusteringIter, clusteringEpsilon) # Define criteria for kmeans
    clusterA = []
    clusterB = []
    center = []
    clusterNumber = 1
    if multiTouch:
        clusterNumber = 2
    return criteria, clusterNumber, clusterA, clusterB, center


# Clustering contour points
def contourClustering(contours, criteria, clusterNumber, multiTouch):
    groupedListXY = []
    for i in contours:
        for j in range(len(i)):
            groupedListXY.append(i[j][0]) # Save contour point coordinates

    groupedListXY = np.float32(groupedListXY)
    ret, label, center = cv2.kmeans(groupedListXY, clusterNumber, None,
                                    criteria, 10, cv2.KMEANS_RANDOM_CENTERS) # Apply kmeans clustering
    clusterA = groupedListXY[label.ravel() == 0] # Cluster input A
    clusterB = []
    if multiTouch:
        clusterB = groupedListXY[label.ravel() == 1] # Cluster input B
    return clusterA, clusterB, center, ret


# Display contours
def displayContours(data, screen, sContours, multiTouch):
    if sContours:
        for i in range(len(data[2])):
            pygame.draw.circle(screen, RED, (int(round(data[2][i][0])),
                                             int(round(data[2][i][1]))), 1) # Render cluster A
        if multiTouch:
            for i in range(len(data[3])):
                pygame.draw.circle(screen, BLUE, (int(round(data[3][i][0])),
                                                  int(round(data[3][i][1]))), 1) # Render cluster B


# Display centroid
def displayCentroid(data, screen, sContours, sCentroid, cSize, multiTouch):
    if sCentroid:
        cidx = 4
        if sContours is False:
            cidx = 2
        pygame.draw.circle(screen, GOLD, (int(round(data[cidx][0][0])),
                                          int(round(data[cidx][0][1]))), cSize) # Render centroid cluster A
        if multiTouch:
            pygame.draw.circle(screen, GOLD, (int(round(data[cidx][1][0])),
                                              int(round(data[cidx][1][1]))), cSize) # Render centroid cluster B


# Display cameras
def displayAllFrames(data, sContours, sCentroid, dFrames):
    if dFrames:
        fidx = 5
        if sContours is False:
            fidx = 3
        if sCentroid is False:
            fidx = 4
        if sContours is False and sCentroid is False:
            fidx = 2
        cv2.imshow("Frame0: Raw", data[fidx][0])
        cv2.imshow("Frame1: Gray", data[fidx][1])
        cv2.imshow("Frame2: Blur", data[fidx][2])
        cv2.imshow("Frame3: Delta", data[fidx][3])
        cv2.imshow("Frame4: Threshold", data[fidx][4])
        cv2.imshow("Frame5: Dialated", data[fidx][5])
