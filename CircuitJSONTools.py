import warnings
import json
from errors import InternalCommandException
from GateAssembler import addGate, verifyGate, validgates

class Gate:
    def __init__(self, gatestr: str, row, col):
        self.parts = gatestr.split()
        self.control = []
        self.params = []
        self.gatename = ""

        passedGateName = False
        for item in self.parts:
            if item.isalpha():
                if self.gatename != "":
                    warnings.warn("Gate at (" + str(row) + "," + str(col) + ") can only have one name.")
                    raise InternalCommandException
                self.gatename = item
                passedGateName = True
            else:
                try:
                    if not passedGateName:
                        self.control.append(round(float(item),6))
                    else:
                        self.params.append(round(float(item),6))
                except ValueError:
                    warnings.warn("Gate at (" + str(row) + "," + str(col) + ") has non float number.")
                    raise InternalCommandException

        if self.gatename == "":
            warnings.warn("Gate at (" + str(row) + "," + str(col) + ") missing.")
            raise InternalCommandException

    def getJson(self):
        d = {"type": self.gatename}
        if len(self.control) > 0:
            d["control"] = self.control
        if len(self.params) > 0:
            d["params"] = self.params
        return d


def loadjson(fname):
    """Loads a circuit file and returns it"""
    try:
        with open("circuits/" + fname + ".json") as f:
            circuitjson = json.load(f)

    except FileNotFoundError:
        warnings.warn("Could not find file.")
        raise InternalCommandException

    return circuitjson

def validateJson(circuitjson):
    """Loads JSON and warns if there are any errors."""
    if "rows" not in circuitjson or len(circuitjson["rows"]) == 0:
        warnings.warn("Malformed file. Missing rows.")
        raise InternalCommandException

    rows = circuitjson["rows"]
    for index, row in enumerate(rows):
        if "gates" not in row:
            warnings.warn("Row # " + str(index) + " missing gates.")
            raise InternalCommandException

    rowidtable = []
    for index, row in enumerate(rows):
        if "id" in row:
            rowidtable.append(row["id"])
        else:
            rowidtable.append(index)

    maxlen = 0
    for row in rows:
        maxlen = max(len(row["gates"]), maxlen)

    for row in rows:
        for i in range(len(row["gates"]), maxlen):
            row.append({"type": "empty"})

    for rownum, row in enumerate(rows):
        gates = row["gates"]
        for index, gate in enumerate(gates):
            if "type" not in gate:
                warnings.warn("Gate in row #: " + str(rownum) + " missing gate type at gate: " + str(index))
                raise InternalCommandException
            if gate["type"] not in validgates:
                warnings.warn("Gate <" + str(gate["type"]) + "> not valid.")
                raise InternalCommandException

    for x in range(0, len(rows[0]["gates"])):
        mult_expected = []
        mult_used = []
        for index, row in enumerate(rows):
            #print(row["gates"][x])
            rcontrol = row["gates"][x].get("control", [])
            control = []
            for item in rcontrol:
                if item in rowidtable:
                    control.append(rowidtable.index(item))
                else:
                    if type(item) is int and item < len(rows):
                        control.append(item)
                    else:
                        warnings.warn("Gate in row " + str(index) + " at col " + str(x) + " requesting invalid control.")
                        raise InternalCommandException

        for item in mult_expected:
            if item in mult_used:
                mult_used.remove(item)
            else:
                warnings.warn("Error in parsing multigates on collumn " + str(x))
                raise InternalCommandException
        if len(mult_used) > 0:
            warnings.warn("Error in parsing multigates on collumn " + str(x))
            raise InternalCommandException

    for x in range(0, len(rows[0]["gates"])):
        for index, row in enumerate(rows):
            verifyGate(row["gates"][x], index, x, rowidtable)

    return True

def assembleCircuit(circuitjson, depth=0):
    """Returns a QuantumCircuit."""
    rows = circuitjson["rows"]
    rowidtable = []
    for index, row in enumerate(rows):
        if "id" in row:
            rowidtable.append(row["id"])
        else:
            rowidtable.append(index)

    from qiskit import QuantumCircuit
    qc = QuantumCircuit(len(rows), len(rows))

    if depth == 0:
        depth = len(rows[0]["gates"])

    for x in range(0, depth):
        for index, row in enumerate(rows):
            addGate(qc, row["gates"][x], index, x, rowidtable)
    return qc

def preassembleStages(circuitjson):
    rows = circuitjson["rows"]
    depth = len(rows[0]["gates"])
    circuits = []
    for i in range(1, depth):
        circuits.append(assembleCircuit(circuitjson, i))
    for c in circuits:
        print(c.draw())
        print("----------------------------------")
    return circuits

def compileCircuit(params):
    """Converts a txt file to a JSON file"""
    fnamein = params[0]
    if len(params) > 1:
        fnameout = params[1]
    else:
        fnameout = fnamein

    try:
        with open("circuits/" + fnamein + ".txt") as f:
            rawtext = f.readlines()

    except FileNotFoundError:
        warnings.warn("Could not find file.")
        raise InternalCommandException

    for i in range(0, len(rawtext)):
        rawtext[i] = rawtext[i].strip()

    rawgatelist = []
    for line in rawtext:
        rawgatelist.append(line.split(','))

    gatelist = []
    for rownum, row in enumerate(rawgatelist):
        gaterow = []
        for colnum, gate in enumerate(row):
            if len(gate) == 0:
                gaterow.append({"type": "empty"})
            else:
                gate = Gate(gate, rownum, colnum)
                gaterow.append(gate.getJson())
        gatelist.append(gaterow)

    maxl = 0
    for row in gatelist:
        maxl = max(len(row), maxl)

    for row in gatelist:
        for i in range(len(row), maxl):
            row.append({"type": "empty"})

    for col in range(0, len(gatelist[0])):
        for rownum, row in enumerate(gatelist):
            gate = row[col]
            control = gate.get("control", [])

            for item in control:
                if item >= len(gatelist):
                    warnings.warn("Control requests at row " + str(rownum) + " col " + str(col) +
                                  " is out of range.")
                    raise InternalCommandException
                controlgate = gatelist[item][col]["type"]
                if controlgate != "empty":
                    warnings.warn("Because of control requests, gate at row " + str(item) + " col " + str(col) +
                                  " should be empty.")
                    raise InternalCommandException
                else:
                    gatelist[item][col]["type"] = "multi"

    jsonrows = []
    for row in gatelist:
        jsonrows.append({"gates": row})
    outjson = {"rows": jsonrows}

    validateJson(outjson)

    with open("circuits/" + fnameout + ".json", "w+") as f:
        json.dump(outjson, f, indent=4)