class CommandNotFoundError(Exception):
    def __init__(self, command):
        self.message = "Command <" + command + "> not found"

    def __str__(self):
        return self.message

class UnexpectedFlag(Exception):
    def __init__(self, flag):
        if type(flag) is list:
            if len(flag) == 1:
                self.message = "Unexpected flag: " + str(flag[0])
            else:
                self.message = "Unexpected flags: " + str(flag)
        else:
            self.message = "Unexpected flag: " + str(flag)

    def __str__(self):
        return self.message

class ParameterError(Exception):
    def __init__(self, given, expected):
        self.message = ("This command takes " + str(expected) + " parameter" +
                        ("s" * (expected != 1)) + ", but " + str(given) +
                        " " + ("were" * (given != 1)) + ("was" * (given == 1)) + " given.")

    def __str__(self):
        return self.message

class InternalCommandException(Exception):
    pass

def verifyCMD(flags, expectedFlags, params, pmin, pmax):
    invalidFlags = []
    for flag in flags:
        if flag not in expectedFlags:
            invalidFlags.append(flag)
    if len(invalidFlags) > 0:
        raise UnexpectedFlag(invalidFlags)

    if len(params) > pmax:
        raise ParameterError(len(params), pmax)

    if len(params) < pmin:
        raise ParameterError(len(params), pmin)