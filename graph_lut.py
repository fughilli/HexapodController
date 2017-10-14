#!/usr/bin/python

from mpl_toolkits.mplot3d import Axes3D
import argparse
import math
import matplotlib.pyplot as plt
import numpy
import sys

import lib.util

parser = argparse.ArgumentParser(
    description='Plot the envelope of a kinematic chain from its lookup table.')
parser.add_argument(
    '-l', '--lut', type=str, help='The lookup table file to plot')
parser.add_argument(
    '-o',
    '--output',
    type=str,
    help=
    'Image file to write the plot to. No interactive plot will be opened if ' +
    'this argument is provided.')

args = parser.parse_args(sys.argv[1:])

points, pointdata = lib.util.load_lut(args.lut)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

good_points = [
    point for point, data in zip(points, pointdata) if not numpy.isnan(data[0])
]

ax.scatter(*zip(*good_points))

if args.output:
    fig.savefig(args.output)
else:
    plt.show()
