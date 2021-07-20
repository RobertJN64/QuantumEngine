from qiskit import transpile, execute, QuantumCircuit
from qiskit.providers.ibmq import least_busy
from qiskit import IBMQ
from qiskit.providers.aer import StatevectorSimulator as AerStatevetor
from qiskit.providers.aer import AerSimulator as Aer
from qiskit.tools.monitor import job_monitor
from errors import InternalCommandException
from qiskit.visualization import plot_histogram, plot_state_qsphere
import warnings
import matplotlib.pyplot as pyplot

provider = IBMQ.load_account()

def visualize(result, circuit, flags, sv=None):
    if '-t' in flags:
        print(result.get_counts(circuit))
    else:
        figa = pyplot.figure()
        plt = figa.add_subplot()
        plot_histogram(result.get_counts(), ax=plt)
        if '-q' in flags:
            figb = pyplot.figure()
            plt = figb.add_subplot()
            plot_state_qsphere(sv.get_statevector(circuit), ax=plt)

        pyplot.show()


def simulate(circuit, shots=1000):
    simulator = Aer()
    statevectorsimulator = AerStatevetor()
    compiled_circuit = transpile(circuit, simulator)
    circuit.remove_final_measurements()
    sv_circuit = transpile(circuit, statevectorsimulator)
    job = simulator.run(compiled_circuit, shots=shots)
    job2 = statevectorsimulator.run(sv_circuit, shots=shots)
    result = job.result()
    statevector = job2.result()
    return result, statevector

def sendToIBM(circuit: QuantumCircuit, shots=1000, useSimulator=False):
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
    print("Backend is running:", backend.status().pending_jobs, "jobs.")
    job = execute(circuit, backend, shots=shots)
    print("Job Queued")
    job_monitor(job)
    result = job.result()
    print("Job finished")
    return result