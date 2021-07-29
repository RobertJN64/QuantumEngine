import matplotlib.pyplot as pyplot
import RenderBackend as Render
from RenderBackend import images, clickLocations, warningMessage
import PygameTools
from PygameTools import config, ClickMode, ClickLocation
from errors import InternalCommandException
from CircuitJSONTools import refactorJSON, addGate, deleteGate, updateGate, assembleCircuit
from PygameTextInput import TextInput
import warnings
import pygame

#TODO - swap gate graphics
#TODO - scrolling

editorfig = None

def cleanclose(event):
    global editorfig
    if event.name == "":
        pass
    editorfig = None
    pyplot.ioff()

def render(qc, qcjson, flags, fig=None):
    if '-h' in flags:
        pass
    elif '-t' in flags:
        print(qc.draw("text"))
    elif '-c' in flags:
        runDisplayLoop(qcjson)
    else:
        if fig is None:
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
        Render.drawCircuitToScreen(screen, circuitjson, "Custom Circuit Render")
        PygameTools.displayText(screen, "FPS: " + str(round(clock.get_fps())), config.screenW-100, 25, 15, (0,0,0))
        clock.tick(30)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
    pygame.display.quit()

def editor(circuitjson):
    global editorfig
    refactorJSON(circuitjson)
    hand = ""
    handmode = ClickMode.Empty
    paramboxopen = False
    parambox = TextInput()
    screen = PygameTools.createPygameWindow()
    done = False
    save = False
    clock = pygame.time.Clock()
    while not done:
        clickLocations.clear()
        screen.fill(config.screenColor)
        Render.drawCircuitToScreen(screen, circuitjson, "Custom Circuit Render")
        Render.drawGateToolbox(screen, [["h", "x", "y", "z", "u"], ["m", "swap", "barrier", "reset"]], ["control", "delete"])
        PygameTools.displayText(screen, warningMessage.display(), config.screenW/2,
                                config.screenH - config.toolboxOffGround - config.gateSpacing * 1.5, 20, (200,0,0))

        PygameTools.displayText(screen, "FPS: " + str(round(clock.get_fps())), config.screenW - 100, 25, 15, (0, 0, 0))
        screen.blit(images["save.png"], (config.screenW - config.smallImageSize - 10, 5))
        clickLocations.append(ClickLocation(config.screenW - config.smallImageSize - 10, 5, config.smallImageSize,
                                            config.smallImageSize, target="save", mode=ClickMode.Command))
        screen.blit(images["view.png"], (config.screenW - config.smallImageSize - 10, config.smallImageSize + 15))
        clickLocations.append(ClickLocation(config.screenW - config.smallImageSize - 10, config.smallImageSize + 15, config.smallImageSize,
                                            config.smallImageSize, target="view", mode=ClickMode.Command))

        #region drag and drop
        x, y = pygame.mouse.get_pos()
        if hand != "":
            if handmode == ClickMode.AddGate or handmode == ClickMode.MoveGate:
                Render.drawGate(screen, hand, x, y)
                row, col = getGateDropPos(x, y, circuitjson, config.gateSize)
                if (row is not None) and (col is not None):
                    if col == "end":
                        depth = len(circuitjson["rows"][row]["gates"])
                        drawDropBox(screen, row, depth, "box")

                    elif circuitjson["rows"][row]["gates"][col]["type"] == "empty":
                        drawDropBox(screen, row, col, "box")

                    else:
                        if col > 0 and circuitjson["rows"][row]["gates"][col-1]["type"] == "empty":
                            drawDropBox(screen, row, col-1, "box")
                        else:
                            drawDropBox(screen, row, col, "line")

            elif handmode == ClickMode.DeleteGate:
                screen.blit(images["delete.png"], (x - config.imageSize/2, y - config.imageSize/2))
                row, col = getDeletePos(x, y, circuitjson, config.gateSize)
                if row is not None and col is not None and col != "end":
                    drawDropBox(screen, row, col, "box")
        #endregion

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not paramboxopen: #left click:
                    for clickLoc in clickLocations:
                        if clickLoc.checkClick(x, y):
                            handmode = clickLoc.mode
                            if clickLoc.mode == ClickMode.AddGate:
                                hand = clickLoc.target
                            elif clickLoc.mode == ClickMode.DeleteGate:
                                hand = "delete"
                            elif clickLoc.mode == ClickMode.MoveGate:
                                row, col = getDeletePos(x, y, circuitjson, config.gateSize)
                                hand = clickLoc.target
                                deleteGate(circuitjson, row, col)
                                circuitjson = refactorJSON(circuitjson)
                            elif clickLoc.mode == ClickMode.AddRow:
                                if clickLoc.target == "add":
                                    length = len(circuitjson["rows"][0]["gates"])
                                    newrow = []
                                    for i in range(0, length):
                                        newrow.append({"type": "empty"})
                                    circuitjson["rows"].append({"gates": newrow})
                                    circuitjson = refactorJSON(circuitjson)
                                else:
                                    warningMessage.warn(clickLoc.target, 100)
                            elif clickLoc.mode == ClickMode.DeleteRow:
                                if clickLoc.target == "del":
                                    circuitjson["rows"].pop()
                                    circuitjson = refactorJSON(circuitjson)
                                else:
                                    warningMessage.warn(clickLoc.target, 100)
                            elif clickLoc.mode == ClickMode.Command:
                                if clickLoc.target == "save":
                                    circuitjson = refactorJSON(circuitjson)
                                    done = True
                                    save = True
                                elif clickLoc.target == "view":
                                    circuitjson = refactorJSON(circuitjson)
                                    if editorfig is None:
                                        editorfig = pyplot.figure()
                                    pyplot.ion()
                                    render(assembleCircuit(circuitjson), circuitjson, [], editorfig)
                                    editorfig.canvas.mpl_connect('close_event', cleanclose)

                if event.button == 3 and not paramboxopen:
                    for clickLoc in clickLocations:
                        if clickLoc.checkClick(x, y):
                            if clickLoc.mode == ClickMode.MoveGate:
                                if clickLoc.target["type"][-1] in ["x", "y", "z", "u"]:
                                    handmode = ClickMode.EditParams
                                    hand = clickLoc.target
                                    paramboxopen = True
                                    params = hand.get("params", [])
                                    p = []
                                    for param in params:
                                        p.append(str(round(param)))
                                    if len(p) == 0:
                                        p = ["180"]
                                    parambox.input_string = ", ".join(p)
                                    parambox.cursor_position = len(parambox.input_string)

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and not paramboxopen:
                    if hand != "":
                        if handmode == ClickMode.AddGate:
                            row, col = getGateDropPos(x, y, circuitjson, config.gateSize)
                            addGate(circuitjson, hand, row, col)
                            circuitjson = refactorJSON(circuitjson)
                        elif handmode == ClickMode.DeleteGate:
                            row, col = getDeletePos(x, y, circuitjson, config.gateSize)
                            deleteGate(circuitjson, row, col)
                            circuitjson = refactorJSON(circuitjson)
                        elif handmode == ClickMode.MoveGate:
                            row, col = getGateDropPos(x, y, circuitjson, config.gateSize)
                            addGate(circuitjson, hand, row, col)
                            circuitjson = refactorJSON(circuitjson)

                    hand = ""
                    handmode = ClickMode.Empty

            if event.type == pygame.VIDEORESIZE:
                config.screenW = event.w
                config.screenH = event.h

        if paramboxopen:
            if parambox.update(events):
                paramboxopen = False
                newparam = parambox.get_text()
                parambox.clear_text()
                try:
                    newparams = newparam.split(',')
                    params = []
                    for param in newparams:
                        params.append(float(param))

                    hand["params"] = params
                    updateGate(hand)
                    hand = ""
                    handmode = ClickMode.Empty

                except ValueError:
                    warningMessage.warn("Invalid param format.", 100)

            surf = parambox.get_surface()
            pygame.draw.rect(screen, (100,100,100), (config.screenW/2 - 150, config.screenH/2 - 100, 300, 100),
                             border_radius=3)
            pygame.draw.rect(screen, (0, 0, 0), (config.screenW / 2 - 150, config.screenH / 2 - 100, 300, 100),
                             width=5, border_radius=3)
            PygameTools.displayText(screen, "Enter param: ", config.screenW/2,
                                    config.screenH/2 - 75, 25, (0,0,0))
            screen.blit(surf, (config.screenW/2 - 125, config.screenH/2 - 50))

        if editorfig is not None:
            editorfig.canvas.flush_events()

        pygame.display.update()
        clock.tick(30)
        # clock.tick() #for fps testing
        warningMessage.tick()

    pygame.display.quit()
    pyplot.ioff()
    pyplot.show()
    return save, circuitjson

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