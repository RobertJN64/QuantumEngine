import matplotlib.pyplot as pyplot
import PygameTools
from PygameTools import config
from errors import InternalCommandException
from CircuitJSONTools import validgates
import warnings
import pygame
import json

with open("resources/gategraphics.json") as f:
    gategraphics = json.load(f)

def verifyGateGraphics():
    for group in gategraphics:
        for key in ["group", "text-color", "background-color", "text-style"]:
            if key not in group:
                warnings.warn("Group: " + str(group["group"]) + " missing key: " + str(key))
                raise InternalCommandException
            if group["text-style"] not in ["lastchar", "swap", "image"]:
                warnings.warn("Group: " + str(group["group"]) + " invalid text style: " + str(key))
                raise InternalCommandException
            if group["text-style"] == "image":
                if "image" not in group:
                    warnings.warn("Group: " + str(group["group"]) + " missing image: " + str(key))
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

def render(qc, qcjson, flags):
    if '-h' in flags:
        pass
    elif '-t' in flags:
        print(qc.draw("text"))
    elif '-c' in flags:
        screen = PygameTools.createPygameWindow()
        done = False
        while not done:
            screen.fill(config.screenColor)
            drawCircuitToScreen(screen, qcjson, "Custom Circuit Render")
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True
        pygame.display.quit()
    else:
        fig = pyplot.figure()
        plt = fig.add_subplot()
        qc.draw("mpl", ax=plt)
        pyplot.show()

def drawCircuitToScreen(screen, circuitjson, title):
    PygameTools.displayText(screen, title, config.titlepos[0], config.titlepos[0],
                            config.titlesize, config.titleColor, "topleft")
    rows = circuitjson["rows"]
    for i in range(0, len(rows)):
        pygame.draw.line(screen, (0, 0, 0), (50, i * 100 + 100), (50, i * 100 + 150), 3)
        pygame.draw.line(screen, (0, 0, 0), (config.screenW-50, i * 100 + 100), (config.screenW-50, i * 100 + 150), 3)
        pygame.draw.line(screen, (0, 0, 0), (50, i * 100 + 125), (config.screenW - 50, i * 100 + 125), 3)

    rowidtable = []
    for index, row in enumerate(rows):
        if "id" in row:
            rowidtable.append(row["id"])
        else:
            rowidtable.append(index)

    for rownum, row in enumerate(circuitjson["rows"]):
        for colnum, gatejson in enumerate(row["gates"]):
            gate = gatejson["type"]
            if "control" in gatejson:
                for rowid in gatejson["control"]:
                    if rowid in rowidtable:
                        pass

            if gate not in ["empty", "multi"]:
                drawGate(screen, gate, colnum * 70 + 85, rownum * 100 + 125)

def drawGate(screen, name, x, y):
    gateconfig = {}
    for group in gategraphics:
        if name in group["group"]:
            gateconfig = group

    text = ""
    if gateconfig["text-style"] != "swap":
        pygame.draw.rect(screen, gateconfig["background-color"], (x-25, y-25, 50, 50))

    if gateconfig["text-style"] == "lastchar":
        text = name[-1].upper()

    PygameTools.displayText(screen, text, x, y, 20, gateconfig["text-color"])

    if gateconfig["text-style"] == "image":
        img = pygame.image.load("resources/" + gateconfig["image"])
        img = pygame.transform.smoothscale(img, (44,44))
        screen.blit(img, (x-22,y-22))

    #todo - images
