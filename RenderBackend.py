import pygame
from errors import InternalCommandException
import warnings
import json
from PygameTools import config, ClickMode, ClickLocation
import PygameTools
from CircuitJSONTools import validgates

class WarningMessage:
    def __init__(self):
        self.message = ""
        self.timer = 0

    def tick(self):
        if self.timer >= 0:
            self.timer -= 1

    def warn(self, message, timer):
        self.message = message
        self.timer = timer

    def display(self):
        if self.timer > 0:
            return self.message
        else:
            return ""

warningMessage = WarningMessage()

clickLocations = []

with open("resources/gategraphics.json") as f:
    gategraphics = json.load(f)

images = {}
def verifyGateGraphics():
    for image, size in [["delete.png", config.imageSize], ["plus.png", config.smallImageSize],
                        ["minus.png", config.smallImageSize], ["redplus.png", config.smallImageSize],
                        ["redminus.png", config.smallImageSize], ["save.png", config.smallImageSize],
                        ["view.png", config.smallImageSize], ["play.png", config.smallImageSize]]:
        img = pygame.image.load("resources/images/" + image)
        img = pygame.transform.smoothscale(img, (round(size), round(size)))
        images[image] = img

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
                img = pygame.image.load("resources/images/" + group["image"])
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


def drawCircuitToScreen(screen, circuitjson, title, minrows = 1, maxrows = 50):
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

    if maxrows != minrows:
        y = len(rows) * config.wireSpace + config.wireStartingY + 0.5 * config.wireEndHeight - config.smallImageSize/2
        leftx = config.leftWirePos - config.smallImageSize/2 - 3
        rightx = config.leftWirePos + config.smallImageSize/2 + 3


        if len(rows) < maxrows:
            drawPlusMinus(screen, "plus.png", leftx, y, "add", ClickMode.AddRow)

        else:
            drawPlusMinus(screen, "redplus.png", leftx, y, "Max row limit reached.", ClickMode.AddRow)

        if len(rows) > minrows:
            allempty = True
            for gate in circuitjson["rows"][-1]["gates"]:
                if gate["type"] != "empty":
                    allempty = False

            if allempty:
                drawPlusMinus(screen, "minus.png", rightx, y, "del", ClickMode.DeleteRow)
            else:
                drawPlusMinus(screen, "redminus.png", rightx, y, "Row is not empty", ClickMode.DeleteRow)

        else:
            drawPlusMinus(screen, "redminus.png", rightx, y, "Min row limit reached.", ClickMode.AddRow)


    for rownum, row in enumerate(circuitjson["rows"]):
        for colnum, gatejson in enumerate(row["gates"]):
            gatex = colnum * config.gateSpacing + config.leftWirePos + config.gateSpacing / 2 + 10
            gatey = rownum * config.wireSpace + config.wireStartingY + 0.5 * config.wireEndHeight

            gate = gatejson["type"]
            if "control" in gatejson:
                for rowid in gatejson["control"]:
                    controly = rowid * config.wireSpace + config.wireStartingY + 0.5 * config.wireEndHeight
                    connectControl(screen, getGateColor(gate), gatex, gatey, controly)

            if gate not in ["empty", "multi"]:
                drawGate(screen, gatejson, gatex, gatey)
                clickLocations.append(ClickLocation(gatex-config.gateSize/2, gatey-config.gateSize/2, config.gateSize,
                                                    config.gateSize, gatejson, ClickMode.MoveGate))

def drawPlusMinus(screen, filename, x, y, target, mode):
    screen.blit(images[filename], (x, y))
    clickLocations.append(ClickLocation(x, y, config.smallImageSize, config.smallImageSize, target, mode))


def drawGate(screen, gate: dict, x, y):
    gateconfig = {}
    name = gate["type"]
    params = gate.get("params", [])
    ps = []
    for item in params:
        ps.append(round(item))
    pstring = str(ps).replace("[", "").replace("]", "")
    if len(pstring) > 8:
        pstring = pstring[0:6] + "..."

    for group in gategraphics:
        if name in group["group"]:
            gateconfig = group

    if gateconfig == {}:
        warnings.warn("No gategraphics found for gate: " + str(name))
        raise InternalCommandException

    if gateconfig["text-style"] not in ["swap", "barrier"]:
        pygame.draw.rect(screen, gateconfig["background-color"],
                         (x - config.gateSize / 2, y - config.gateSize / 2, config.gateSize, config.gateSize))

    if gateconfig["text-style"] == "barrier":
        ypos = y - config.gateSize / 2
        sections = 5
        distance = config.gateSize / sections
        for i in range(0, sections):
            pygame.draw.line(screen, (0, 0, 0), (x, ypos), (x, ypos + distance / 2), 3)
            ypos += distance

    if gateconfig["text-style"] == "swap":
        # only for toolbox render
        l = config.swapToolLineLen
        leftx = x - config.gateSize / 2
        rightx = x + config.gateSize / 2
        topy = y - config.gateSize / 2 + l
        bottomy = y + config.gateSize / 2 - l
        pygame.draw.line(screen, (0, 0, 0), (leftx + l, topy), (rightx - l, bottomy), 3)
        pygame.draw.line(screen, (0, 0, 0), (rightx - l, topy), (leftx + l, bottomy), 3)

        pygame.draw.line(screen, (0, 0, 0), (leftx, topy), (leftx + l, topy), 3)
        pygame.draw.line(screen, (0, 0, 0), (leftx, bottomy), (leftx + l, bottomy), 3)
        pygame.draw.line(screen, (0, 0, 0), (rightx, topy), (rightx - l, topy), 3)
        pygame.draw.line(screen, (0, 0, 0), (rightx, bottomy), (rightx - l, bottomy), 3)


    elif gateconfig["text-style"] == "lastchar":
        text = name[-1].upper()
        if len(params) > 0:
            y -= 5
            PygameTools.displayText(screen, pstring, x, y + gateconfig["text-size"], round(gateconfig["text-size"] / 1.5),
                                    gateconfig["text-color"])
        PygameTools.displayText(screen, text, x, y, gateconfig["text-size"], gateconfig["text-color"])


    elif gateconfig["text-style"] == "raw":
        text = gateconfig["text"]
        if len(params) > 0:
            y -= 5
            PygameTools.displayText(screen, pstring, x, y + gateconfig["text-size"], round(gateconfig["text-size"] / 1.5),
                                    gateconfig["text-color"])
        PygameTools.displayText(screen, text, x, y, gateconfig["text-size"], gateconfig["text-color"])


    elif gateconfig["text-style"] == "image":
        screen.blit(images[gateconfig["image"]], (x - config.imageSize / 2, y - config.imageSize / 2))

def drawTool(screen, name, x, y):
    pygame.draw.rect(screen, config.toolBackgroundColor,
                     (x - config.gateSize / 2, y - config.gateSize / 2, config.gateSize, config.gateSize))

    if name == "control":
        pygame.draw.circle(screen, (0, 0, 0), (x, y), 10)
    elif name == "delete":
        screen.blit(images["delete.png"], (x - config.imageSize / 2, y - config.imageSize / 2))

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
    gatemargin = config.gateSpacing - config.gateSize

    totalgatecount = len(allowedtools)
    for minilist in allowedgates:
        totalgatecount += len(minilist)

    toolboxWidth = totalgatecount * config.gateSpacing + gatemargin * (len(allowedgates) + 1)
    toolboxHeight = config.gateSize + 2 * gatemargin
    leftx = config.screenW / 2 - toolboxWidth / 2
    topy = config.screenH - toolboxHeight - config.toolboxOffGround
    bottomy = config.screenH - config.toolboxOffGround
    midy = (topy + bottomy) / 2

    pygame.draw.rect(screen, config.toolboxColor, (leftx, topy, toolboxWidth, toolboxHeight),
                     config.toolboxThickness)

    gatepos = leftx + config.gateSize / 2
    for minilist in allowedgates:
        gatepos += gatemargin
        for gate in minilist:
            if gate not in validgates:
                warnings.warn("Gate: " + str(gate) + " not valid.")
                raise InternalCommandException
            drawGate(screen, {"type": gate}, gatepos, midy)
            clickLocations.append(ClickLocation(gatepos - config.gateSize / 2, midy - config.gateSize / 2,
                                                config.gateSize, config.gateSize, {"type": gate}, ClickMode.AddGate))
            gatepos += config.gateSpacing
        pygame.draw.line(screen, config.toolboxColor, (gatepos - gatemargin, topy), (gatepos - gatemargin, bottomy),
                         config.toolboxThickness)

    gatepos += gatemargin
    for gate in allowedtools:
        drawTool(screen, gate, gatepos, midy)
        if gate == "delete":
            clickLocations.append(ClickLocation(gatepos - config.gateSize / 2, midy - config.gateSize / 2,
                                                config.gateSize, config.gateSize, gate, ClickMode.DeleteGate))
        gatepos += config.gateSpacing
