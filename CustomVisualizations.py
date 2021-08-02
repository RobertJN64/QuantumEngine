# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2018.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

#Modified from original to allow for multigate vis

"""
Visualization function for animation of state transitions by applying gates to single qubit.
"""

from math import sin, cos, acos, sqrt, radians, degrees
import numpy as np

def _normalize(v, tolerance=0.00001):
    """Makes sure magnitude of the vector is 1 with given tolerance"""

    mag2 = sum(n * n for n in v)
    if abs(mag2 - 1.0) > tolerance:
        mag = sqrt(mag2)
        v = tuple(n / mag for n in v)
    return np.array(v)

class _Quaternion:
    """For calculating vectors on unit sphere"""

    def __init__(self):
        self.val = None

    @staticmethod
    def from_axisangle(theta, v):
        """Create quaternion from axis"""
        v = _normalize(v)

        new_quaternion = _Quaternion()
        new_quaternion._axisangle_to_q(theta, v)
        return new_quaternion

    @staticmethod
    def from_value(value):
        """Create quaternion from vector"""
        new_quaternion = _Quaternion()
        new_quaternion.val = value
        return new_quaternion

    def _axisangle_to_q(self, theta, v):
        """Convert axis and angle to quaternion"""
        x = v[0]
        y = v[1]
        z = v[2]

        w = cos(theta / 2.0)
        x = x * sin(theta / 2.0)
        y = y * sin(theta / 2.0)
        z = z * sin(theta / 2.0)

        self.val = np.array([w, x, y, z])

    def __mul__(self, b):
        """Multiplication of quaternion with quaternion or vector"""

        if isinstance(b, _Quaternion):
            return self._multiply_with_quaternion(b)
        elif isinstance(b, (list, tuple, np.ndarray)):
            if len(b) != 3:
                raise Exception(f"Input vector has invalid length {len(b)}")
            return self._multiply_with_vector(b)
        else:
            raise Exception(f"Multiplication with unknown type {type(b)}")

    def _multiply_with_quaternion(self, q_2):
        """Multiplication of quaternion with quaternion"""
        w_1, x_1, y_1, z_1 = self.val
        w_2, x_2, y_2, z_2 = q_2.val
        w = w_1 * w_2 - x_1 * x_2 - y_1 * y_2 - z_1 * z_2
        x = w_1 * x_2 + x_1 * w_2 + y_1 * z_2 - z_1 * y_2
        y = w_1 * y_2 + y_1 * w_2 + z_1 * x_2 - x_1 * z_2
        z = w_1 * z_2 + z_1 * w_2 + x_1 * y_2 - y_1 * x_2

        result = _Quaternion.from_value(np.array((w, x, y, z)))
        return result

    def _multiply_with_vector(self, v):
        """Multiplication of quaternion with vector"""
        q_2 = _Quaternion.from_value(np.append(0.0, v))
        return (self * q_2 * self.get_conjugate()).val[1:]

    def get_conjugate(self):
        """Conjugation of quaternion"""
        w, x, y, z = self.val
        result = _Quaternion.from_value(np.array((w, -x, -y, -z)))
        return result

    def __repr__(self):
        theta, v = self.get_axisangle()
        return f"(({theta}; {v[0]}, {v[1]}, {v[2]}))"

    def get_axisangle(self):
        """Returns angle and vector of quaternion"""
        w, v = self.val[0], self.val[1:]
        theta = acos(w) * 2.0

        return theta, _normalize(v)

    def tolist(self):
        """Converts quaternion to a list"""
        return self.val.tolist()

    def vector_norm(self):
        """Calculates norm of quaternion"""
        _, v = self.get_axisangle()
        return np.linalg.norm(v)

def visualize_transition(circuitjson, trace=False, saveas=None, fpg=100, spg=2):
    """
    Creates animation showing transitions between states of a single
    qubit by applying quantum gates.

    Args:
        circuitjson (dict): Qiskit single-qubit QuantumCircuit. Gates supported are
            h,x, y, z, rx, ry, rz, s, sdg, t, tdg.
        trace (bool): Controls whether to display tracing vectors - history of 10 past vectors
            at each step of the animation.
        saveas (str): User can choose to save the animation as a video to their filesystem.
            This argument is a string of path with filename and extension (e.g. "movie.mp4" to
            save the video in current working directory).
        fpg (int): Frames per gate. Finer control over animation smoothness and computational
            needs to render the animation. Works well for tkinter GUI as it is, for jupyter GUI
            it might be preferable to choose fpg between 5-30.
        spg (float): Seconds per gate. How many seconds should animation of individual gate
            transitions take.

    Returns:
        IPython.core.display.HTML:
            If arg jupyter is set to True. Otherwise opens tkinter GUI and returns
            after the GUI is closed.

    Raises:
        MissingOptionalLibraryError: Must have Matplotlib (and/or IPython) installed.
        VisualizationError: Given gate(s) are not supported.

    """

    from matplotlib import pyplot as plt
    from matplotlib import animation
    from qiskit.visualization.bloch import Bloch
    from qiskit.visualization.exceptions import VisualizationError


    frames_per_gate = fpg
    time_between_frames = (spg * 1000) / fpg

    # quaternions of gates which don't take parameters
    gates = {"empty": ("x", _Quaternion.from_axisangle(0 / frames_per_gate, [1, 0, 0]), "#1abc9c"),
        "x": ("x", _Quaternion.from_axisangle(np.pi / frames_per_gate, [1, 0, 0]), "#1abc9c"),
             "y": ("y", _Quaternion.from_axisangle(np.pi / frames_per_gate, [0, 1, 0]), "#2ecc71"),
             "z": ("z", _Quaternion.from_axisangle(np.pi / frames_per_gate, [0, 0, 1]), "#3498db"), "s": (
            "s",
            _Quaternion.from_axisangle(np.pi / 2 / frames_per_gate, [0, 0, 1]),
            "#9b59b6",
        ), "sdg": (
            "sdg",
            _Quaternion.from_axisangle(-np.pi / 2 / frames_per_gate, [0, 0, 1]),
            "#8e44ad",
        ), "h": (
            "h",
            _Quaternion.from_axisangle(np.pi / frames_per_gate, _normalize([1, 0, 1])),
            "#34495e",
        ), "t": (
            "t",
            _Quaternion.from_axisangle(np.pi / 4 / frames_per_gate, [0, 0, 1]),
            "#e74c3c",
        ), "tdg": (
            "tdg",
            _Quaternion.from_axisangle(-np.pi / 4 / frames_per_gate, [0, 0, 1]),
            "#c0392b",
        )}

    implemented_gates = ["h", "x", "y", "z", "rx", "ry", "rz", "s", "sdg", "t", "tdg", "empty"]
    simple_gates = ["h", "x", "y", "z", "s", "sdg", "t", "tdg", "empty"]
    list_of_circuit_gates = []

    for row in circuitjson["rows"]:
        temprow = []
        for gate in row["gates"]:
            if gate["type"] not in implemented_gates:
                raise VisualizationError(f"Gate {gate['type']} is not supported")

            if gate["type"] in simple_gates:
                temprow.append(gates[gate["type"]])

            else:
                theta = radians(gate["params"][0])
                if gate["type"] == "rx":
                    quaternion = _Quaternion.from_axisangle(theta / frames_per_gate, [1, 0, 0])
                    temprow.append(("rx:" + str(round(degrees(theta))), quaternion, "#16a085"))
                elif gate["type"] == "ry":
                    quaternion = _Quaternion.from_axisangle(theta / frames_per_gate, [0, 1, 0])
                    temprow.append(("ry:" + str(round(degrees(theta))), quaternion, "#27ae60"))
                elif gate["type"] == "rz":
                    quaternion = _Quaternion.from_axisangle(theta / frames_per_gate, [0, 0, 1])
                    temprow.append(("rz:" + str(round(degrees(theta))), quaternion, "#2980b9"))

        list_of_circuit_gates.append(temprow)

    if len(list_of_circuit_gates) == 0 or len(list_of_circuit_gates[0]) == 0:
        raise VisualizationError("Nothing to visualize.")

    starting_pos = _normalize(np.array([0, 0, 1]))

    fig = plt.figure()
    nrows = len(circuitjson["rows"])

    class Namespace:
        """Helper class serving as scope container"""

        def __init__(self):
            self.new_vec = []
            self.last_gate = -2
            self.colors = []
            self.pnts = []

    axlist = []
    spherelist = []
    namespacelist = []
    for j in range(0, nrows):
        ax = fig.add_subplot(1, nrows, j+1, projection='3d')
        ax.set_xlim(-10, 10)
        ax.set_ylim(-10, 10)
        axlist.append(ax)
        spherelist.append(Bloch(axes=ax))
        namespace = Namespace()
        namespace.new_vec = starting_pos
        namespacelist.append(namespace)


    def animate(i):
        for k in range(0, nrows):
            #print(k, list_of_circuit_gates, list_of_circuit_gates[k])
            spherelist[k].clear()

            # starting gate count from -1 which is the initial vector
            gate_counter = (i - 1) // frames_per_gate
            if gate_counter != namespacelist[k].last_gate:
                namespacelist[k].pnts.append([[], [], []])
                namespacelist[k].colors.append(list_of_circuit_gates[k][gate_counter][2])

            # starts with default vector [0,0,1]
            if i == 0:
                spherelist[k].add_vectors(namespacelist[k].new_vec)
                namespacelist[k].pnts[0][0].append(namespacelist[k].new_vec[0])
                namespacelist[k].pnts[0][1].append(namespacelist[k].new_vec[1])
                namespacelist[k].pnts[0][2].append(namespacelist[k].new_vec[2])
                namespacelist[k].colors[0] = "r"
                spherelist[k].make_sphere()

            else:
                namespacelist[k].new_vec = list_of_circuit_gates[k][gate_counter][1] * namespacelist[k].new_vec

                namespacelist[k].pnts[gate_counter + 1][0].append(namespacelist[k].new_vec[0])
                namespacelist[k].pnts[gate_counter + 1][1].append(namespacelist[k].new_vec[1])
                namespacelist[k].pnts[gate_counter + 1][2].append(namespacelist[k].new_vec[2])

                spherelist[k].add_vectors(namespacelist[k].new_vec)
                if trace:
                    # sphere.add_vectors(namespace.points)
                    for point_set in namespacelist[k].pnts:
                        spherelist[k].add_points([point_set[0], point_set[1], point_set[2]])

                spherelist[k].vector_color = [list_of_circuit_gates[k][gate_counter][2]]
                spherelist[k].point_color = namespacelist[k].colors
                spherelist[k].point_marker = "o"

                annotation_text = list_of_circuit_gates[k][gate_counter][0]
                annotationvector = [1.4, -0.45, 1.7]
                spherelist[k].add_annotation(
                    annotationvector,
                    annotation_text,
                    color=list_of_circuit_gates[k][gate_counter][2],
                    fontsize=30,
                    horizontalalignment="left",
                )

                spherelist[k].make_sphere()

                namespacelist[k].last_gate = gate_counter
        return axlist

    def init():
        for k in range(0, nrows):
            spherelist[k].vector_color = ["r"]
        return axlist

    ani = animation.FuncAnimation(
        fig,
        animate,
        frames_per_gate * len(list_of_circuit_gates[0]) + 1,
        init_func=init,
        blit=False,
        repeat=False,
        interval=time_between_frames,
    )

    if saveas:
        ani.save(saveas, fps=30)

    plt.show()
    plt.close(fig)
    return None
