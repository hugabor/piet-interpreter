
from PIL import Image
from Queue import *

# directions
UP = 0
RIGHT = 1
DOWN = 2
LEFT = 3
def rotateCW(dir):
    return (dir + 1) % 4
def left(dir):
    return (dir - 1) % 4
def right(dir):
    return rotateCW(dir)

# constants

# classes
class RuntimeStack:
    def __init__(self):
        self.__data = []
    def isEmpty(self):
        return len(self.__data) == 0
    def push(self, item):
        self.__data.append(item)
        return item
    def pop(self):
        if self.isEmpty():
            return None
        return self.__data.pop()



im = Image.open("fib.gif").convert("RGB")

width, height = im.size
pixels = im.load()

needle = (0, 0) # x,y position of the needle
DP = RIGHT
CC = LEFT

stack = RuntimeStack()

# returns a set of pixel coordinates that are the same color as the pixel at the
# needle and together form a contiguous block of same-colored pixels
def getColorBlock():

    colorBlock = set()
    potentials = Queue()

    def addPixelToBlock(pos):
        colorBlock.add(pos)
        x, y = pos
        newPotentials = [(x, y-1), (x+1, y), (x, y+1), (x-1, y)]
        for (px, py) in newPotentials:
            if 0 <= px < width and 0 <= py < height and (px, py) not in colorBlock:
                potentials.put((px, py))

    addPixelToBlock(needle)

    while not potentials.empty():
        potential = potentials.get()
        if pixels[potential[0], potential[1]] == pixels[needle[0], needle[1]]:
            addPixelToBlock(potential)

    return colorBlock



def stepNeedle():
