import math
import numpy
import scipy.optimize
import util
import xml.etree.ElementTree as ETree

pi = math.pi


class Armature(object):

    def __init__(self, *parts):
        self.parts = parts
        self.joints = [x for x in self.parts if isinstance(x, Joint)]
        self.linkages = [x for x in self.parts if isinstance(x, Linkage)]

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

        if numpy.linalg.norm(self.forward(minreport.x) - target) < 1e-5:
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

    @property
    def maxlength(self):
        return sum(numpy.linalg.norm(l.axis) for l in self.linkages)

    def xmlElement(self):
        element = ETree.Element('armature')
        for part in self.parts:
            element.append(part.xmlElement())
        element.tail = element.text = '\n'
        return element

    def asXml(self):
        return ETree.tostring(self.xmlElement())

    @classmethod
    def fromXml(self, xml):
        parts = []
        root = ETree.fromstring(xml)
        if root.tag == 'armature':
            for elem in root.getchildren():
                if elem.tag == 'joint':
                    if 'limits' in elem.attrib.keys():
                        limits = util.evaluate_arithmetic(elem.attrib['limits'])
                    if 'dlimits' in elem.attrib.keys():
                        limits = [
                            math.radians(x)
                            for x in util.evaluate_arithmetic(
                                elem.attrib['dlimits'])
                        ]

                    parts.append(
                        Joint(
                            axis=util.evaluate_arithmetic(elem.attrib['axis']),
                            limits=limits))
                if elem.tag == 'linkage':
                    parts.append(
                        Linkage(axis=util.evaluate_arithmetic(
                            elem.attrib['axis'])))
            return Armature(*parts)
        raise Exception('xml root does not have tag "armature"')


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
        return util.rotation_matrix(self.axis, self.angle)

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

    def xmlElement(self):
        element = ETree.Element('joint')
        element.attrib['axis'] = str(self.axis)
        element.attrib['limits'] = str(self.limits)
        element.tail = '\n'
        return element


class Linkage(object):

    def __init__(self, axis):
        self.axis = axis

    @property
    def matrix(self):
        return numpy.array([[1, 0, 0, self.axis[0]], [0, 1, 0, self.axis[1]],
                            [0, 0, 1, self.axis[2]], [0, 0, 0, 1]])

    def xmlElement(self):
        element = ETree.Element('linkage')
        element.attrib['axis'] = str(self.axis)
        element.tail = '\n'
        return element
