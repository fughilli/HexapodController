import iksolve
import util
import numpy as np
from scipy.interpolate import RegularGridInterpolator, LinearNDInterpolator
import sys
from joblib import Parallel, delayed
import pickle

pi = np.pi


def split(array, n):
    retarrays = []
    while (len(array)):
        retarrays.append(array[:n])
        array = array[n:]
    return retarrays


def save_lut(fname, data):
    with open(fname, 'w') as lutfile:
        lutfile.write(pickle.dumps({'points': data[0], 'pointdata': data[1]}))


def load_lut(fname):
    with open(fname, 'r') as lutfile:
        d = pickle.loads(lutfile.read())
        return d['points'], d['pointdata']


leg = iksolve.Armature(
    iksolve.Joint((0, 0, 1), (-pi / 3, pi / 3)),
    iksolve.Linkage((14.98, 0, 0)),
    iksolve.Joint((0, 1, 0), (-pi / 2, pi / 2)),
    iksolve.Linkage((98, 0, 0)),
    iksolve.Joint((0, 1, 0), (-3 * pi / 4, pi / 4)), iksolve.Linkage((88, 0,
                                                                      0)))

# Leg length comes from zero-angle position of end effector
leg_length = np.linalg.norm(leg.forward((0, 0, 0)))

# How finely to subdivide the linear space in each dimension
subdivisions = 12

# Linear space in 3D
x = np.linspace(0, leg_length, leg_length / subdivisions)
y = np.linspace(-leg_length, leg_length, 2 * leg_length / subdivisions)
z = np.linspace(-leg_length, leg_length, 2 * leg_length / subdivisions)

# Nx3 vector of grid points
points = np.array(np.meshgrid(x, y, z)).T.reshape(-1, 3)


# Parallel job function
def compute_inverses(ees):
    return [leg.reverse(ee) for ee in ees]


#print "Computing IK table..."
#pointdata = np.concatenate(
#    Parallel(n_jobs=-1, verbose=1)(map(
#        delayed(compute_inverses), split(points, 32))))
#
#save_lut('lut_hr2.dat', (points, pointdata))

points, pointdata = load_lut('lut_hr2.dat')

print "Initializing interpolator..."
interpolator = LinearNDInterpolator(points, pointdata)
