import qiskit.providers
from qiskit import transpile, execute
from qiskit.providers.ibmq import least_busy
from qiskit import IBMQ
from qiskit.providers.aer import AerSimulator as Aer
from qiskit.tools.monitor import job_monitor
from errors import InternalCommandException
from qiskit.visualization import plot_histogram, plot_bloch_multivector
import warnings
import matplotlib.pyplot as pyplot
import threading

provider:qiskit.providers.ibmq.AccountProvider
provideractive = False
def loadaccount():
    global provider
    global provideractive
    provider = IBMQ.load_account()
    provideractive = True
threading.Thread(target=loadaccount).start()

def visualize(result, circuit, flags):
    if '-t' in flags:
        print(result.get_counts(circuit))
    else:
        fig = pyplot.figure()
        plt = fig.add_subplot()
        plot_histogram(result.get_counts(circuit), ax=plt)
        if '-b' in flags:
            plot_bloch_multivector(result.get_statevector(circuit))
            print(result.get_statevector(circuit))

        pyplot.show()


def simulate(circuit, shots=1000):
    simulator = Aer()
    circuit.save_statevector()
    compiled_circuit = transpile(circuit, simulator)
    job = simulator.run(compiled_circuit, shots=shots)
    result = job.result()
    return result

def sendToIBM(circuit, shots=1000, useSimulator=False):
    if not provideractive:
        print("Issue loading account... Please wait while we retry...")
    while not provideractive:
        pass
    backends = provider.backends(filters=lambda x: x.configuration().n_qubits >= circuit.num_qubits
                                        and (not x.configuration().simulator or useSimulator)
                                        and x.status().operational == True)
    if len(backends) == 0:
        warnings.warn("No backends found. Try simulators or simulating locally.")
        raise InternalCommandException
    backend = least_busy(backends)
    config = backend.configuration()
    print("Found ", "simulator " * config.simulator, "backend: ", backend.name(),
          " with version ", config.backend_version, sep="")
    print("Backend has", config.n_qubits, "qubits,", circuit.num_qubits, "needed.")
    print("Backend is running:", backend.status().pending_jobs, "jobs waiting.")
    job = execute(circuit, backend, shots=shots)
    print("Job Queued")
    job_monitor(job)
    result = job.result()
    print("Job finished")
    return result