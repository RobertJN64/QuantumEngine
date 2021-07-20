import matplotlib.pyplot as pyplot

def render(qc, flags):
    if '-h' in flags:
        pass
    elif '-t' in flags:
        print(qc.draw("text"))
    elif '-c' in flags:
        #TODO - custom renderer
        pass
    else:
        fig = pyplot.figure()
        plt = fig.add_subplot()
        qc.draw("mpl", ax=plt)
        pyplot.show()


