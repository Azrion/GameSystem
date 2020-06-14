"""
Ping Pong game
"""

# Imports
import random
from src.gameEngine import *

# General game settings
backgroundColor = BLACK
middlePoint = [width/2, height/2]
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
textBuffer = 200  # Distance of player name from the center of the board (used diagonally)
scoreBuffer = 50  # Distance of the score from the player name (used vertically)
textDirections = [[-1, -1], [1, -1]]
areaBorderWidth = 3  # Thickness of the drawn borders
boundaries = [False, False, True, True]  # Boundaries top, bottom, left, right,

# Player settings
n_players = 2
playerScore = [0 for ns in range(n_players)]  # Initial player score
playArea = [Rect(0, 0, width//2, height), Rect(width//2, 0, width//2, height)]

# Puck settings
puckSpeeds = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75]  # Puck speed increments
speedIndices = [3 for ni in range(n_players)]  # Initial puck speed


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


def initializeGame():
    textSurface = []
    textPosition = []
    for n in range(n_players):
        # Initialize text boxes
        playerSurface = font.render('Player: ' + str(n+1), False, WHITE)
        scoreSurface = font.render('Score: ' + str(playerScore[n]), False, WHITE)
        speedSurface = font.render('Speed: ' + str(puckSpeeds[speedIndices[n]]), False, WHITE)
        textSurface.append([playerSurface, scoreSurface, speedSurface])

        # Calculate positions of text boxes
        textPosition.append([a + (b * textBuffer) for (a, b) in zip(middlePoint, textDirections[n])])
        textPosition[n] = [a - b for (a, b) in zip(textPosition[n], [textSurface[n][0].get_width() // 2,
                                                                     textSurface[n][0].get_height() // 2])]
    return textSurface, textPosition


def renderGame(screen, textSurface, textPosition):
    for i in range(n_players):
        # Draw play areas
        pygame.draw.rect(screen, WHITE, playArea[i], areaBorderWidth)

        # Display player names, scores and speeds
        screen.blit(textSurface[i][0], textPosition[i])
        screen.blit(textSurface[i][1],
                    [a + b for (a, b) in zip(textPosition[i], [textSurface[i][0].get_rect().x, 2 * scoreBuffer])])
        screen.blit(textSurface[i][2],
                    [a + b for (a, b) in zip(textPosition[i], [textSurface[i][0].get_rect().x, scoreBuffer])])


def reset(particles):
    sIdx = 1
    if multiTouch:
        sIdx = 2
    for p in range(len(particles) - sIdx):
        particles[p + sIdx].x = middlePoint[0]
        particles[p + sIdx].y = middlePoint[1]
        particles[p + sIdx].velocity = 0
        particles[p + sIdx].angle = 0


def checkGoal(particles, textSurface):
    cIdx = None
    sIdx = 1
    if multiTouch:
        sIdx = 2
    for p in range(len(particles) - sIdx):
        player = None
        if particles[p + sIdx].x <= particles[p + sIdx].radius:
            player = 1
            cIdx = p + sIdx
        elif particles[p + sIdx].x >= width - particles[p + sIdx].radius:
            player = 0
            cIdx = p + sIdx
        if player is not None:
            playerScore[player] += 1
            textSurface[player][cIdx] = font.render('Score: ' + str(playerScore[player]), False, WHITE)
            reset(particles)
        return textSurface
