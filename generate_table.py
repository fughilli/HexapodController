import tinyik
import util
import numpy as np
from scipy.interpolate import RegularGridInterpolator
import sys
from joblib import Parallel, delayed



def tuple_add(at, bt):
    return tuple(a + b for a, b in zip(at, bt))


class NParallelepiped(object):

    def __init__(self, axes, origin):
        '''Initializes an N-dimensional parallelepiped.

        axes: a tuple of N-dimensional vectors which determine the axes of the
              parallelepiped
        origin: an N-dimensional vector specifying the origin of the
                parallelepiped
        '''
        self.N = len(origin)
        self.axes = []
        self.naxes = []
        for axis in axes:
            assert (len(axis) == self.N)
            axis = np.array(axis)
            self.axes.append(axis)
            self.naxes.append(axis/np.linalg.norm(axis))

        self.origin = np.array(origin)

    def points(self, stepsize):
        stepsize = float(stepsize)
        qdims = [int(np.linalg.norm(axis) / stepsize) for axis in self.axes]

        ipoints = np.array(
            np.meshgrid(*[range(dim) for dim in qdims])).T.reshape(-1, self.N)

        points = []
        for ipoint in ipoints:
            point = self.origin + reduce(lambda a, b: a + b, (
                v * s for v, s in zip(self.naxes, ipoint))) * stepsize
            points.append(point)

        return qdims, ipoints, points


print "Initializing vector space..."
leg_length = 14.98+98+88
#
#pp3 = NParallelepiped([(leg_length, 0, 0), (0, leg_length * 2, 0),
#                       (0, 0, leg_length * 2)], (0, -leg_length, -leg_length))
#
#qdims, ipoints, points = pp3.points(20)A

step_size = 20

x = np.linspace(0,leg_length,leg_length/step_size)
y = np.linspace(-leg_length,leg_length,2*leg_length/step_size)
z = np.linspace(-leg_length,leg_length,2*leg_length/step_size)

points = np.array(np.meshgrid(x,y,z)).T.reshape(-1,3)

#pointdata = []
#for i,point in enumerate(points):
#    sys.stdout.write('%f%%\r' % (100 * i / len(points)))
#
#    leg.ee = point
#    pointdata.append(leg.angles)

leg = tinyik.Actuator(['z', [14.98,0,0], 'y', [98,0,0], 'y', [88,0,0]])

def compute_inverses(ees):
    leg = tinyik.Actuator(['z', [14.98,0,0], 'y', [98,0,0], 'y', [88,0,0]])
    leg.angles = [0, np.pi/4, np.pi/4]
    ret = []
    for ee in ees:
        leg.ee = ee
        ret.append(leg.angles)
    return ret

def split(array, n):
    retarrays = []
    while(len(array)):
        retarrays.append(array[:n])
        array = array[n:]
    return retarrays

print "Computing IK table..."
pointdata = np.concatenate(Parallel(n_jobs=-1, verbose=1)(
        map(delayed(compute_inverses), split(points, 32))))

reshapeddata = pointdata.reshape(20,10,20,3)

print "Initializing interpolator..."
interpolator = RegularGridInterpolator((x,y,z),reshapeddata)
