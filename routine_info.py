#!/usr/bin/python

import argparse
import math
import numpy
import sys

import lib.motion
import lib.util

parser = argparse.ArgumentParser(description='Print info about a routine.')
parser.add_argument(
    '-r',
    '--routine',
    type=str,
    required=True,
    help='Routine file containing the routine to get info about.')

args = parser.parse_args(sys.argv[1:])

routine = lib.motion.read_routine(args.routine)

print "Routine info:"
print "control points:", len(routine)
print "total time:", lib.motion.routine_time(routine)
print "average subdivision:", numpy.average([t for c,t in routine])
