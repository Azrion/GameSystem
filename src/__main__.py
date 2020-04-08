# Imports
from src.gameEngine import *
from multiprocessing import Process, Queue


# Motion Tracking Process
def motionTrackingProcess(in_queue, out_queue, sIdx):
    camera = cameraStart() # Init camera
    criteria, clusterNumber, clusterA, clusterB, center = clusterParams(multiTouch) # Init cluster parameters
    master = None
    minCoordinatesClusterA, minCoordinatesClusterB = [0, 0], [0, 0]

    while True:
        # Manipulate images
        master, contours, hierarchy, frames, result = imageProcessing(camera, master)
        if result == 'break':
            break
        elif result == 'continue':
            continue

        # RECEIVE: Data package received
        data = in_queue.get() # Receive data
        if data:
            ptcCoordinates = data[0]
        else:
            endMessage(out_queue) # Send END message
            break

        # Clustering contour points
        if len(contours) != 0:
            clusterA, clusterB, center, ret = contourClustering(contours, criteria, clusterNumber, multiTouch)

        # Input A: Calculate closest contour point to closest game object particle
        if len(clusterA) != 0:
            minDistanceA = float('inf') # Set initial minimum distance
            minCoordinatesClusterA = closestContour(clusterA, minCoordinatesClusterA,
                                                    ptcCoordinates, sIdx, minDistanceA)

        # Input B: Calculate closest contour point to closest game object particle
        if multiTouch:
            if len(clusterB) != 0:
                minDistanceB = float('inf') # Set initial minimum distance
                minCoordinatesClusterB = closestContour(clusterB, minCoordinatesClusterB,
                                                        ptcCoordinates, sIdx, minDistanceB)

        # SEND: Data package preparation
        if len(clusterA) != 0 or len(clusterB) != 0:
            dataPackage = [minCoordinatesClusterA, minCoordinatesClusterB]
            if showContours:
                dataPackage.append(clusterA)
                dataPackage.append(clusterB)
            if showCentroid:
                dataPackage.append(center)
            if displayFrames:
                dataPackage.append(frames)
            out_queue.put(dataPackage) # Send data

    camera.release() # Release camera
    cv2.destroyAllWindows() # Close all windows


# Game Engine Process
def gameEngineProcess(in_queue, out_queue, particles):
    screen, clock = pyStart() # Init pygame
    minCoordinatesClusterA, minCoordinatesClusterB = [0, 0], [0, 0]

    try:
        while True:
            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    pyEvents(event)

            moveInput(minCoordinatesClusterA, particles[0]) # Update attributes for input A
            if multiTouch:
                moveInput(minCoordinatesClusterB, particles[1])  # Update attributes for input B

            particleCoordinates = render(screen, particles) # Render and animate game object particles

            # SEND: Data package preparation
            dataPackage = [particleCoordinates]
            out_queue.put(dataPackage) # Send data

            # RECEIVE: Data package received
            data = in_queue.get() # Receive data
            if data:
                minCoordinatesClusterA = data[0] # Set coordinates smallest distance of input A found
                minCoordinatesClusterB = data[1] # Set coordinates smallest distance of input B found
                displayContours(data, screen, showContours, multiTouch) # Display contours
                displayCentroid(data, screen, showContours, showCentroid, centroidSize, multiTouch) # Display centroid
                displayAllFrames(data, showContours, showCentroid, displayFrames) # Display cameras
            else:
                break

            clock.tick(fps)
            pygame.display.flip()

    except (KeyboardInterrupt, SystemExit):
        pygame.quit() # Close simulator

    endMessage(out_queue) # Send END message
    assert in_queue.get() is None


# Send END message
def endMessage(out_queue):
    out_queue.put(None)
    out_queue.close()
    out_queue.join_thread()


# Init multiprocessing
def multiprocess(pList, sIdx):
    q1 = Queue()
    q2 = Queue()

    process_1 = Process(target=motionTrackingProcess, args=(q1, q2, sIdx)) # Init Motion Tracking Process
    process_2 = Process(target=gameEngineProcess, args=(q2, q1, pList)) # Init Game Engine Process

    process_1.start()
    process_2.start()

    process_2.join()
    process_1.join()

    q1.close()
    q2.close()

    q1.join_thread()
    q2.join_thread()


# Main function
if __name__ == "__main__":
    particlesList, skipIdx = spawn(particleSpawnPos, particleSpawnVel, particleSpawnAngle) # Spawn game object particles
    multiprocess(particlesList, skipIdx) # Init multiprocessing
