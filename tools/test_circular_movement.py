#!/usr/bin/python

import argparse
import math
import motion
import numpy
import sys
import util
import iksolve

parser = argparse.ArgumentParser(
    description='Move an armature in a planar circular motion.')
parser.add_argument(
    '-l', '--lut', type=str, help='The lookup table file for the armature')
parser.add_argument(
    '-x', '--xml', type=str, help='The xml specification file for the armature')
parser.add_argument(
    '-c',
    '--center',
    type=str,
    default='(0,0,0)',
    help='A tuple of (x,y,z) around which the circle will be performed')
parser.add_argument(
    '-r', '--radius', type=float, default=10.0, help='The radius of the circle')
parser.add_argument(
    '-t',
    '--time',
    type=float,
    default=2.0,
    help='The time in which to complete the circle')
parser.add_argument(
    '-s',
    '--subdivisions',
    type=int,
    default=32,
    help='The number of segments to generate for the circular path')


args = parser.parse_args(sys.argv[1:])

points, pointdata = util.load_lut(args.lut)
interp = util.make_interpolator_from_lut(points, pointdata)

def get_angles(ee):
    return tuple(x for x in interp(*ee))

p0 = util.evaluate_arithmetic(args.center)

routine = motion.planar_ellipse_routine(p0[0], p0[1], p0[2], args.radius,
                                            args.radius, args.subdivisions,
                                            args.time / args.subdivisions)

routine_subdivided = motion.subdivide_routine(
    routine, args.time / args.subdivisions / 2)
polar_routine = motion.transform_routine(routine_subdivided, get_angles)

if motion.check_routine(polar_routine):
    print "Given path will succeed."
else:
    print "Given path will fail."
