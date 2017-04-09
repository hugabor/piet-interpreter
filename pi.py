
from __future__ import print_function
import sys
from PIL import Image

################################################################################

logCmds = False

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

    checked = [needle]
    colorBlock = set([])
    potentials = []

    def addCodeltoBlock(pos):
        colorBlock.add(pos)
        x, y = pos
        newPotentials = [(x, y-1), (x+1, y), (x, y+1), (x-1, y)]
        for (px, py) in newPotentials:
            if (0 <= px < width) and (0 <= py < height) and ((px, py) not in checked):
                potentials.append((px, py))
            checked.append((px, py))

    addCodeltoBlock(needle)

    while len(potentials) > 0:
        potential = potentials.pop(0)
        if codels[potential[0], potential[1]] == codels[needle[0], needle[1]]:
            addCodeltoBlock(potential)
        # checked.append(potential)

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
    global needle

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

    while (needle, DP) not in visited:
        visited.add((needle, DP))

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

        lastIndex = colorRotationMatrix.index(lastColor)
        newIndex  = colorRotationMatrix.index(color)

        hueDiff   = ((newIndex / 3) - (lastIndex / 3)) % 6
        shadeDiff = ((newIndex % 3) - (lastIndex % 3)) % 3

        commandID = hueDiff * 3 + shadeDiff

        executeCommand(commandID, lastSize)

    lastColor = color
    lastSize = size

def executeCommand(id, val):
    global CC, DP

    if id == 1: # push
        if logCmds: print("PUSH", val)
        stack.push(val)
    if id == 2: # pop
        if logCmds: print("POP")
        stack.pop()
    if id == 3: # add
        if logCmds: print("ADD")
        if stack.size() >= 2:
            stack.push(stack.pop() + stack.pop())
    if id == 4: # subtract
        if logCmds: print("SUBTRACT")
        if stack.size() >= 2:
            stack.push(- stack.pop() + stack.pop())
    if id == 5: # multiply
        if logCmds: print("MUL")
        if stack.size() >= 2:
            stack.push(stack.pop() * stack.pop())
    if id == 6: # divide
        if logCmds: print("DIV")
        if stack.size() >= 2:
            top = stack.pop()
            second = stack.pop()
            if top != 0:
                stack.push(second / top)
            else:
                stack.push(second)
                stack.push(top)
    if id == 7: # mod
        if logCmds: print("MOD")
        if stack.size() >= 2:
            top = stack.pop()
            second = stack.pop()
            if top != 0:
                stack.push(second % top)
            else:
                stack.push(second)
                stack.push(top)
    if id == 8: # not
        if logCmds: print("NOT")
        if stack.size() >= 1:
            if stack.pop() == 0:
                stack.push(1)
            else:
                stack.push(0)
    if id == 9: # greater
        if logCmds: print("GT")
        if stack.size() >= 2:
            if stack.pop() < stack.pop():
                stack.push(1)
            else:
                stack.push(0)
    if id == 10: # pointer
        if logCmds: print("POINTER")
        if stack.size() >= 1:
            DP = (DP + stack.pop()) % 4
    if id == 11: # switch
        if logCmds: print("SWITCH")
        if stack.size() >= 1:
            if stack.pop() % 2 == 1:
                CC = newDir(CC, DOWN) # toggle CC
    if id == 12: # duplicate
        if logCmds: print("DUPE")
        if stack.size() >= 1:
            stack.push(stack.push(stack.pop()))
    if id == 13: # roll
        if logCmds: print("ROLL")
        if stack.size() >= 2:
            rolls = stack.pop()
            depth = stack.pop()
            rolls = rolls % depth if depth > 0 else 0
            poppedToBury = []
            poppedToBringUp = []
            if depth >= 0 and stack.size() >= depth:
                for _ in range(rolls % depth):
                    poppedToBury.append(stack.pop())
                for _ in range(depth - (rolls % depth)):
                    poppedToBringUp.append(stack.pop())
                for elem in poppedToBury[::-1]:
                    stack.push(elem)
                for elem in poppedToBringUp[::-1]:
                    stack.push(elem)
            else:
                stack.push(depth)
                stack.push(rolls)
    if id == 14: # in(number)
        if logCmds: print("IN(num)")
        while True:
            inputStr = str(raw_input("#:"))
            try:
                stack.push(int(inputStr))
                break
            except:
                continue
    if id == 15: # in(char)
        if logCmds: print("IN(char)")
        while True:
            inputStr = str(raw_input("\":"))
            if len(inputStr) > 0:
                stack.push(ord(inputStr[0]) - 48)
                break
    if id == 16: # out(number)
        if logCmds: print("OUT(num)")
        print(stack.pop(), end="")
    if id == 17: # out(char)
        if logCmds: print("OUT(char)")
        print(chr(stack.pop()), end="")

    # print(stack.getData())


################################################################################
################################################################################
# start execution here

################################################################################
# load

# load file and set up environment
if len(sys.argv) < 2:
    print("You need to supply a path to an image file")
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

# start
interpretNewColorBlock(getColor(), len(colorBlock))

while exitAttempts < 8:
    exitAttempts += 1

    oldNeedle = needle

    farthestEdge = findFarthestInDir(colorBlock, DP)
    farthestCodel = list(findFarthestInDir(farthestEdge, newDir(DP, CC)))[0]

    needle = farthestCodel

    if peakCodel() == BLACK:
        # hit restriction (either black codel or edge of image)

        if exitAttempts % 2 == 1:
            CC = newDir(CC, DOWN) # toggle CC l/r
        else:
            DP = newDir(DP, RIGHT) # rotate DP clockwise

        needle = oldNeedle # try again

    else:
        # no restriction
        # found exit
        exitAttempts = 0

        stepNeedle(DP) # move into new color block


        if getColor() == WHITE:
            # if needle is on a white codel

            # let the interpreter know about the white color
            interpretNewColorBlock(WHITE, 0)

            # try to leave the white
            if not moveToNextColorBlockFromWhite():
                break # couldn't exit white color block, stop reading the image

        # print(needle, DP)

        # next color block
        colorBlock = getColorBlock()

        interpretNewColorBlock(getColor(), len(colorBlock))

print("")










################################################################################
