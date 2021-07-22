from qiskit import QuantumCircuit
import warnings
from errors import InternalCommandException
from math import radians

validgates = []
singleparamgates = []
tripleparamsgates = []
controlgates = []
doublecontrolgates = []
multicontrolgates = []

pauligates = ["x", "y", "z"]
coremodifiers = ["", "c", "r", "cr", "mcr"]
universalgates = ["u", "cu"]
specialgates = ["ccx", "h", "ch", "i"]
othergates = ["swap", "cswap", "barrier", "reset"]
customgates = ["empty", "multi", "m"]  # TODO - if gate
for p in pauligates:
    for mod in coremodifiers:
        validgates.append(mod + p)
        if "c" in mod:
            if "mc" in mod:
                multicontrolgates.append(mod + p)
            else:
                controlgates.append(mod + p)

        if "r" in mod:
            singleparamgates.append(mod + p)


validgates += universalgates + specialgates + othergates + customgates
controlgates += ["cu", "swap"]
doublecontrolgates += ["ccx", "cswap"]
tripleparamsgates += ["u", "cu"]


def verifyGate(gatejson, row, col, rowidtable):
    gate = gatejson["type"]

    # region validate gates
    if gate in controlgates or gate in doublecontrolgates or gate in multicontrolgates:
        if "control" not in gatejson:
            warnings.warn("Gate at (" + str(row) + "," + str(col) + ") has control but is missing control in json.")
            raise InternalCommandException

        rcontrol = gatejson["control"]
        control = []
        for item in rcontrol:
            if item in rowidtable:
                control.append(rowidtable.index(item))
            else:
                if type(item) is int and item < len(rowidtable):
                    control.append(item)
                else:
                    warnings.warn("Gate at (" + str(row) + "," + str(col) + ") requesting invalid control.")
                    raise InternalCommandException

        if ((gate in controlgates and len(control) != 1) or (gate in doublecontrolgates and len(control) != 2) or
                (gate in multicontrolgates and len(control) == 0)):
            warnings.warn("Gate at (" + str(row) + "," + str(col) + ") has unexpected amount of controls.")
            raise InternalCommandException

    if gate in singleparamgates or gate in tripleparamsgates:
        if "params" not in gatejson:
            warnings.warn("Gate at (" + str(row) + "," + str(col) + ") has params but is missing params in json.")
            raise InternalCommandException

        params = gatejson["params"]
        if (gate in singleparamgates and len(params) != 1) or (gate in tripleparamsgates and len(params) != 3):
            if len(params) != 1:
                warnings.warn("Gate at (" + str(row) + "," + str(col) + ") has unexpected amount of params.")
                raise InternalCommandException
    # endregion


def addGate(qc: QuantumCircuit, gatejson: dict, row: int, col:int, rowidtable:list):
    gate = gatejson["type"]

    rcontrol = gatejson.get("control", [])
    control = []
    for item in rcontrol:
        if item in rowidtable:
            control.append(rowidtable.index(item))
        else:
            if type(item) is int and item < len(rowidtable):
                control.append(item)
            else:
                warnings.warn("Gate at (" + str(row) + "," + str(col) + ") requesting invalid control.")
                raise InternalCommandException

    rparams = gatejson.get("params", [])
    params = []
    for param in rparams:
        params.append(radians(param))

    if gate == "empty":
        pass
    elif gate == "multi":
        pass
    elif gate == "barrier":
        qc.barrier(row)
    elif gate == "reset":
        qc.reset(row)
    elif gate == "m":
        qc.measure(row,row)
    elif gate == "i":
        qc.i(row)

    elif gate == "h":
        qc.h(row)
    elif gate == "ch":
        qc.ch(control[0], row)

    elif gate == "x":
        qc.x(row)
    elif gate == "y":
        qc.y(row)
    elif gate == "z":
        qc.z(row)

    elif gate == "rx":
        qc.rx(params[0], row)
    elif gate == "ry":
        qc.ry(params[0], row)
    elif gate == "rz":
        qc.rz(params[0], row)

    elif gate == "cx":
        qc.cx(control[0], row)
    elif gate == "cy":
        qc.cy(control[0], row)
    elif gate == "cz":
        qc.cz(control[0], row)

    elif gate == "crx":
        qc.crx(params[0], control[0], row)
    elif gate == "cry":
        qc.cry(params[0], control[0], row)
    elif gate == "crz":
        qc.crz(params[0], control[0], row)

    elif gate == "ccx":
        qc.ccx(control[0], control[1], row)
    elif gate == "mcrx":
        qc.mcrx(params[0], control, row)
    elif gate == "mcry":
        qc.mcry(params[0], control, row)
    elif gate == "mcrz":
        qc.mcrz(params[0], control, row)

    elif gate == "u":
        qc.u(params[0], params[1], params[2], row)
    elif gate == "cu":
        qc.cu(params[0], params[1], params[2], 0, control[0], row)

    elif gate == "swap":
        qc.swap(control[0], row)
    elif gate == "cswap":
        qc.cswap(control[0], control[1], row)


    else:
        warnings.warn("Gate <" + str(gate) + "> not yet implemented.")
        raise InternalCommandException