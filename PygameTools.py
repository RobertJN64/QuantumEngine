import pygame
import json
from errors import InternalCommandException
import warnings
import traceback

pygame.init()

with open("resources/pygameconfig.json") as f:
    c = json.load(f)

class PygameConfig:
    def __init__(self, configjson):
        try:
            self.screenColor = tuple(configjson["screen-color"])
            self.titleColor = tuple(configjson["title-color"])
            self.titlesize = configjson["title-size"]
            self.titlepos = tuple(configjson["title-pos"])
            self.screenW = configjson["screen-size"][0]
            self.screenH = configjson["screen-size"][1]

            self.leftWirePos = configjson["left-wire-pos"]
            self.rightWirePos = configjson["right-wire-pos"]
            self.wireWidth = configjson["wire-width"]
            self.wireSpace = configjson["wire-space"]
            self.wireEndHeight = configjson["wire-end-height"]
            self.wireStartingY = configjson["wire-starting-y"]

            self.gateSpacing = configjson["gate-spacing"]
            self.gateSize = configjson["gate-size"]
            self.imageSize = configjson["image-size"]
            self.smallImageSize = configjson["small-image-size"]
            self.controlCircleRadius = configjson["control-circle-radius"]
            self.controlWireThickness = configjson["control-wire-thickness"]

            self.toolboxThickness = configjson["toolbox-thickness"]
            self.toolboxSpacerThickness = configjson["toolbox-spacer-thickness"]
            self.toolboxColor = configjson["toolbox-color"]
            self.toolboxOffGround = configjson["toolbox-offground"]

            self.toolBackgroundColor = configjson["tool-background"]
            self.swapToolLineLen = configjson["swap-tool-line-len"]

            self.gateDropColor = configjson["gate-drop-color"]

            self.blochSphereHeight = configjson["bloch-sphere-height"]

            self.statevectorAllKeys = configjson["statevector-allkeys"]

        except KeyError:
            warnings.warn("Malformed pygame config.")
            warnings.warn(traceback.format_exc())
            raise InternalCommandException

config = PygameConfig(c)

class ClickMode:
    Empty = 0,
    AddGate = 1,
    MoveGate = 2,
    AddControl = 3,
    DeleteGate = 4,
    AddRow = 5,
    DeleteRow = 6,
    EditParams = 7,
    Command = 8, #for custom commands like save, etc.
    ControlDot = 9

class UIMode:
    Main = 0,
    ParamBoxOpen = 1,
    ControlWireConfig = 2,
    BlochSphereTargetBoxOpen = 3,
    CompareStatevectorTargetBoxOpen = 4,
    InfoBoxOpen = 5

class ClickLocation:
    def __init__(self, x, y, w, h, target, mode):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.target = target
        self.mode = mode

    def checkClick(self, x, y):
        return self.x < x < self.x + self.h and self.y < y < self.y + self.h


def createPygameWindow():
    pygame.display.set_icon(pygame.image.load('resources/images/qc_icon.ico'))
    pygame.display.set_caption("QC Circuit Render")
    screen = pygame.display.set_mode((config.screenW, config.screenH), pygame.RESIZABLE)
    return screen

def displayText(screen, text, x, y, size, color, mode="center", font=None):
    if font is None:
        font = pygame.font.Font('freesansbold.ttf', size)
    elif font == "monospaced":
        font = pygame.font.SysFont("monospace", size)
    else:
        warnings.warn("Font: " + str(font) + " not found.")
        raise InternalCommandException

    textSurface = font.render(text, True, color)
    textRect = textSurface.get_rect()
    if mode == "center":
        textRect.center = (x, y)
    elif mode == "topleft":
        textRect.topleft = (x, y)
    else:
        warnings.warn("Invalid text display mode!")
        raise InternalCommandException
    screen.blit(textSurface, textRect)