import json
import CircuitFileRenderer as CFR

def loadPuzzle(fname):
    with open("puzzles/" + fname + ".json") as f:
        puzzlejson = json.load(f)

    CFR.editor(puzzlejson["circuit"],
               title=puzzlejson["name"],
               gates=puzzlejson["unlocked-gates"],
               minrows=puzzlejson["minrows"],
               maxrows=puzzlejson["maxrows"],
               allowcontrol=puzzlejson["allowcontrol"])