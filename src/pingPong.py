"""
Ping Pong game
"""

# Imports
import random
from src.gameEngine import *

# General game settings
backgroundColor = BLACK
middlePoint = [width / 2, height / 2]
inputSize = 50  # Integer required
n_particles = 1
particleSize = 50  # Integer required
particleSpawnRandom = False
particleSpawnPos = middlePoint
particleSpawnVel = 0  # Between 0 and 1
particleSpawnAngle = 0  # Between 0 and (PI * 2)
particleColor = GREEN
multiTouch = True

# Custom game settings
pygame.font.init()
font = pygame.font.SysFont('Helvetica', 30)  # Font name and font size
textBuffer = 500  # Distance of player name from the center of the board (used diagonally)
scoreBuffer = 50  # Distance of the score from the player name (used vertically)
textDirections = [[-1, -1], [1, -1]]
areaBorderWidth = 3  # Thickness of the drawn borders
goalBorderWidth = 25  # Thickness of the goal
goalBorderColor = GREEN  # Color of the goal
boundaries = [True, True, True, True]  # Boundaries top, bottom, left, right

# Player settings
n_players = 2  # Number of players
sPlayer = 0  # Selected player in use (simulating PSE system)
playerScore = [0 for ns in range(n_players)]  # Initial player score
playArea = [Rect(0, 0, width // 2, height), Rect(width // 2, 0, width // 2, height)]

# Difficulty settings
paddleSize = [40, 50]  # Paddle size increments
puckSpeeds = [0.65, 1]  # Puck speed increments
goalSize = [1, 0.9, 0.8, 0.7, 0.6, 0.5]  # Goal size increments
speedIndices = [1 for n in range(n_players)]
goalIndices = [0 for nG in range(n_players)]


# Spawn game object particles
def spawn(pSpawnPos, pSpawnVel, pSpawnAngle):
    """
    :param pSpawnPos: initial coordinates of spawn position
    :param pSpawnVel: initial spawn velocity
    :param pSpawnAngle: initial spawn angle
    :return: array of generated game object particles and multi touch index
    """
    particlesList = []
    inputA = Gameobject([0, 0], 0, 0, inputSize, RED, boundaries)  # Init player input A
    particlesList.append(inputA)
    if multiTouch:
        inputB = Gameobject([0, 0], 0, 0, inputSize, BLUE, boundaries)  # Init player input B
        particlesList.append(inputB)
    for n in range(n_particles):
        if particleSpawnRandom:
            pSpawnPos = [random.randint(particleSize, width - particleSize),
                         random.randint(particleSize, height - particleSize)]
            pSpawnVel = random.random()
            pSpawnAngle = random.uniform(0, math.pi * 2)
        particle = Gameobject(pSpawnPos, pSpawnVel, pSpawnAngle,
                              particleSize, particleColor, boundaries)  # Init game object particles
        particlesList.append(particle)
    return particlesList


# Init Ping Pong game
def initializeGame():
    """
    :return: text surface and position
    """
    textSurface = []
    textPosition = []
    for n in range(n_players):
        # Initialize text boxes
        playerSurface = font.render('Player: ' + str(n + 1), False, WHITE)
        moodSurface = font.render('Mood: None', False, WHITE)
        engagementSurface = font.render('Engagement: None', False, WHITE)
        scoreSurface = font.render('Score: ' + str(playerScore[n]), False, WHITE)
        goalSurface = font.render('Goal size: ' + str(int(goalSize[0] * 100)) + '%', False, WHITE)
        paddleSurface = font.render('Paddle size: ' + str(paddleSize[1]), False, WHITE)
        speedSurface = font.render('Puck speed: ' + str(int(puckSpeeds[1] * 100)) + '%', False, WHITE)
        textSurface.append([playerSurface, moodSurface, engagementSurface, scoreSurface,
                            goalSurface, paddleSurface, speedSurface])

        # Calculate positions of text boxes
        textPosition.append([a + (b * textBuffer) for (a, b) in zip(middlePoint, textDirections[n])])
        textPosition[n] = [a - b for (a, b) in zip(textPosition[n], [textSurface[n][0].get_width() // 2,
                                                                     textSurface[n][0].get_height() // 2])]
    return textSurface, textPosition


# Find surface index of the area in use
def findArea(particles):
    """
    :param particles: array of game object particles
    :return: surface index of current player
    """
    for n in range(n_players):
        isInside = playArea[n].collidepoint(particles[n_players].x, particles[n_players].y)
        if isInside:
            return n


# Ping Pong Events
def pingPongEvents(particles, mqttServ, textSurface, speedInd):
    """
    :param particles: array of game object particles
    :param mqttServ: MQTT Service
    :param textSurface: text surface
    :param speedInd: speed index
    :return: resulting difficulty event effects and updated text surface as well as speed index
    """
    # Increase paddle size
    if mqttServ.mood == "good":
        particles[sPlayer].radius = paddleSize[1]
        textSurface[sPlayer][5] = font.render('Paddle size: ' + str(paddleSize[1]), False, WHITE)
    # Decrease paddle size
    if mqttServ.mood == "bad":
        particles[sPlayer].radius = paddleSize[0]
        textSurface[sPlayer][5] = font.render('Paddle size: ' + str(paddleSize[0]), False, WHITE)
    # Increase puck speed
    if mqttServ.engagement == "high":
        speedInd[sPlayer] = 1
        textSurface[sPlayer][6] = font.render('Puck speed: ' +
                                              str(int(puckSpeeds[speedInd[sPlayer]] * 100)) + '%', False, WHITE)
    # Decrease puck speed
    if mqttServ.engagement == "low":
        speedInd[sPlayer] = 0
        textSurface[sPlayer][6] = font.render('Puck speed: ' +
                                              str(int(puckSpeeds[speedInd[sPlayer]] * 100)) + '%', False, WHITE)
    return textSurface, speedInd


# Render game results
def renderGame(screen, textSurface, textPosition, mqttServ):
    """
    :param screen: pygame screen
    :param textSurface: text surface
    :param textPosition: text position
    :param mqttServ: MQTT Service
    """
    for i in range(n_players):
        # Draw play areas
        pygame.draw.rect(screen, WHITE, playArea[i], areaBorderWidth)

        # Display player names, scores and speeds
        screen.blit(textSurface[i][0], textPosition[i])
        if mqttServ.mood is not None:
            textSurface[sPlayer][1] = font.render('Mood: ' + str(mqttServ.mood), False, WHITE)
        if mqttServ.engagement is not None:
            textSurface[sPlayer][2] = font.render('Engagement: ' + str(mqttServ.engagement), False, WHITE)
        for tSi in range(len(textSurface[i]) - 1):
            screen.blit(textSurface[i][tSi + 1], [a + b for (a, b) in zip(textPosition[i],
                                                                          [textSurface[i][0].get_rect().x,
                                                                           (tSi + 1) * scoreBuffer])])


# Reset puck to initial position
def reset(particles):
    """
    :param particles: array of game object particles
    """
    sIdx = 1
    if multiTouch:
        sIdx = 2
    for p in range(len(particles) - sIdx):
        particles[p + sIdx].x = middlePoint[0]
        particles[p + sIdx].y = middlePoint[1]
        particles[p + sIdx].velocity = 0
        particles[p + sIdx].angle = 0


# Check if a player scored
def checkGoal(screen, particles, textSurface):
    """
    :param screen: pygame screen
    :param particles: array of game object particles
    :param textSurface: text surface
    :return: updated text surface
    """
    # Define goal sizes
    sGSList = []
    for i in range(n_players):
        scaledGoalSize = height * goalSize[goalIndices[i]]
        subtractedGoalSize = height - scaledGoalSize
        sGSList.append(subtractedGoalSize)
        if (i % 2) == 0:
            pygame.draw.line(screen, goalBorderColor,
                             (0, int(subtractedGoalSize/2)), (0, height - (subtractedGoalSize/2)), goalBorderWidth)
        else:
            pygame.draw.line(screen, goalBorderColor, (width, int(subtractedGoalSize/2)),
                             (width, height - (subtractedGoalSize/2)), goalBorderWidth)
    sIdx = 1
    if multiTouch:
        sIdx = 2
    for p in range(len(particles) - sIdx):
        player = None
        # Puck hits left goal
        if particles[p + sIdx].x <= particles[p + sIdx].radius + goalBorderWidth and \
                int(sGSList[0] / 2) <= particles[p + sIdx].y <= height - (sGSList[0] / 2):
            player = 1
            # Reduce right goal size
            if goalIndices[0] < len(goalSize) - 1:
                goalIndices[0] += 1
                textSurface[player][4] = font.render('Goal size: ' + str(int(goalSize[goalIndices[0]] * 100)) + '%',
                                                     False, WHITE)
        # Puck hits right goal
        elif particles[p + sIdx].x >= width - particles[p + sIdx].radius - goalBorderWidth and \
                int(sGSList[1] / 2) <= particles[p + sIdx].y <= height - (sGSList[1] / 2):
            player = 0
            # Reduce left goal size
            if goalIndices[1] < len(goalSize) - 1:
                goalIndices[1] += 1
                textSurface[player][4] = font.render('Goal size: ' + str(int(goalSize[goalIndices[1]] * 100)) + '%',
                                                     False, WHITE)
        # Update scores and reset puck
        if player is not None:
            playerScore[player] += 1
            textSurface[player][3] = font.render('Score: ' + str(playerScore[player]), False, WHITE)
            reset(particles)
        return textSurface


# Ping Pong game function
def pingPongGame(screen, particles, mqttServ, textSurfaces, textPositions):
    """
    :param screen: pygame screen
    :param particles: array of game object particles
    :param mqttServ: MQTT Service
    :param textSurfaces: text surface
    :param textPositions: text position
    """
    textSurfaces, speedInd = pingPongEvents(particles, mqttServ, textSurfaces, speedIndices)  # Change difficulty
    # Adjust puck speed
    sIdx = 1
    if multiTouch:
        sIdx = 2
    for p in range(len(particles) - sIdx):
        if findArea(particles) is not None:
            particles[p + sIdx].speed = puckSpeeds[speedInd[findArea(particles)]]
    textSurfaces = checkGoal(screen, particles, textSurfaces)  # Check if a player scored
    renderGame(screen, textSurfaces, textPositions, mqttServ)  # Render game results
