# Imports
from gameEngine import *
from multiprocessing import Process, Queue, Array


# Motion Tracking Process
def motionTrackingProcess(in_queue, out_queue, sIdx):
    # Init camera
    if resolutionAdjuster:
        camera = cv2.VideoCapture(0)
    else:
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    screen = None
    clock = None

    if showContours:
        screen = pygame.display.set_mode((width, height), pygame.DOUBLEBUF | pygame.HWSURFACE)
        pygame.init()
        clock = pygame.time.Clock()
        screen.blit(pygame.transform.scale(screen, (width, height)), (0, 0))

    master = None
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, clusteringIter, clusteringEpsilon) # Define criteria for kmeans
    clusterNumber = 1
    if multiTouch:
        clusterNumber = 2
    minCoordinatesClusterA = [0, 0]
    minCoordinatesClusterB = [0, 0]
    minDistanceA = float('inf')
    minDistanceB = float('inf')

    try:
        while True:
            if showContours:
                for event in pygame.event.get():
                    pyEvents(event)

            if showContours:
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

            frame3 = cv2.absdiff(master, frame2) # Delta frame
            frame4 = cv2.threshold(frame3, thresholdValue, thresholdMaxValue, cv2.THRESH_BINARY)[1] # Threshold frame

            # Dilate the thresholded image to fill in holes
            kernel = np.ones((2, 2), np.uint8)
            frame5 = cv2.erode(frame4, kernel, iterations=erodingIter)
            frame5 = cv2.dilate(frame5, kernel, iterations=dilatingIter)

            # Find contours on thresholded image
            nada, contours, nada = cv2.findContours(frame5.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            data = in_queue.get() # Receive data
            if data:
                ptcCoordinates = data
            else:
                # Send END message
                out_queue.put(None)
                out_queue.close()
                out_queue.join_thread()
                break

            if len(contours) != 0:
                groupedListXY = []
                distanceListClusterA = []
                distanceListClusterB = []

                for i in contours:
                    for j in range(len(i)):
                        coordinates = i[j][0]
                        groupedListXY.append(coordinates)

                groupedListXY = np.float32(groupedListXY)
                ret, label, center = cv2.kmeans(groupedListXY, clusterNumber, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS) # Apply kmeans
                clusterA = groupedListXY[label.ravel() == 0] # Cluster Input A
                if multiTouch:
                    clusterB = groupedListXY[label.ravel() == 1] # Cluster Input B

                idx = 0
                for i in clusterA:
                    coordinatesClusterA = i
                    distanceListClusterA.append(math.sqrt((ptcCoordinates[1+sIdx][0] - coordinatesClusterA[0]) ** 2 + (ptcCoordinates[1+sIdx][0] - coordinatesClusterA[1]) ** 2))
                    if distanceListClusterA[-1] < minDistanceA:
                        minDistanceA = distanceListClusterA[-1]
                        minCoordinatesClusterA = coordinatesClusterA
                    if showContours:
                        pygame.draw.circle(screen, RED, (int(round(coordinatesClusterA[0])), int(round(coordinatesClusterA[1]))), 1) # Render cluster A
                    idx += 1

                if multiTouch:
                    idx = 0
                    for i in clusterB:
                        coordinatesClusterB = i
                        distanceListClusterB.append(math.sqrt((ptcCoordinates[1+sIdx][0] - coordinatesClusterB[0]) ** 2 + (ptcCoordinates[1+sIdx][0] - coordinatesClusterB[1]) ** 2))
                        if distanceListClusterB[-1] < minDistanceB:
                            minDistanceB = distanceListClusterB[-1]
                            minCoordinatesClusterB = coordinatesClusterB
                        if showContours:
                            pygame.draw.circle(screen, BLUE, (int(round(coordinatesClusterB[0])), int(round(coordinatesClusterB[1]))), 1) # Render cluster B
                        idx += 1

                if showContours:
                    if showCentroid:
                        pygame.draw.circle(screen, GOLD, (int(round(center[0][0])), int(round(center[0][1]))), centroidSize) # Render centroid cluster A
                        if multiTouch:
                            pygame.draw.circle(screen, GOLD, (int(round(center[1][0])), int(round(center[1][1]))), centroidSize) # Render centroid cluster B

            out_queue.put([minCoordinatesClusterA, minCoordinatesClusterB])  # Send data

            # Reset minimum distances
            minDistanceA = float('inf')
            minDistanceB = float('inf')

            master = frame2 # Update master

            if displayFrames:
                displayAllFrames([frame0, frame1, frame2, frame3, frame4, frame5])

            if showContours:
                clock.tick(fps)
                pygame.display.flip()

    except (KeyboardInterrupt, SystemExit):
        if showContours:
            pygame.quit() # Close simulator
        camera.release() # Release camera
        cv2.destroyAllWindows() # Close all windows


# Game Engine Process
def gameEngineProcess(in_queue, out_queue, particles):
    screen = pygame.display.set_mode((width, height), pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.FULLSCREEN)
    pygame.init()
    clock = pygame.time.Clock()
    screen.blit(pygame.transform.scale(screen, (width, height)), (0, 0))
    minCoordinatesClusterA = [0, 0]
    minCoordinatesClusterB = [0, 0]
    particleCoordinates = []

    try:
        while True:
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    pyEvents(event)

            # Update position for input 1 and input 2
            dx1 = minCoordinatesClusterA[0] - particles[0].x
            dy1 = minCoordinatesClusterA[1] - particles[0].y
            particles[0].x = minCoordinatesClusterA[0]
            particles[0].y = minCoordinatesClusterA[1]
            particles[0].angle = inputDrag * math.pi + math.atan2(dy1, dx1)
            particles[0].velocity = math.hypot(dx1, dy1) * inputSpeed

            if multiTouch:
                dx2 = minCoordinatesClusterB[0] - particles[1].x
                dy2 = minCoordinatesClusterB[1] - particles[1].y
                particles[1].x = minCoordinatesClusterB[0]
                particles[1].y = minCoordinatesClusterB[1]
                particles[1].angle = inputDrag * math.pi + math.atan2(dy2, dx2)
                particles[1].velocity = math.hypot(dx2, dy2) * inputSpeed

            screen.fill(backgroundColor)

            # Render and animate game object
            for i, ptc in enumerate(particles):
                ptc.move()
                ptc.bounce()
                for ptc2 in particles[i + 1:]:
                    collide(ptc, ptc2)
                ptc.draw(screen)
                particleCoordinates.append([ptc.x, ptc.y])

            out_queue.put(particleCoordinates) # Send data
            data = in_queue.get() # Receive data
            if data:
                minCoordinatesClusterA = data[0]
                minCoordinatesClusterB = data[1]
            else:
                break

            clock.tick(fps)
            pygame.display.flip()

    except (KeyboardInterrupt, SystemExit):
        pygame.quit() # Close simulator

    # Send END message
    out_queue.put(None)
    out_queue.close()
    out_queue.join_thread()
    assert in_queue.get() is None


# Main function
if __name__ == "__main__":
    q1 = Queue()
    q2 = Queue()

    process_1 = Process(target=motionTrackingProcess, args=(q1, q2, skipIdx))
    process_2 = Process(target=gameEngineProcess, args=(q2, q1, particlesList))

    process_1.start()
    process_2.start()

    process_2.join()
    process_1.join()

    q1.close()
    q2.close()

    q1.join_thread()
    q2.join_thread()
