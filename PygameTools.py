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
            self.controlCircleRadius = configjson["control-circle-radius"]
            self.controlWireThickness = configjson["control-wire-thickness"]

        except KeyError:
            warnings.warn("Malformed pygame config.")
            warnings.warn(traceback.format_exc())
            raise InternalCommandException

config = PygameConfig(c)

def createPygameWindow():
    pygame.display.set_icon(pygame.image.load('resources/qc_icon.ico'))
    pygame.display.set_caption("QC Circuit Render")
    screen = pygame.display.set_mode((config.screenW, config.screenH))
    return screen

def displayText(screen, text, x, y, size, color, mode="center"):
    font = pygame.font.Font('freesansbold.ttf', size)
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