import warnings
import json
from errors import InternalCommandException
from GateAssembler import createGate, verifyGate, validgates, updateGate

#TODO - handle control wire overlap

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

def loadJSON(fname):
    """Loads a circuit file and returns it"""
    try:
        with open("circuits/" + fname + ".json") as f:
            circuitjson = json.load(f)

    except FileNotFoundError:
        warnings.warn("Could not find file.")
        raise InternalCommandException

    return circuitjson

def saveJSON(circuitjson, fname):
    """Saves a circuit file"""
    with open("circuits/" + fname + ".json", "w+") as f:
        json.dump(circuitjson, f, indent=2)

def validateJSON(circuitjson):
    """Loads JSON and warns if there are any errors."""
    if "rows" not in circuitjson or len(circuitjson["rows"]) == 0:
        warnings.warn("Malformed file. Missing rows.")
        raise InternalCommandException

    rows = circuitjson["rows"]
    for index, row in enumerate(rows):
        if "gates" not in row:
            warnings.warn("Row # " + str(index) + " missing gates.")
            raise InternalCommandException


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
            control = row["gates"][x].get("control", [])
            for item in control:
                if type(item) is int and item < len(rows):
                    pass
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
            verifyGate(row["gates"][x], index, x, len(rows))

    return True

def refactorJSON(circuitjson):
    """Recursive refactoring of JSON to remove empty lines and such..."""
    madechange = False
    #print(circuitjson)
    rows = circuitjson["rows"]

    targetlen = len(rows[0]["gates"])
    for row in rows:
        if len(row["gates"]) != targetlen:
            print(circuitjson)
            warnings.warn("Circuit json length error.")
            raise InternalCommandException

    removecols = []
    depth = len(rows[0]["gates"])
    for col in range(0, depth):
        allempty = True
        for index, row in enumerate(rows):
            gatejson = row["gates"][col]
            gate = gatejson["type"]

            if gate != "empty":
                allempty = False

        if allempty:
            removecols.append(col)

    removecols.reverse()

    for col in removecols:
        for row in rows:
            row["gates"].pop(col)
            madechange = True

    depth = len(rows[0]["gates"])
    if depth > 1:
        for col in range(1, depth):
            for index, row in enumerate(rows):
                gateajson = row["gates"][col-1]
                gatebjson = row["gates"][col]

                if (gateajson["type"] == "empty" and len(gatebjson.get("control", [])) == 0
                    and gatebjson["type"] not in ["empty", "multi"]):
                    row["gates"][col-1] = gatebjson
                    row["gates"][col] = gateajson
                    madechange = True

    if madechange:
        return refactorJSON(circuitjson) #recursion
    else:
        return circuitjson

def assembleCircuit(circuitjson, depth=0):
    """Returns a QuantumCircuit."""
    rows = circuitjson["rows"]

    from qiskit import QuantumCircuit
    qc = QuantumCircuit(len(rows), len(rows))

    if depth == 0:
        depth = len(rows[0]["gates"])

    for x in range(0, depth):
        for index, row in enumerate(rows):
            createGate(qc, row["gates"][x], index, x, len(rows))
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

    validateJSON(outjson)

    with open("circuits/" + fnameout + ".json", "w+") as f:
        json.dump(outjson, f, indent=4)


def addGate(circuitjson, gate, rownum, colnum):
    if gate["type"] in "u, cu":
        if len(gate.get("params", [])) == 0:
            gate["params"] = [0,0,0]
    if (rownum is not None) and (colnum is not None):
        if colnum == "end":
            for index, row in enumerate(circuitjson["rows"]):
                if index == rownum:
                    row["gates"].append(gate)
                else:
                    row["gates"].append({"type": "empty"})

        elif circuitjson["rows"][rownum]["gates"][colnum]["type"] == "empty":
            circuitjson["rows"][rownum]["gates"][colnum] = gate

        else:
            if colnum > 0 and circuitjson["rows"][rownum]["gates"][colnum - 1]["type"] == "empty":
                circuitjson["rows"][rownum]["gates"][colnum - 1] = gate
            else:
                for index, row in enumerate(circuitjson["rows"]):
                    if index == rownum:
                        row["gates"].insert(colnum, gate)
                    else:
                        row["gates"].insert(colnum, {"type": "empty"})

def deleteGate(circuitjson, rownum, colnum):
    if (rownum is not None) and (colnum is not None):
        gatejson = circuitjson["rows"][rownum]["gates"][colnum]

        if gatejson["type"] == "empty":
            warnings.warn("Deleting empty gate!")
            raise InternalCommandException

        if gatejson["type"] == "multi":
            for row in circuitjson["rows"]:
                gatejsonb = row["gates"][colnum]
                control = gatejsonb.get("control", [])
                if rownum in control:
                    control.remove(rownum)
                    row["gates"][colnum] = updateGate(gatejsonb)
            gatejson["type"] = "empty"

        elif len(gatejson.get("control", [])) == 0:
            circuitjson["rows"][rownum]["gates"][colnum] = {"type": "empty"}

        elif len(gatejson.get("control", [])) > 0:
            for item in gatejson["control"]:
                circuitjson["rows"][item]["gates"][colnum] = {"type": "empty"}
            circuitjson["rows"][rownum]["gates"][colnum] = {"type": "empty"}

        else:
            warnings.warn("Unexpected format for gatejson: " + str(gatejson))
            raise InternalCommandException