from errors import *
from time import sleep
import traceback as tb
import warnings

print("Quantum engine starting...")
import qiskit
print("Loading qiskit version:", qiskit.version.get_version_info())
import CircuitJSONTools as qcJSON
import CircuitFileRenderer as qcRENDER
import QCircuitSimulator as qcSIMULATOR
print("Quantum engine started. Enter a command.")

config_recall = True
lastcmd = ""

def main():
    global lastcmd
    while True:
        sleep(0.1)
        rawcmd = input(">> ")

        allparts = rawcmd.split(' ')
        cmd = allparts.pop(0)
        lastcmd = rawcmd
        flags = []
        params = []
        for item in allparts:
            if item[0] == "-":
                flags.append(item)
            else:
                params.append(item)

        try:
            if cmd == "help":
                handleHelp(flags, params)

            elif cmd == "listcmds":
                handleListCmds(flags, params)

            elif cmd == "render":
                verifyCMD(flags, ["-t", "-c", "-h"], params, 1, 1)
                circuitjson = qcJSON.loadjson(params[0])
                qcJSON.validateJson(circuitjson)
                qc = qcJSON.assembleCircuit(circuitjson)
                qcRENDER.render(qc, flags)

            elif cmd == "compile":
                verifyCMD(flags, [], params, 1, 2)
                qcJSON.compileCircuit(params)

            elif cmd == "simulate":
                verifyCMD(flags, ['-t', '-b'], params, 1, 1)
                circuitjson = qcJSON.loadjson(params[0])
                qcJSON.validateJson(circuitjson)
                qc = qcJSON.assembleCircuit(circuitjson)
                result = qcSIMULATOR.simulate(qc)
                qcSIMULATOR.visualize(result, qc, flags)

            elif cmd == "preassemble":
                circuitjson = qcJSON.loadjson(params[0])
                qcJSON.validateJson(circuitjson)
                qcJSON.preassembleStages(circuitjson)

            elif cmd == "run":
                verifyCMD(flags, ['-s', '-t', '-b'], params, 1, 1)
                circuitjson = qcJSON.loadjson(params[0])
                qcJSON.validateJson(circuitjson)
                qc = qcJSON.assembleCircuit(circuitjson)
                result = qcSIMULATOR.sendToIBM(qc, useSimulator=('-s' in flags))
                qcSIMULATOR.visualize(result, qc, flags)

            else:
                raise CommandNotFoundError(cmd)

        except (CommandNotFoundError, UnexpectedFlag, ParameterError) as e:
            print(e)
        except InternalCommandException:
            print("Error while running command...")
            warnings.resetwarnings()
            pass #this should already throw a warning
        except (Exception,):
            tb.print_exc()

def handleHelp(flags, params):
    verifyCMD(flags, [], params, 0, 1)
    if len(params) == 0:
        print("Try help <cmd> for help with a command.")

    else:
        with open("help.txt") as f:
            lines = f.readlines()

        isprinting = False
        hasprinted = False
        for l in lines:
            if isprinting:
                if l.strip() != "":
                    if l[0] == "#":
                        isprinting = False
                    else:
                        print(l.strip())
            if l.strip() == "#" + params[0]:
                isprinting = True
                hasprinted = True
        if not hasprinted:
            print("Command not found.")

def handleListCmds(flags, params):
    verifyCMD(flags, [], params, 0, 0)
    with open("help.txt") as f:
        lines = f.readlines()

    commandlist = []
    for l in lines:
        if l[0] == "#":
            commandlist.append(l[1:].strip())
    print(commandlist)

import keyboard as k
import threading as t

def monitor():
    while True:
        sleep(0.01)
        if k.is_pressed('['):
            k.press_and_release("backspace")
            k.write(lastcmd)
            while k.is_pressed('['):
                sleep(0.01)

if __name__ == "__main__":
    if config_recall:
        t.Thread(target=monitor).start()
    main()