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
resolutionAdjuster = False
resolution = "FullHD"
gaussianBlurKSize = (21, 21) # Odd number required
thresholdValue = 10
thresholdMaxValue = 255
erodingIter = 4
dilatingIter = 8
clusteringIter = 10
clusteringEpsilon = 1.0
showContours = True
showCentroid = True
centroidSize = 25 # Even number required
displayFrames = False # Works only with showContours = True

# Setting resolutions
if resolution == "FullHD":
    width, height = 1920, 1080
elif resolution == "HD":
    width, height = 1280, 720
elif resolution == "SD":
    width, height = 1024, 576


# Display frames
def displayAllFrames(frame):
    cv2.imshow("Frame0: Raw", frame[0])
    cv2.imshow("Frame1: Gray", frame[1])
    cv2.imshow("Frame2: Blur", frame[2])
    cv2.imshow("Frame3: Delta", frame[3])
    cv2.imshow("Frame4: Threshold", frame[4])
    cv2.imshow("Frame5: Dialated", frame[5])
