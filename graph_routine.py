#!/usr/bin/python

from mpl_toolkits.mplot3d import Axes3D
import argparse
import math
import matplotlib.pyplot as plt
import numpy
import sys

import lib.iksolve
import lib.motion
import lib.util

parser = argparse.ArgumentParser(description='Plot a routine.')
parser.add_argument(
    '-x',
    '--xml',
    type=str,
    help='The xml specification file for the armature (input)')
parser.add_argument(
    '-c',
    '--cartesian',
    action='store_true',
    help=
    'Whether the given routine is cartesian (can be directly plotted without ' +
    'needing the armature geometry).')
parser.add_argument(
    '-r',
    '--routine',
    type=str,
    required=True,
    help='Routine file containing the routine to plot.')
parser.add_argument(
    '-o',
    '--output',
    type=str,
    help=
    'Image file to write the plot to. No interactive plot will be opened if ' +
    'this argument is provided.')

args = parser.parse_args(sys.argv[1:])

routine = lib.motion.read_routine(args.routine)

if not args.cartesian:
    if not args.xml:
        print("You must specify an armature configuration to plot a " +
              "non-cartesian routine.")
        exit(1)
    armature = lib.iksolve.Armature.fromXml(open(args.xml, 'r').read())
    # Transform the routine into a cartesian routine.
    routine = lib.motion.transform_routine(routine, armature.forward)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

points = [x[0] for x in routine]

xs, ys, zs = zip(*points)
ax.plot(xs, ys, zs, marker='o')

limits = numpy.array([ax.get_xlim3d(), ax.get_ylim3d(), ax.get_zlim3d()])
centers = numpy.array([sum(lim) / 2 for lim in limits])
nobias_limits = numpy.array([l - c for l, c in zip(limits, centers)])
minextent, maxextent = (numpy.minimum(*nobias_limits)[0],
                        numpy.maximum(*nobias_limits)[1])
limits = zip(centers + minextent, centers + maxextent)
ax.set_xlim3d(*limits[0])
ax.set_ylim3d(*limits[1])
ax.set_zlim3d(*limits[2])

if args.output:
    fig.savefig(args.output)
else:
    plt.show()
