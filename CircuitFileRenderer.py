import matplotlib.pyplot as pyplot
from Puzzle import PuzzleValidator
import RenderBackend as Render
from RenderBackend import images, clickLocations, warningMessage
import PygameTools
from PygameTools import config, ClickMode, ClickLocation, UIMode
from errors import InternalCommandException
from CircuitJSONTools import refactorJSON, addGate, deleteGate, updateGate, assembleCircuit
from CustomVisualizations import visualize_transition
import QCircuitSimulator as qcSIM
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

def blitImageCommand(screen, file, x, y, size, command):
    screen.blit(images[file], (x, y))
    clickLocations.append(ClickLocation(x, y, size, size, target=command, mode=ClickMode.Command))

defaultgates = [["h", "x", "y", "z", "u"], ["m", "swap", "barrier", "reset"]]

def editor(circuitjson, title="Custom Circuit Render", gates=None,
           minrows=1, maxrows=50, allowcontrol = True, allowparams = True, ispuzzle=False,
           validator:PuzzleValidator=None):
    global editorfig

    if gates is None:
        gates = defaultgates
    if ispuzzle and validator is None:
        warnings.warn("Puzzle missing validator")
        raise InternalCommandException

    refactorJSON(circuitjson)
    hand = ""
    handmode = ClickMode.Empty
    currentmode = UIMode.Main
    parambox = TextInput()
    screen = PygameTools.createPygameWindow()
    done = False
    save = False
    clock = pygame.time.Clock()
    while not done:
        clickLocations.clear()
        screen.fill(config.screenColor)
        Render.drawCircuitToScreen(screen, circuitjson, title, minrows=minrows, maxrows=maxrows)

        tools = []
        if allowcontrol:
            tools.append("control")
        tools.append("delete")

        Render.drawGateToolbox(screen, gates, tools)
        PygameTools.displayText(screen, warningMessage.display(), config.screenW/2,
                                config.screenH - config.toolboxOffGround - config.gateSpacing * 1.5, 20, (200,0,0))

        PygameTools.displayText(screen, "FPS: " + str(round(clock.get_fps())), config.screenW - 100, 25, 15, (0, 0, 0))

        x = config.screenW - config.smallImageSize - 10
        blitImageCommand(screen, "save.png", x, (config.smallImageSize + 10) * 0 + 5, config.smallImageSize, "save")
        blitImageCommand(screen, "view.png", x, (config.smallImageSize + 10) * 1 + 5, config.smallImageSize, "view")
        blitImageCommand(screen, "bloch.png", x, (config.smallImageSize + 10) * 2 + 5, config.smallImageSize, "bloch")
        blitImageCommand(screen, "play.png", x, (config.smallImageSize + 10) * 3 + 5, config.smallImageSize, "play")
        if ispuzzle:
            blitImageCommand(screen, "check.png", x, (config.smallImageSize + 10) * 4 + 5, config.smallImageSize, "check")

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

            elif handmode == ClickMode.AddControl:
                pygame.draw.rect(screen, config.toolBackgroundColor,
                                 (x - config.gateSize / 2, y - config.gateSize / 2, config.gateSize, config.gateSize))
                pygame.draw.circle(screen, (0, 0, 0), (x, y), 10)
                row, col = getDeletePos(x, y, circuitjson, config.gateSize)
                if row is not None and col is not None and col != "end":
                    drawDropBox(screen, row, col, "box")
        #endregion

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and currentmode == UIMode.Main: #left click:
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

                            elif clickLoc.mode == ClickMode.AddControl:
                                hand = "addcontrol"

                            elif clickLoc.mode == ClickMode.ControlDot:
                                controlrow, colnum, gaterow = clickLoc.target
                                gatejson = circuitjson["rows"][gaterow]["gates"][colnum]
                                control = gatejson.get("control", [])
                                control.append(controlrow)
                                gatejson["control"] = control
                                circuitjson["rows"][gaterow]["gates"][colnum] = updateGate(gatejson)
                                circuitjson["rows"][controlrow]["gates"][colnum] = {"type": "multi"}
                                circuitjson = refactorJSON(circuitjson)

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
                                    editorfig.clf()
                                    render(assembleCircuit(circuitjson), circuitjson, [], editorfig)
                                    editorfig.canvas.mpl_connect('close_event', cleanclose)

                                elif clickLoc.target == "play":
                                    circuitjson = refactorJSON(circuitjson)
                                    qc = assembleCircuit(circuitjson)
                                    for i in range(0, len(circuitjson["rows"])):
                                        qc.measure(i,i)
                                    results = qcSIM.simulate(qc, 1000)
                                    if editorfig is None:
                                        editorfig = pyplot.figure()
                                    pyplot.ion()
                                    editorfig.clf()
                                    qcSIM.visualize(results, qc, [], editorfig)
                                    editorfig.canvas.mpl_connect('close_event', cleanclose)

                                elif clickLoc.target == "bloch":
                                    circuitjson = refactorJSON(circuitjson)
                                    vgates = True
                                    invgate = ""
                                    for row in circuitjson["rows"]:
                                        for gate in row["gates"]:
                                            if gate["type"] not in ["h", "x", "y", "z", "rx", "ry", "rz", "empty"]:
                                                invgate = gate["type"]
                                                vgates = False

                                    if vgates:
                                        visualize_transition(circuitjson, trace=True, spg=0.5, fpg=25)

                                    else: #TODO - stepthrough vis
                                        print("Error. We don't have a visualization for " + invgate + ".")

                                elif clickLoc.target == "check":
                                    circuitjson = refactorJSON(circuitjson)
                                    qc = assembleCircuit(circuitjson)
                                    if validator.validate(qc):
                                        print("Circuit solved puzzle!")
                                    else:
                                        print("Try again!")

                if event.button == 3 and currentmode == UIMode.Main:
                    for clickLoc in clickLocations:
                        if clickLoc.checkClick(x, y):
                            if clickLoc.mode == ClickMode.MoveGate and allowparams:
                                if clickLoc.target["type"][-1] in ["x", "y", "z", "u"]:
                                    handmode = ClickMode.EditParams
                                    hand = clickLoc.target
                                    currentmode = UIMode.ParamBoxOpen
                                    params = hand.get("params", [])
                                    p = []
                                    for param in params:
                                        p.append(str(round(param)))
                                    if len(p) == 0:
                                        p = ["180"]
                                    parambox.input_string = ", ".join(p)
                                    parambox.cursor_position = len(parambox.input_string)

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and currentmode == UIMode.Main:
                    if hand != "":
                        if handmode == ClickMode.AddGate:
                            row, col = getGateDropPos(x, y, circuitjson, config.gateSize)
                            addGate(circuitjson, hand, row, col)
                            circuitjson = refactorJSON(circuitjson)
                        elif handmode == ClickMode.DeleteGate:
                            row, col = getDeletePos(x, y, circuitjson, config.gateSize)
                            deleteGate(circuitjson, row, col)
                            circuitjson = refactorJSON(circuitjson)
                        elif handmode == ClickMode.AddControl:
                            rownum, col = getDeletePos(x, y, circuitjson, config.gateSize)

                            if rownum is not None and col is not None:
                                gatejson = circuitjson["rows"][rownum]["gates"][col]
                                if gatejson["type"] not in ["empty", "multi", "m", "barrier", "reset", "puzzle", "i"]:
                                    control = gatejson.get("control", [])
                                    allempty = True
                                    for index, row in enumerate(circuitjson["rows"]):
                                        if row["gates"][col]["type"] == "empty" or index == rownum:
                                            pass
                                        else:
                                            allempty = False

                                    for index, row in enumerate(circuitjson["rows"]):
                                        if allempty:
                                            if index != rownum and index not in control:
                                                row["gates"][col] = {"type": "addcontrol", "control": [rownum]}
                                        else:
                                            if index == rownum:
                                                row["gates"].insert(col + 1, {"type": "empty"})
                                            elif index in control:
                                                row["gates"].insert(col + 1, {"type": "empty"})
                                            else:
                                                row["gates"].insert(col, {"type": "addcontrol", "control": [rownum]})

                                else:
                                    warningMessage.warn("Can't add control to gate.", 100)

                        elif handmode == ClickMode.MoveGate:
                            row, col = getGateDropPos(x, y, circuitjson, config.gateSize)
                            addGate(circuitjson, hand, row, col)
                            circuitjson = refactorJSON(circuitjson)

                    hand = ""
                    handmode = ClickMode.Empty

            if event.type == pygame.VIDEORESIZE:
                config.screenW = event.w
                config.screenH = event.h

        if currentmode == UIMode.ParamBoxOpen:
            if parambox.update(events):
                currentmode = UIMode.Main
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

#region drop funcs
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
#endregion