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
    type=str,
    required=True,
    help='The index of the leg to run the routine on (or a tuple for multiple).')
parser.add_argument(
    '-m',
    '--multiplier',
    type=float,
    default=1.0,
    help='The speed multiplier to run the routine at.')
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
    help='Routine file containing the routine to run (or a tuple of files for multiple).')

args = parser.parse_args(sys.argv[1:])

routine = lib.motion.read_routine(args.routine)

index_parsed = lib.util.evaluate_arithmetic(args.index)

leg_indices = []

if isinstance(index_parsed, tuple):
    leg_indices = list(index_parsed)
elif isinstance(index_parsed, int):
    leg_indices.append(index_parsed)
else:
    raise Exception('index must be a single integer, or a tuple of integers')

mcs = [hexapod.motion_controllers[i] for i in leg_indices]
legs = [hexapod.legs[i] for i in leg_indices]

command_spoolers = [lib.util.ControlLoopSpooler(routine, mc.nq) for mc in mcs]

refill_tasks = [lib.util.make_refill_task(command_spooler, mc, 100) for command_spooler,mc in zip(command_spoolers,mcs)]

multiplier = args.multiplier

def scaled_motion_plan_task(t, dt):
    for mc in mcs:
        mc.update(multiplier * dt)

for leg in legs:
    leg.enable = True
lib.util.looper(
    lib.util.round_robin_dispatcher(*(refill_tasks + [scaled_motion_plan_task, hexapod.battery_check_task])),
    args.time)
for leg in legs:
    leg.enable = False
