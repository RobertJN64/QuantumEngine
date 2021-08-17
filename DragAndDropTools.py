from PygameTools import config
import pygame
import warnings
from errors import InternalCommandException

def drawDropBox(screen, row, col, t):
    gatex = col * config.gateSpacing + config.leftWirePos + config.gateSpacing / 2 + 10
    gatey = row * config.wireSpace + config.wireStartingY + 0.5 * config.wireEndHeight
    if t == "box":
        pygame.draw.rect(screen, config.gateDropColor,
                         (gatex - config.gateSize / 2, gatey - config.gateSize / 2, config.gateSize,
                          config.gateSize), width=2)
    elif t == "line":
        pygame.draw.line(screen, config.gateDropColor,
                         (gatex - config.gateSpacing / 2 ,gatey + 0.5 * config.gateSize),
                         (gatex - config.gateSpacing / 2, gatey - 0.5 * config.gateSize), 3)
    else:
        warnings.warn("Unexpected drop box type.")
        raise InternalCommandException

def getGateDropPos(x, y, circuitjson, mindistance):
    ypos = config.wireStartingY + config.wireEndHeight * 0.5
    row = None
    distance = 0
    rownum = len(circuitjson["rows"])
    for i in range(0, rownum):
        dis = abs(y - ypos)
        if dis < mindistance:
            if row is None:
                row = i
                distance = dis
            else:
                if dis < distance:
                    row = i
        ypos += config.wireSpace

    col = None
    distance = 0
    if row is not None:
        xpos = config.leftWirePos
        for i in range(0, len(circuitjson["rows"][row]["gates"])):
            dis = abs(x - xpos)
            if dis < mindistance:
                if col is None:
                    col = i
                    distance = dis
                else:
                    if dis < distance:
                        col = i
            xpos += config.gateSpacing

        if x > xpos - config.gateSize and col is None:
            col = "end"

    return row, col

def getDeletePos(x, y, circuitjson, mindistance):
    ypos = config.wireStartingY + config.wireEndHeight * 0.5
    row = None
    distance = 0
    rownum = len(circuitjson["rows"])
    for i in range(0, rownum):
        dis = abs(y - ypos)
        if dis < mindistance:
            if row is None:
                row = i
                distance = dis
            else:
                if dis < distance:
                    row = i
        ypos += config.wireSpace

    col = None
    distance = 0
    if row is not None:
        xpos = config.leftWirePos + config.gateSpacing/2 + 10
        for i in range(0, len(circuitjson["rows"][row]["gates"])):
            dis = abs(x - xpos)
            if dis < mindistance:
                if col is None:
                    col = i
                    distance = dis
                else:
                    if dis < distance:
                        col = i
            xpos += config.gateSpacing

    if row is not None and col is not None:
        if circuitjson["rows"][row]["gates"][col]["type"] == "empty":
            row = None
            col = None

    return row, col