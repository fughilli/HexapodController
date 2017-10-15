from scipy.interpolate import LinearNDInterpolator
import ast
import math
import numpy
import operator as op
import pickle
import time


def clamp(val, low, high):
    return min((max((val, low)), high))


def map(val, ilow, ihigh, olow, ohigh):
    return olow + (ohigh - olow) * (val - ilow) / (ihigh - ilow)


def lerp(a, b, t):
    t = float(t)
    return b * t + a * (1 - t)


def lerp_tuple(at, bt, t):
    t = float(t)
    return tuple(be * t + ae * (1 - t) for ae, be in zip(at, bt))


def looper(function, total_time):
    start_time = time.time()
    last_time = start_time
    while (True):
        current_time = time.time()
        function(current_time - start_time, current_time - last_time)
        last_time = current_time
        if (current_time - start_time >= total_time):
            break


def round_robin_dispatcher(*loop_functions):

    def _dispatch(t, dt):
        for loop_function in loop_functions:
            loop_function(t, dt)

    return _dispatch


def delay_task(delay):

    def _dispatch(t, dt):
        time.sleep(delay)

    return _dispatch


class PeriodicTimer(object):

    def __init__(self, period):
        self.period = period
        self.count = 0

    def tick(self, dt=1):
        self.count += dt
        if self.count >= self.period:
            self.count = 0
            return True
        return False


def rotate(l, n):
    n = n % len(l)
    return l[n:] + l[:n]


class ControlLoopSpooler(object):

    def __init__(self, commands, command_func):
        self.command_func = command_func
        self.commands = commands
        self.command_idx = 0

    def spool(self, n=1):
        if len(self.commands):
            for _ in range(n):
                self.command_func(*self.commands[self.command_idx])
                self.command_idx = (self.command_idx + 1) % len(self.commands)


def load_interpolator(interp_file_name):
    return pickle.loads(open(interp_file_name, 'r').read())


def save_interpolator(interp_file_name, interpolator):
    open(interp_file_name, 'w').write(pickle.dumps(interpolator))


def load_lut(lut_file_name):
    with open(lut_file_name, 'r') as lutfile:
        d = pickle.loads(lutfile.read())
        return (d['points'], d['pointdata'])


def save_lut(lut_file_name, points, pointdata):
    with open(lut_file_name, 'w') as lutfile:
        lutfile.write(pickle.dumps({'points': points, 'pointdata': pointdata}))


def load_interpolator_from_lut(lut_file_name):
    interp = LinearNDInterpolator(*load_lut(lut_file_name))
    return interp


def make_interpolator_from_lut(points, pointdata):
    return LinearNDInterpolator(points, pointdata)


def split(array, n):
    retarrays = []
    while (len(array)):
        retarrays.append(array[:n])
        array = array[n:]
    return retarrays


def _eval(node):
    operators = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Pow: op.pow,
        ast.USub: op.neg
    }
    if isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.Name):
        return {'pi': numpy.pi, 'sqrt': numpy.sqrt}[node.id]
    elif isinstance(node, ast.Tuple):
        return tuple(_eval(x) for x in node.elts)
    elif isinstance(node, ast.BinOp):
        return operators[type(node.op)](_eval(node.left), _eval(node.right))
    elif isinstance(node, ast.UnaryOp):
        return operators[type(node.op)](_eval(node.operand))
    elif isinstance(node, ast.Call):
        return _eval(node.func)(*(_eval(arg) for arg in node.args))
    raise TypeError(node)


def evaluate_arithmetic(expr):
    expr_ast = ast.parse(expr, mode='eval').body
    return _eval(expr_ast)


def rotation_matrix(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
    axis = numpy.asarray(axis)
    axis = axis / math.sqrt(numpy.dot(axis, axis))
    a = math.cos(theta / 2.0)
    b, c, d = -axis * math.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    return numpy.array([[aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac), 0], [
        2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab), 0
    ], [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc, 0], [0, 0, 0, 1]])


def translation_matrix(vec):
    """
    Return the translation matrix given by the positional delta, vec.
    """
    return numpy.array([[1, 0, 0, vec[0]], [0, 1, 0, vec[1]], [0, 0, 1, vec[2]],
                        [0, 0, 0, 1]])
