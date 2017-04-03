
import sys

from PIL import Image
from Queue import *

################################################################################
# constants

# colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

LIGHT_RED = (255, 192, 192)
RED       = (255, 0  , 0  )
DARK_RED  = (192, 0  , 0  )

LIGHT_YELLOW = (255, 255, 192)
YELLOW       = (255, 255, 0  )
DARK_YELLOW  = (192, 192, 0  )

LIGHT_GREEN = (192, 255, 192)
GREEN       = (0  , 255, 0  )
DARK_GREEN  = (0  , 192, 0  )

LIGHT_CYAN = (192, 255, 255)
CYAN       = (0  , 255, 255)
DARK_CYAN  = (0  , 192, 192)

LIGHT_BLUE = (192, 192, 255)
BLUE       = (0  , 0  , 255)
DARK_BLUE  = (0  , 0  , 192)

LIGHT_MAGENTA = (255, 192, 255)
MAGENTA       = (255, 0  , 255)
DARK_MAGENTA  = (192, 0  , 192)

colorRotationMatrix = [
    LIGHT_RED, RED, DARK_RED,
    LIGHT_YELLOW, YELLOW, DARK_YELLOW,
    LIGHT_GREEN, GREEN, DARK_GREEN,
    LIGHT_CYAN, CYAN, DARK_CYAN,
    LIGHT_BLUE, BLUE, DARK_BLUE,
    LIGHT_MAGENTA, MAGENTA, DARK_MAGENTA
]

# directions
UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3
def newDir(referenceDir, relativeDir):
    return (referenceDir + relativeDir) % 4


################################################################################
# classes

class RuntimeStack:
    def __init__(self):
        self.__data = []
    def getData(self):
        return self.__data
    def size(self):
        return len(self.__data)
    def isEmpty(self):
        return self.size() == 0
    def push(self, item):
        self.__data.append(int(item))
        return int(item)
    def pop(self):
        if self.isEmpty():
            return None
        return self.__data.pop()


################################################################################
# state variables

# image characteristics
codelSize = 1 # width and height of a codel in pixels
codels = [] # 2d array of rgb colors of codels represented as 3-tuples (0-255, 0-255, 0-255)
            # accessible by codels[x, y], where codels[0, 0] is the top left corner
width, height = 0, 0 # dimensions of the image in codels

# "lexing" state variables
needle = (0, 0) # x,y position of the needle
DP = RIGHT # direction pointer
CC = LEFT # codel chooser

# parser/interpreter state variables
lastColor = WHITE
lastSize = 0

stack = RuntimeStack()

################################################################################
# helper functions

def getColor():
    return codels[needle[0], needle[1]]

# returns set of ordered pairs for the color block the needle is in currently
def getColorBlock():

    colorBlock = set()
    potentials = Queue()

    def addCodeltoBlock(pos):
        colorBlock.add(pos)
        x, y = pos
        newPotentials = [(x, y-1), (x+1, y), (x, y+1), (x-1, y)]
        for (px, py) in newPotentials:
            if 0 <= px < width and 0 <= py < height and (px, py) not in colorBlock:
                potentials.put((px, py))

    addCodeltoBlock(needle)

    while not potentials.empty():
        potential = potentials.get()
        if codels[potential[0], potential[1]] == codels[needle[0], needle[1]]:
            addCodeltoBlock(potential)

    return colorBlock

# moves the needle one codel over in a specific direction (usually DP)
def stepNeedle(dir):
    global needle
    if dir == UP    : needle = ( needle[0]     , needle[1] - 1 )
    if dir == RIGHT : needle = ( needle[0] + 1 , needle[1]     )
    if dir == DOWN  : needle = ( needle[0]     , needle[1] + 1 )
    if dir == LEFT  : needle = ( needle[0] - 1 , needle[1]     )

# returns color of codel one over from the needle in the direction of DP
# if it attempts to peak past the edge of the image, BLACK is returned
def peakCodel():

    stepNeedle(DP) # temporarily
    peakNeedle = needle
    stepNeedle(newDir(DP, DOWN)) # step back

    if peakNeedle[0] < 0 or peakNeedle[0] >= width or peakNeedle[1] < 0 or peakNeedle[1] >= height:
        # needle out of bounds
        return BLACK

    return codels[peakNeedle[0], peakNeedle[1]]

# finds the subset of codels (from setOfCoords) that are furthest in the specified direction
def findFarthestInDir(setOfCoords, dir):
    subset = set()
    lastCoord = (-1, -1)

    for coord in setOfCoords:

        if len(subset) == 0:
            subset.add(coord)
            lastCoord = coord
            continue

        if dir == UP:
            if coord[1] < lastCoord[1]:
                subset = set()
            if coord[1] <= lastCoord[1]:
                subset.add(coord)
                lastCoord = coord
        if dir == RIGHT:
            if coord[0] > lastCoord[0]:
                subset = set()
            if coord[0] >= lastCoord[0]:
                subset.add(coord)
                lastCoord = coord
        if dir == DOWN:
            if coord[1] > lastCoord[1]:
                subset = set()
            if coord[1] >= lastCoord[1]:
                subset.add(coord)
                lastCoord = coord
        if dir == LEFT:
            if coord[0] < lastCoord[0]:
                subset = set()
            if coord[0] <= lastCoord[0]:
                subset.add(coord)
                lastCoord = coord

    return subset


# attempts to "slide" through the current white color block
# returns false if no exit is found
def moveToNextColorBlockFromWhite():
    global CC, DP

    visited = set()

    while needle not in visited:
        visited.add(needle)

        while peakCodel() == BLACK:
            CC = newDir(CC, DOWN) # toggles CC l/r
            DP = newDir(DP, RIGHT) # rotate DP clockwise

        stepNeedle(DP)

        if getColor() != WHITE:
            return True

    return False



################################################################################
# interpret

def interpretNewColorBlock(color, size):
    global lastColor, lastSize

    if color != lastColor and color != WHITE and lastColor != WHITE:
        commandID = (colorRotationMatrix.index(color) - colorRotationMatrix.index(lastColor)) % 18
        executeCommand(commandID, lastSize)

    lastColor = color
    lastSize = size

    # print stack.getData()

def executeCommand(id, val):
    global CC, DP

    # print "command: " + str(id)

    if id == 1: # push
        stack.push(val)
    if id == 2: # pop
        stack.pop()
    if id == 3: # add
        if stack.size() >= 2:
            stack.push(stack.pop() + stack.pop())
    if id == 4: # subtract
        if stack.size() >= 2:
            stack.push(- stack.pop() + stack.pop())
    if id == 5: # multiply
        if stack.size() >= 2:
            stack.push(stack.pop() * stack.pop())
    if id == 6: # divide
        if stack.size() >= 2:
            top = stack.pop()
            second = stack.pop()
            if top != 0:
                stack.push(second / top)
            else:
                stack.push(second)
                stack.push(top)
    if id == 7: # mod
        if stack.size() >= 2:
            top = stack.pop()
            second = stack.pop()
            if top != 0:
                stack.push(second % top)
            else:
                stack.push(second)
                stack.push(top)
    if id == 8: # not
        if stack.size() >= 1:
            if stack.pop() == 0:
                stack.push(1)
            else:
                stack.push(0)
    if id == 9: # greater
        if stack.size() >= 2:
            if stack.pop() < stack.pop():
                stack.push(1)
            else:
                stack.push(0)
    if id == 10: # pointer
        if stack.size() >= 1:
            DP = (DP + stack.pop()) % 4
    if id == 11: # switch
        if stack.size() >= 1:
            if stack.pop() % 2 == 1:
                CC = newDir(CC, DOWN) # toggle CC
    if id == 12: # duplicate
        if stack.size() >= 1:
            stack.push(stack.push(stack.pop()))
    if id == 13: # roll
        if stack.size() >= 2:
            rolls = stack.pop()
            depth = stack.pop()
            rolls = rolls % depth
            poppedToBury = []
            poppedToBringUp = []
            if depth >= 2 and stack.size() >= depth:
                for _ in range(rolls):
                    poppedToBury.append(stack.pop())
                for _ in range(depth - rolls):
                    poppedToBringUp.append(stack.pop())
                for elem in poppedToBury:
                    stack.push(elem)
                for elem in poppedToBringUp:
                    stack.push(elem)
            else:
                stack.push(depth)
                stack.push(rolls)
    if id == 14: # in(number)
        stack.push(100)
    if id == 15: # in(char)
        stack.push(66)
    if id == 16: # out(number)
        print(stack.pop())
    if id == 17: # out(char)
        print(chr(stack.pop()))

    #print ("command:", id, val)
    #print (stack.getData())

################################################################################
################################################################################
# start execution here

################################################################################
# load

# load file and set up environment
if len(sys.argv) < 2:
    print "You need to supply a path to an image file"
    exit()
path = sys.argv[1]
if len(sys.argv) >= 3:
    pass
    # codelSize = int(sys.argv[2])
    # no support yet for codels larger than one pixel
img = Image.open(path).convert("RGB")
width = img.size[0]
height = img.size[1]
codels = img.load()


################################################################################
# parse


# initial "reset"
colorBlock = getColorBlock()
exitAttempts = 0

while exitAttempts < 8:
    exitAttempts += 1

    oldNeedle = needle

    farthestEdge = findFarthestInDir(colorBlock, DP)
    farthestCodel = list(findFarthestInDir(farthestEdge, newDir(DP, CC)))[0]

    needle = farthestCodel

    # print ("attempt:", needle, getColor(), peakCodel())

    if peakCodel() == BLACK:
        # hit restriction (either black codel or edge of image)

        if exitAttempts % 2 == 1:
            DP = newDir(DP, RIGHT) # rotate DP clockwise
        else:
            CC = newDir(CC, DOWN) # toggle CC l/r

        needle = oldNeedle # try again

    else:
        # no restriction
        # found exit

        stepNeedle(DP) # move into new color block
        # next color block
        colorBlock = getColorBlock()
        exitAttempts = 0

        # print (CC, needle)

        if getColor() is WHITE:

            interpretNewColorBlock(WHITE, 0)

            if not moveToNextColorBlockFromWhite():
                break # couldn't exit white color block, stop reading the image

        interpretNewColorBlock(getColor(), len(colorBlock))












################################################################################
