import json
import CircuitFileRenderer as CFR
from errors import InternalCommandException
from CircuitJSONTools import validateJSON, assembleCircuit, saveJSON
from QCircuitSimulator import simulate
from qiskit.quantum_info import Statevector
import warnings

def validatePuzzle(puzzlejson):
    for key in ["name", "info", "circuit", "unlocked-gates", "minrows", "maxrows", "allowcontrol", "allowparams",
                "validation-mode"]:
        if key not in puzzlejson:
            warnings.warn("Puzzle json missing key: " + key)
            raise InternalCommandException

    if puzzlejson["validation-mode"] not in ["statevector", "results"]:
        warnings.warn("Unexpected validation mode.")
        raise InternalCommandException

    if puzzlejson["validation-mode"] in ["statevector", "results"]:
        if "validation-circuit" not in puzzlejson:
            warnings.warn("Puzzle json missing key: " + "validation-circuit")
            raise InternalCommandException
        validateJSON(puzzlejson["validation-circuit"])

    validateJSON(puzzlejson["circuit"])

    if not (puzzlejson["minrows"] <= len(puzzlejson["circuit"]["rows"]) <= puzzlejson["maxrows"]):
        warnings.warn("Puzzle row count not in valid range!")
        raise InternalCommandException

#region internal validators
def validateStatevector(circuita, circuitb, tolerance):
    if tolerance == tolerance:
        pass
    a = simulate(circuita)
    b = simulate(circuitb)

    sa = Statevector(a.get_statevector(circuita))
    sb = Statevector(b.get_statevector(circuitb))
    return sa.equiv(sb)

def validateResults(circuita, circuitb, tolerance):
    a = simulate(circuita)
    b = simulate(circuitb)

    da = a.get_counts(circuita)
    db = b.get_counts(circuitb)

    for key, valuea in da.items():
        valueb = db.get(key, 0)
        if abs(valuea - valueb) > tolerance * 1000: #number of shots
            return False

    for key, valueb in db.items():
        valuea = da.get(key, 0)
        if abs(valuea - valueb) > tolerance * 1000: #number of shots
            return False

    return True

def validateNone(circuita, circuitb, tolerance):
    if circuita == circuitb or tolerance == tolerance:
        pass
    warnings.warn("Validation none error case triggered!")
    raise InternalCommandException

class PuzzleValidator:
    def __init__(self, puzzlejson, tolerance):
        self.correctcircuitjson = puzzlejson["validation-circuit"]
        self.validationMode = puzzlejson["validation-mode"]
        self.validationFunction = validateNone
        self.tolerance = tolerance
        if puzzlejson["validation-mode"] == "statevector":
            self.validationFunction = validateStatevector
        elif puzzlejson["validation-mode"] == "results":
            self.validationFunction = validateResults

    def validate(self, circuit):
        return self.validationFunction(circuit, assembleCircuit(self.correctcircuitjson), self.tolerance)
#endregion

def loadPuzzle(fname):
    try:
        with open("puzzles/" + fname + ".json") as f:
            puzzlejson = json.load(f)
    except FileNotFoundError:
        warnings.warn("Puzzle file not found.")
        raise InternalCommandException

    validatePuzzle(puzzlejson)
    print(puzzlejson["info"]) #TODO - info box
    save, circuitjson = CFR.editor(puzzlejson["circuit"],
               title=puzzlejson["name"],
               ispuzzle=True,
               validator=PuzzleValidator(puzzlejson, puzzlejson.get("tolerance", 0.1)),
               gates=puzzlejson["unlocked-gates"],
               minrows=puzzlejson["minrows"],
               maxrows=puzzlejson["maxrows"],
               allowcontrol=puzzlejson["allowcontrol"],
               allowparams=puzzlejson["allowparams"])

    validateJSON(circuitjson)
    if save:
        saveJSON(circuitjson, input("File name: "))

def loadPuzzleset(fname):
    try:
        with open("puzzles/" + fname + ".json") as f:
            puzzleset = json.load(f)
    except FileNotFoundError:
        warnings.warn("Puzzle set file not found.")
        raise InternalCommandException

    for puzzle in puzzleset:
        try:
            open("puzzles/" + puzzle + ".json")
        except FileNotFoundError:
            warnings.warn("Puzzle <" + str(puzzle) + "> file not found.")
            raise InternalCommandException

    for puzzle in puzzleset:
        loadPuzzle(puzzle)

def editPuzzle(fname):
    try:
        with open("puzzles/" + fname + ".json") as f:
            puzzle = json.load(f)
            print("You are editting an existing puzzle...")

    except FileNotFoundError:
        print("You are creating a new puzzle...")
        puzzle = {}

    if "name" not in puzzle or input("Puzzle name is: " + str(puzzle["name"]) + " Change? ") == "y":
        puzzle["name"] = input("Enter puzzle name: ")

    if "info" not in puzzle or input("Puzzle description is:\n" + str(puzzle["info"]) + "\nChange? ") == "y":
        puzzle["info"] = input("Enter puzzle description: ")

    if "allowcontrol" not in puzzle or input("Puzzle allowcontrol is: " + str(puzzle["allowcontrol"])  + " Change? ") == "y":
        puzzle["allowcontrol"] = input("Enter puzzle allowcontrol: ").lower() == "true"

    if "allowparams" not in puzzle or input("Puzzle allowparams is: " + str(puzzle["allowparams"])  + " Change? ") == "y":
        puzzle["allowparams"] = input("Enter puzzle allowparams: ").lower() == "true"

    if "minrows" not in puzzle or input("Puzzle minrows is: " + str(puzzle["minrows"])  + " Change? ") == "y":
        puzzle["minrows"] = int(input("Enter puzzle minrows: "))

    if "maxrows" not in puzzle or input("Puzzle maxrows is: " + str(puzzle["minrows"])  + " Change? ") == "y":
        puzzle["minrows"] = int(input("Enter puzzle maxrows: "))

    if "unlocked-gates" not in puzzle or input("Puzzle unlocked gates is:\n" + str(puzzle["minrows"])  + "\nChange? ") == "y":
        done = False
        groups = []
        while not done:
            gates = input("Enter gate group: ")
            gates = gates.split(',')
            for i in range(0, len(gates)):
                gates[i] = gates[i].replace(' ', '')
            groups.append(gates)
            done = input("Done? ") == "y"
        puzzle["unlocked-gates"] = groups

    if "validation-circuit" not in puzzle or input("Change validation circuit? ") == "y":
        print("Build puzzle solution.")
        startingcircuit = {"rows": [{"gates": []}]}
        save, cjson = CFR.editor(startingcircuit, "Puzzle Solution", puzzle["unlocked-gates"], puzzle["minrows"],
                                puzzle["maxrows"], puzzle["allowcontrol"], puzzle["allowparams"])
        if save:
            puzzle["validation-circuit"] = cjson

    if "circuit" not in puzzle or input("Change starting circuit? ") == "y":
        print("Build staring circuit.")
        startingcircuit = {"rows": [{"gates": []}]}
        save, cjson = CFR.editor(startingcircuit, "Puzzle Solution", puzzle["unlocked-gates"], puzzle["minrows"],
                                puzzle["maxrows"], puzzle["allowcontrol"], puzzle["allowparams"])
        if save:
            puzzle["circuit"] = cjson

    if "validation-mode" not in puzzle or input("Puzzle validation mode is: " + str(puzzle["validation-mode"])  + " Change? ") == "y":
        newmode = ""
        while newmode not in ["statevector, results"]:
            newmode = str(input("Enter puzzle validation mode (statevector / results): "))
        puzzle["validation-mode"] = newmode

    if (puzzle["validation-mode"] == "results" and
            ("tolerance" not in puzzle or input("Puzzle validation tolerance is: " + str(puzzle["tolerance"])  + " Change? ") == "y")):
        puzzle["tolerance-mode"] = str(input("Enter puzzle validation tolerance: "))

    validatePuzzle(puzzle)

    if input("Save changes?: ") == "y":
        with open("puzzles/" + fname + ".json", "w+") as f:
            json.dump(puzzle, f, indent=4)
