import matplotlib.pyplot as pyplot
from Puzzle import PuzzleValidator
import RenderBackend as Render
from RenderBackend import images, clickLocations, warningMessage
from DragAndDropTools import drawDropBox, getGateDropPos, getDeletePos
import PygameTools
from PygameTools import config, ClickMode, UIMode
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


defaultgates = [["h", "x", "y", "z", "u"], ["m", "swap", "barrier", "reset"]]

def editor(circuitjson, title="Custom Circuit Render", gates=None,
           minrows=1, maxrows=50, allowcontrol = True, allowparams = True, ispuzzle=False,
           validator:PuzzleValidator=None, infobox="", startscreen=None):
    global editorfig

    if gates is None:
        gates = defaultgates
    if ispuzzle and validator is None:
        warnings.warn("Puzzle missing validator")
        raise InternalCommandException

    refactorJSON(circuitjson)
    hand = ""
    handmode = ClickMode.Empty

    if infobox != "":
        currentmode = UIMode.InfoBoxOpen
    else:
        currentmode = UIMode.Main

    parambox = TextInput()
    if startscreen is None:
        screen = PygameTools.createPygameWindow()
    else:
        screen = startscreen

    done = False
    save = False
    clock = pygame.time.Clock()

    blocha = None
    blochb = None
    svimg = None

    blochheight = config.blochSphereHeight
    blochwidth = 0

    tools = []
    if allowcontrol:
        tools.append("control")
    tools.append("delete")

    pygame.event.pump() #stops clicks from carrying over...
    warningMessage.timer = 0 #stops message from carrying over

    while not done:
        clickLocations.clear()
        screen.fill(config.screenColor)
        Render.drawCircuitToScreen(screen, circuitjson, title, minrows=minrows, maxrows=maxrows)
        Render.drawGateToolbox(screen, gates, tools)
        text, color = warningMessage.display()
        PygameTools.displayText(screen, text, config.screenW/2,
                                config.screenH - config.toolboxOffGround - config.gateSpacing * 1.5, 20, color)
        PygameTools.displayText(screen, "FPS: " + str(round(clock.get_fps())), config.screenW - 100, 25, 15, (0, 0, 0))
        Render.displayCommandImages(screen, ispuzzle)

        #region drag and drop
        x, y = pygame.mouse.get_pos()
        if hand != "":
            if handmode == ClickMode.AddGate or handmode == ClickMode.MoveGate:
                Render.drawGate(screen, hand, x, y)
                row, col = getGateDropPos(x, y, circuitjson, config.gateSize)
                if (row is not None) and (col is not None):
                    if col == "end":
                        depth, t = len(circuitjson["rows"][row]["gates"]), "box"

                    elif circuitjson["rows"][row]["gates"][col]["type"] == "empty":
                        depth, t = col, "box"

                    else:
                        if col > 0 and circuitjson["rows"][row]["gates"][col-1]["type"] == "empty":
                            depth, t = col - 1, "box"

                        else:
                            depth, t = col, "line"

                    drawDropBox(screen, row, depth, t)

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

        if currentmode == UIMode.BlochSphereTargetBoxOpen:
            tlx, tly = Render.drawBlochSpheres(screen, blocha, blochb, blochwidth, blochheight)
            Render.blitImageCommand(screen, "close.png", tlx - config.smallImageSize, tly, config.smallImageSize, "close")

        elif currentmode == UIMode.CompareStatevectorTargetBoxOpen:
            tlx, tly = Render.drawStatevector(screen, svimg)
            Render.blitImageCommand(screen, "close.png", tlx - config.smallImageSize, tly, config.smallImageSize, "close")

        elif currentmode == UIMode.InfoBoxOpen:
            tlx, tly = Render.textBox(screen, infobox)
            Render.blitImageCommand(screen, "close.png", tlx - config.smallImageSize, tly, config.smallImageSize,
                                    "close")

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                done = True

            elif event.type == pygame.MOUSEBUTTONDOWN:
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

                                    else: #TODO - qsphere vis
                                        print("Error. We don't have a visualization for " + invgate + ".")

                                elif clickLoc.target == "check":
                                    circuitjson = refactorJSON(circuitjson)
                                    qc = assembleCircuit(circuitjson)
                                    if validator.validate(qc):
                                        warningMessage.warn("Circuit solved puzzle!", 120, color=(0, 0, 0))
                                    else:
                                        warningMessage.warn("Try again", 120, color=(255,0,0))

                                elif clickLoc.target == "target":
                                    circuitjson = refactorJSON(circuitjson)
                                    qca = assembleCircuit(circuitjson)
                                    qcb = assembleCircuit(validator.correctcircuitjson)
                                    resultsa = qcSIM.simulate(qca, 1000)
                                    resultsb = qcSIM.simulate(qcb, 1000)
                                    if validator.validationMode == "statevector":
                                        qcSIM.save_bloch_multivector(resultsa, qca, "blocha")
                                        qcSIM.save_bloch_multivector(resultsb, qcb, "blochb")

                                        blocha = pygame.image.load("resources/dynamic/blocha.png")
                                        blochb = pygame.image.load("resources/dynamic/blochb.png")
                                        recta = blocha.get_rect()
                                        rectb = blochb.get_rect()

                                        wa = round(recta.w * (blochheight / recta.h))
                                        wb = round(rectb.w * (blochheight / rectb.h))

                                        blochwidth = max(wa, wb)

                                        blocha = pygame.transform.smoothscale(blocha, (wa, blochheight))
                                        blochb = pygame.transform.smoothscale(blochb, (wb, blochheight))

                                        currentmode = UIMode.BlochSphereTargetBoxOpen

                                    elif validator.validationMode == "results":
                                        qcSIM.save_compare_statevector(
                                            [resultsa.get_counts(qca), resultsb.get_counts(qcb)], ["Current", "Target"],
                                                                       ['b', 'r'], allkeys=config.statevectorAllKeys)
                                        svimg = pygame.image.load("resources/dynamic/statevector.png")
                                        r = svimg.get_rect()
                                        if r.w/config.screenW > r.h/config.screenH:
                                            w = round(config.screenW/1.5)
                                            h = round(r.h * w/r.w)

                                        else:
                                            h = round(config.screenH / 1.5)
                                            w = round(r.w * h / r.h)

                                        svimg = pygame.transform.smoothscale(svimg, (w, h))
                                        currentmode = UIMode.CompareStatevectorTargetBoxOpen

                                    else:
                                        warnings.warn("Unknown validation mode: " + str(validator.validationMode))
                                        raise InternalCommandException

                elif event.button == 1 and (currentmode == UIMode.BlochSphereTargetBoxOpen
                                            or currentmode == UIMode.CompareStatevectorTargetBoxOpen): #left click:
                    for clickLoc in clickLocations:
                        if clickLoc.checkClick(x, y):
                            handmode = clickLoc.mode
                            if clickLoc.mode == ClickMode.Command:
                                if clickLoc.target == "target":
                                    currentmode = UIMode.Main
                                elif clickLoc.target == "close":
                                    currentmode = UIMode.Main

                elif event.button == 1 and currentmode == UIMode.InfoBoxOpen:
                    for clickLoc in clickLocations:
                        if clickLoc.checkClick(x, y):
                            handmode = clickLoc.mode
                            if clickLoc.mode == ClickMode.Command and clickLoc.target == "close":
                                currentmode = UIMode.Main

                elif event.button == 3 and currentmode == UIMode.Main:
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
                                else:
                                    warningMessage.warn("Can't add param to that gate.", 100)
                            elif not allowparams:
                                warningMessage.warn("You can't add params in this circuit.", 100)


            elif event.type == pygame.MOUSEBUTTONUP:
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

            elif event.type == pygame.VIDEORESIZE:
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

            else:
                Render.drawParamBox(screen, parambox)

        if editorfig is not None:
            editorfig.canvas.flush_events()

        pygame.display.update()
        clock.tick(30)
        # clock.tick() #for fps testing
        warningMessage.tick()

    if startscreen is None:
        pygame.display.quit()
    pyplot.ioff()
    pyplot.show()
    return save, circuitjson
