#!/usr/bin/python

from joblib import Parallel, delayed
from scipy.interpolate import LinearNDInterpolator
import argparse
import numpy
import pickle
import sys

import lib.iksolve
import lib.util

parser = argparse.ArgumentParser(
    description=
    'Generate a lookup table and/or a pickled interpolator for an armature.')
parser.add_argument(
    '-x',
    '--xml',
    type=str,
    help='The xml specification file for the armature (input)')
parser.add_argument(
    '-l',
    '--lut',
    type=str,
    help='The lookup table file for the armature (input/output)')
parser.add_argument(
    '-i',
    '--interp',
    type=str,
    help='The interpolator pickle file for the armature (output)')
parser.add_argument(
    '-s',
    '--subdivisions',
    type=int,
    default=16,
    help='How finely to subdivide the armature\'s envelope when computing the '
    + 'lookup table. Note that memory consumption will go as x**3.')

args = parser.parse_args(sys.argv[1:])

if not args.lut and not args.interp:
    print 'No output files specified. Aborting.'
    exit(1)

if not args.lut and not args.xml:
    print 'No input file specified. Aborting.'
    exit(1)

if args.xml:
    print 'Importing armature from %s' % (args.xml,)
    armature = lib.iksolve.Armature.fromXml(open(args.xml).read())

    # Armature envelope radius
    radius = armature.maxlength

    # How finely to subdivide the linear space in each dimension
    subdivisions = args.subdivisions

    # Linear space in 3D
    x = numpy.linspace(-radius, radius, 2 * subdivisions)
    y = numpy.linspace(-radius, radius, 2 * subdivisions)
    z = numpy.linspace(-radius, radius, 2 * subdivisions)

    # Nx3 vector of grid points
    points = numpy.array(numpy.meshgrid(x, y, z)).T.reshape(-1, 3)

    # Parallel job function
    def compute_inverses(ees):
        return [armature.reverse(ee) for ee in ees]

    print 'Computing IK table...'
    pointdata = numpy.concatenate(
        Parallel(n_jobs=-1, verbose=1)(map(
            delayed(compute_inverses), lib.util.split(points, 32))))

    if args.lut:
        print 'Exporting LUT to %s' % (args.lut,)
        lib.util.save_lut(args.lut, points, pointdata)
elif args.lut:
    print 'Importing LUT from %s' % (args.lut,)
    points, pointdata = lib.util.load_lut(args.lut)

if args.interp:
    print 'Exporting interpolator to %s' % (args.interp,)
    lib.util.save_interpolator(args.interp,
                               lib.util.make_interpolator_from_lut(
                                   points, pointdata))
