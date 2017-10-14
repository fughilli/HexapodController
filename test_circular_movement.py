#!/usr/bin/python

import argparse
import math
import numpy
import sys

import lib.iksolve
import lib.motion
import lib.util

parser = argparse.ArgumentParser(
    description='Move an armature in a planar circular motion.')
parser.add_argument(
    '-l',
    '--lut',
    type=str,
    required=True,
    help='The lookup table file for the armature')
parser.add_argument(
    '-x',
    '--xml',
    type=str,
    required=True,
    help='The xml specification file for the armature')
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
parser.add_argument(
    '-o', '--output', type=str, help='The output file to write the routine to')

args = parser.parse_args(sys.argv[1:])

points, pointdata = lib.util.load_lut(args.lut)
interp = lib.util.make_interpolator_from_lut(points, pointdata)


def get_angles(ee):
    return tuple(x for x in interp(*ee))


p0 = lib.util.evaluate_arithmetic(args.center)

routine = lib.motion.planar_ellipse_routine(p0[0], p0[1], p0[2], args.radius,
                                            args.radius, args.subdivisions,
                                            args.time / args.subdivisions)

routine_subdivided = lib.motion.subdivide_routine(
    routine, args.time / args.subdivisions / 2)
polar_routine = lib.motion.transform_routine(routine_subdivided, get_angles)

if lib.motion.check_routine(polar_routine):
    print "Given path will succeed."
else:
    print "Given path will fail."

if args.output:
    print "Exporting routine to %s" % (args.output,)
    lib.motion.write_routine(args.output, polar_routine)
