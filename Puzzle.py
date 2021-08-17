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


def loadPuzzle(fname):
    with open("puzzles/" + fname + ".json") as f:
        puzzlejson = json.load(f)

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