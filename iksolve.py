import math
import numpy
import scipy.optimize

pi = math.pi


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


class Armature(object):

    def __init__(self, *parts):
        self.parts = parts
        self.joints = [x for x in self.parts if isinstance(x, Joint)]

    def forward(self, angles):
        for x, angle in zip(self.joints, angles):
            x._angle = angle
        result = reduce(lambda a, b: a.dot(b), (
            part.matrix
            for part in self.parts)).dot(numpy.array([0, 0, 0, 1]).T)
        return result[:3]

    def reverse(self, target=None):
        target = numpy.asarray(target)

        minreport = scipy.optimize.minimize(
            fun=(lambda angles: numpy.linalg.norm(target - self.forward(angles))
                ),
            x0=self.centers,
            bounds=self.limits,
            method='L-BFGS-B')

        if numpy.linalg.norm(self.forward(minreport.x) - target) < 1e-6:
            return minreport.x
        return numpy.array([numpy.nan] * len(minreport.x))

    @property
    def angles(self):
        return [x.angle for x in self.joints]

    @angles.setter
    def angles(self, _angles):
        for x, angle in zip(self.joints, _angles):
            x.angle = angle

    @property
    def limits(self):
        return [x.limits for x in self.joints]

    @property
    def centers(self):
        return [x._limits.center for x in self.joints]


class Limits(object):

    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper

    @property
    def center(self):
        return (self.lower + self.upper) / 2

    def check(self, value):
        return value >= self.lower and value <= self.upper

    def __repr__(self):
        return "[%f:%f]" % (self.lower, self.upper)

    def asTuple(self):
        return (self.lower, self.upper)


class Joint(object):

    def __init__(self, axis, limits):
        self._limits = Limits(*limits)
        self.axis = axis
        self._angle = self._limits.center

    @property
    def limits(self):
        return self._limits.asTuple()

    @limits.setter
    def limits(self, _limits):
        self._limits = Limits(*_limits)
        if not self._limits.check(self._angle):
            raise ValueError("Joint angle %f is outside of new limits %s" %
                             (self._angle, self._limits))
            self._angle = self._limits.center

    @property
    def matrix(self):
        return rotation_matrix(self.axis, self.angle)

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, _angle):
        if not self._limits.check(_angle):
            raise ValueError("Angle %f is out of range %s" % (_angle,
                                                              self._limits))
        self._angle = _angle

    def check(self):
        return self._limits.check(self.angle)


class Linkage(object):

    def __init__(self, axis):
        self.axis = axis

    @property
    def matrix(self):
        return numpy.array([[1, 0, 0, self.axis[0]], [0, 1, 0, self.axis[1]],
                            [0, 0, 1, self.axis[2]], [0, 0, 0, 1]])
