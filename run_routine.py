#!/usr/bin/python

import argparse
import math
import numpy
import sys

import hexapod
import lib.motion
import lib.util

parser = argparse.ArgumentParser(
    description='Execute a given routine on the robot.')
parser.add_argument(
    '-i',
    '--index',
    type=int,
    required=True,
    help='The index of the leg to run the routine on.')
parser.add_argument(
    '-t',
    '--time',
    type=float,
    default=1.0,
    help='The amount of time to run the routine for.')
parser.add_argument(
    '-r',
    '--routine',
    type=str,
    required=True,
    help='Routine file containing the routine to run.')

args = parser.parse_args(sys.argv[1:])

routine = lib.motion.read_routine(args.routine)

mc = hexapod.motion_controllers[args.index]
leg = hexapod.legs[args.index]

command_spooler = lib.util.ControlLoopSpooler(routine, mc.nq)

refill_task = lib.util.make_refill_task(command_spooler, mc, 100)

leg.enable = True
lib.util.looper(
    lib.util.round_robin_dispatcher(refill_task, hexapod.motion_plan_task),
    args.time)
leg.enable = False
