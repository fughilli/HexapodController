import tinyik
import util
import numpy as np
from scipy.interpolate import RegularGridInterpolator,LinearNDInterpolator
import sys
from joblib import Parallel, delayed
import pickle



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

step_size = 10

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

def out_of_range(angles):
    if angles[0] > np.pi/3 or angles[0] < -np.pi/3:
        return True
    if angles[1] > np.pi/2 or angles[0] < -np.pi/2:
        return True
    if angles[2] > np.pi/4 or angles[0] < -3*np.pi/4:
        return True
    return False


def compute_inverses(ees):
    leg = tinyik.Actuator(['z', [14.98,0,0], 'y', [98,0,0], 'y', [88,0,0]])
    leg.angles = [0, np.pi/4, np.pi/4]
    ret = []
    for ee in ees:
        fail_counter = 0
        leg.ee = ee
        while out_of_range(leg.angles) and fail_counter < 10:
            leg.angles = (np.random.random((3,))-0.5)*(np.pi/2)
            leg.ee = ee
            fail_counter += 1
        if fail_counter < 10:
            ret.append(leg.angles)
        else:
            ret.append(np.array([np.nan]*3))
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

def save_lut(fname, data):
    with open(fname, 'w') as lutfile:
        lutfile.write(pickle.dumps({'points': data[0], 'pointdata': data[1]}))

def load_lut(fname):
    with open(fname, 'r') as lutfile:
        d = pickle.loads(lutfile.read())
        return d['points'],d['pointdata']

save_lut('lut_hr.dat', (points, pointdata))

points,pointdata = load_lut('lut_hr.dat')

print "Initializing interpolator..."
#interpolator = RegularGridInterpolator((x,y,z),reshapeddata)
interpolator = LinearNDInterpolator(points,pointdata)
