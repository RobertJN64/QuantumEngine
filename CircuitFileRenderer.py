import matplotlib.pyplot as pyplot
import PygameTools
from PygameTools import config
from errors import InternalCommandException
from CircuitJSONTools import validgates
import warnings
import pygame
import json

#TODO - draw parameters

with open("resources/gategraphics.json") as f:
    gategraphics = json.load(f)

images = {}
def verifyGateGraphics():
    img = pygame.image.load("resources/" + "delete.png")
    img = pygame.transform.smoothscale(img, (config.imageSize, config.imageSize))
    images["delete"] = img
    for group in gategraphics:
        for key in ["group", "text-color", "background-color", "text-style"]:
            if key not in group:
                warnings.warn("Group: " + str(group["group"]) + " missing key: " + str(key))
                raise InternalCommandException
            if group["text-style"] not in ["lastchar", "swap", "image", "barrier", "raw"]:
                warnings.warn("Group: " + str(group["group"]) + " invalid text style: " + str(key))
                raise InternalCommandException
            if group["text-style"] == "image":
                if "image" not in group:
                    warnings.warn("Group: " + str(group["group"]) + " missing image.")
                    raise InternalCommandException
                img = pygame.image.load("resources/" + group["image"])
                img = pygame.transform.smoothscale(img, (config.imageSize,config.imageSize))
                images[group["image"]] = img
            if group["text-style"] in ["lastchar", "raw"]:
                if "text-size" not in group:
                    warnings.warn("Group: " + str(group["group"]) + " missing text size.")
                    raise InternalCommandException
            elif group["text-style"] == "raw":
                if "text" not in group:
                    warnings.warn("Group: " + str(group["group"]) + " missing text.")
                    raise InternalCommandException
    for gate in validgates:
        found = False
        for group in gategraphics:
            if gate in group["group"]:
                found = True
        if not found and gate not in ["empty", "multi"]:
            warnings.warn("No graphics found for: " + str(gate))
            raise InternalCommandException

    for group in gategraphics:
        for gate in group["group"]:
            if gate not in validgates:
                warnings.warn("Extra graphics found for: " + str(gate))
                raise InternalCommandException

verifyGateGraphics()

clickLocations = []
hand = ""

def render(qc, qcjson, flags):
    if '-h' in flags:
        pass
    elif '-t' in flags:
        print(qc.draw("text"))
    elif '-c' in flags:
        runDisplayLoop(qcjson)
    else:
        fig = pyplot.figure()
        plt = fig.add_subplot()
        qc.draw("mpl", ax=plt)
        pyplot.show()

def runDisplayLoop(circuitjson):
    screen = PygameTools.createPygameWindow()
    done = False
    clock = pygame.time.Clock()
    while not done:
        screen.fill(config.screenColor)
        drawCircuitToScreen(screen, circuitjson, "Custom Circuit Render")
        PygameTools.displayText(screen, "FPS: " + str(round(clock.get_fps())), config.screenW-100, 25, 15, (0,0,0))
        clock.tick(30)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
    pygame.display.quit()

def editor(circuitjson):
    global clickLocations
    global hand
    screen = PygameTools.createPygameWindow()
    done = False
    clock = pygame.time.Clock()
    while not done:
        screen.fill(config.screenColor)
        drawCircuitToScreen(screen, circuitjson, "Custom Circuit Render")
        drawGateToolbox(screen, [["h", "x", "y", "z", "u"], ["m", "swap", "barrier", "reset"]], ["control", "delete"])
        x, y = pygame.mouse.get_pos()
        if hand != "":
            drawGate(screen, hand, x, y)
            print(getGateDropPos(x, y, len(circuitjson["rows"]), 40))
        PygameTools.displayText(screen, "FPS: " + str(round(clock.get_fps())), config.screenW - 100, 25, 15, (0, 0, 0))
        pygame.display.update()
        clock.tick(30)
        # clock.tick() #for fps testing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: #left click:
                    for clickLoc in clickLocations:
                        if clickLoc.checkClick(x, y):
                            hand = clickLoc.target
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    hand = ""

    pygame.display.quit()

def drawCircuitToScreen(screen, circuitjson, title):
    PygameTools.displayText(screen, title, config.titlepos[0], config.titlepos[0],
                            config.titlesize, config.titleColor, "topleft")
    rows = circuitjson["rows"]
    for i in range(0, len(rows)):
        top = i * config.wireSpace + config.wireStartingY
        mid = i * config.wireSpace + config.wireStartingY + 0.5 * config.wireEndHeight
        bottom = i * config.wireSpace + config.wireStartingY + config.wireEndHeight
        left = config.leftWirePos
        right = config.screenW - config.rightWirePos

        pygame.draw.line(screen, (0, 0, 0), (left, top), (left, bottom), config.wireWidth)
        pygame.draw.line(screen, (0, 0, 0), (right, top), (right, bottom), config.wireWidth)
        pygame.draw.line(screen, (0, 0, 0), (left, mid), (right, mid), config.wireWidth)

    rowidtable = []
    for index, row in enumerate(rows):
        if "id" in row:
            rowidtable.append(row["id"])
        else:
            rowidtable.append(index)

    for rownum, row in enumerate(circuitjson["rows"]):
        for colnum, gatejson in enumerate(row["gates"]):
            gatex = colnum * config.gateSpacing + config.leftWirePos + 35
            gatey = rownum * config.wireSpace + config.wireStartingY + 0.5 * config.wireEndHeight

            gate = gatejson["type"]
            if "control" in gatejson:
                for rowid in gatejson["control"]:
                    if rowid in rowidtable:
                        rowid = rowidtable.index(rowid)
                    controly = rowid * config.wireSpace + config.wireStartingY + 0.5 * config.wireEndHeight
                    connectControl(screen, getGateColor(gate), gatex, gatey, controly)

            if gate not in ["empty", "multi"]:
                drawGate(screen, gate, gatex, gatey)

def drawGate(screen, name, x, y):
    gateconfig = {}
    for group in gategraphics:
        if name in group["group"]:
            gateconfig = group

    if gateconfig["text-style"] not in ["swap", "barrier"]:
        pygame.draw.rect(screen, gateconfig["background-color"],
                         (x-config.gateSize/2, y-config.gateSize/2, config.gateSize, config.gateSize))

    if gateconfig["text-style"] == "barrier":
        ypos = y - config.gateSize/2
        sections = 5
        distance = config.gateSize/sections
        for i in range(0, sections):
            pygame.draw.line(screen, (0,0,0), (x, ypos), (x, ypos + distance/2), 3)
            ypos += distance

    if gateconfig["text-style"] == "swap":
        #only for toolbox render
        l = config.swapToolLineLen
        leftx = x - config.gateSize/2
        rightx = x + config.gateSize/2
        topy = y - config.gateSize/2 + l
        bottomy = y + config.gateSize/2 - l
        pygame.draw.line(screen, (0, 0, 0), (leftx + l, topy), (rightx - l, bottomy), 3)
        pygame.draw.line(screen, (0, 0, 0), (rightx - l, topy), (leftx + l, bottomy), 3)

        pygame.draw.line(screen, (0, 0, 0), (leftx, topy), (leftx + l, topy), 3)
        pygame.draw.line(screen, (0, 0, 0), (leftx, bottomy), (leftx + l, bottomy), 3)
        pygame.draw.line(screen, (0, 0, 0), (rightx, topy), (rightx - l, topy), 3)
        pygame.draw.line(screen, (0, 0, 0), (rightx, bottomy), (rightx - l, bottomy), 3)

    elif gateconfig["text-style"] == "lastchar":
        text = name[-1].upper()
        PygameTools.displayText(screen, text, x, y, gateconfig["text-size"], gateconfig["text-color"])

    elif gateconfig["text-style"] == "raw":
        text = gateconfig["text"]
        PygameTools.displayText(screen, text, x, y, gateconfig["text-size"], gateconfig["text-color"])

    elif gateconfig["text-style"] == "image":
        screen.blit(images[gateconfig["image"]], (x - config.imageSize/2, y - config.imageSize/2))

def drawTool(screen, name, x, y):
    pygame.draw.rect(screen, config.toolBackgroundColor,
                     (x - config.gateSize / 2, y - config.gateSize / 2, config.gateSize, config.gateSize))

    if name == "control":
        pygame.draw.circle(screen, (0,0,0), (x,y), 10)
    elif name == "delete":
        screen.blit(images["delete"], (x - config.imageSize/2, y - config.imageSize/2))

def getGateColor(gate):
    gateconfig = {}
    for group in gategraphics:
        if gate in group["group"]:
            gateconfig = group
    return gateconfig["background-color"]

def connectControl(screen, color, x, y1, y2):
    pygame.draw.line(screen, color, (x, y1), (x, y2), config.controlWireThickness)
    pygame.draw.circle(screen, color, (x, y2), config.controlCircleRadius)

def drawGateToolbox(screen, allowedgates, allowedtools):
    global clickLocations
    clickLocations = []
    gatemargin = config.gateSpacing - config.gateSize

    totalgatecount = len(allowedtools)
    for minilist in allowedgates:
        totalgatecount += len(minilist)

    toolboxWidth = totalgatecount * config.gateSpacing + gatemargin * (len(allowedgates) + 1)
    toolboxHeight = config.gateSize + 2 * gatemargin
    leftx = config.screenW/2 - toolboxWidth/2
    topy = config.screenH - toolboxHeight - config.toolboxOffGround
    bottomy = config.screenH - config.toolboxOffGround
    midy = (topy + bottomy) / 2

    pygame.draw.rect(screen, config.toolboxColor, (leftx, topy, toolboxWidth, toolboxHeight), config.toolboxThickness)

    gatepos = leftx + config.gateSize/2
    for minilist in allowedgates:
        gatepos += gatemargin
        for gate in minilist:
            if gate not in validgates:
                warnings.warn("Gate: " + str(gate) + " not valid.")
                raise InternalCommandException
            drawGate(screen, gate, gatepos, midy)
            clickLocations.append(
                PygameTools.ClickLocation(gatepos-config.gateSize/2, midy-config.gateSize/2,
                                          config.gateSize, config.gateSize, gate))
            gatepos += config.gateSpacing
        pygame.draw.line(screen, config.toolboxColor, (gatepos-gatemargin,topy), (gatepos-gatemargin,bottomy),
                         config.toolboxThickness)

    gatepos += gatemargin
    for gate in allowedtools:
        drawTool(screen, gate, gatepos, midy)
        gatepos += config.gateSpacing

def getGateDropPos(x, y, rownum, mindistance):
    ypos = config.wireStartingY + config.wireEndHeight * 0.5
    row = None
    distance = 0
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

    #TODO - get x pos as well

    return row