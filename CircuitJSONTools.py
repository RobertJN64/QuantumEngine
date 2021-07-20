import warnings
import json
from errors import InternalCommandException

validgates = ["empty", "barrier", "multi", "h", "cx", "m"]

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

    return True

def assembleCircuit(circuitjson):
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

    for x in range(0, len(rows[0]["gates"])):
        for index, row in enumerate(rows):
            # print(row["gates"][x])
            gate = row["gates"][x]["type"]
            rcontrol = row["gates"][x].get("control", [])
            control = []
            for item in rcontrol:
                if item in rowidtable:
                    control.append(rowidtable.index(item))
                else:
                    if type(item) is int and item < len(rows):
                        control.append(item)
                    else:
                        warnings.warn(
                            "Gate in row " + str(index) + " at col " + str(x) + " requesting invalid control.")
                        raise InternalCommandException

            if gate == "empty" or gate == "multi":
                pass
            elif gate == "barrier":
                qc.barrier(index)
            elif gate == "h":
                qc.h(index)
            elif gate == "cx":
                qc.cx(control, index)
            elif gate == "m":
                qc.measure(index, index)
            else:
                warnings.warn("Gate <" + str(gate) + "> not yet implemented.")
                raise InternalCommandException
    return qc

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
        rawtext[i] = rawtext[i].strip().replace(" ", "").replace("(", "").replace(")", "")

    rawgatelist = []
    for line in rawtext:
        rawgatelist.append(line.split(','))

    # TODO - more than 10 lines
    gatelist = []
    for row in rawgatelist:
        gaterow = []
        for gate in row:
            gateinfo = ["", []]
            for letter in gate:
                if letter.isdigit():
                    gateinfo[1].append(int(letter))
                else:
                    gateinfo[0] += letter
            gaterow.append(gateinfo)
        gatelist.append(gaterow)

    for row in gatelist:
        for gate in row:
            if gate[0] == "":
                gate[0] = "empty"

    maxl = 0
    for row in gatelist:
        maxl = max(len(row), maxl)

    for row in gatelist:
        for i in range(len(row), maxl):
            row.append(["empty", []])

    for x in range(0, len(gatelist[0])):
        for row in gatelist:
            gate = row[x]
            if len(gate[1]) > 0:
                for item in gate[1]:
                    if item >= len(gatelist):
                        warnings.warn("Control requests at row " + str(item) + " col " + str(x) +
                                      " is out of range.")
                        raise InternalCommandException
                    newgate = gatelist[item][x][0]
                    if newgate != "empty":
                        warnings.warn("Because of control requests, gate at row " + str(item) + " col " + str(x) +
                                      " should be empty.")
                        raise InternalCommandException
                    else:
                        gatelist[item][x] = ["multi", []]

    jsonrows = []
    outjson = {"rows": jsonrows}
    for row in gatelist:
        jsonrow = []
        for gate in row:
            gatejson = {"type": gate[0]}
            if len(gate[1]) > 0:
                gatejson["control"] = gate[1]
            jsonrow.append(gatejson)
        jsonrows.append({"gates": jsonrow})

    validateJson(outjson)

    with open("circuits/" + fnameout + ".json", "w+") as f:
        json.dump(outjson, f, indent=4)