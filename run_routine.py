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
    help='The index of the leg to run the routine on (or a tuple for multiple).'
)
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
    help='Routine file containing the routine to run (or a tuple of files for '
    + 'multiple).')
parser.add_argument(
    '-s',
    '--shift',
    type=str,
    default='0',
    help='The shift, in seconds, to be applied to the routine (or a tuple of ' +
    'shifts, to be applied to the respective routines).')

args = parser.parse_args(sys.argv[1:])

index_parsed = lib.util.evaluate_arithmetic(args.index)
shift_parsed = lib.util.evaluate_arithmetic(args.shift)
routine_parsed = lib.util.evaluate_arithmetic(args.routine)

leg_indices = []
shifts = []
routines = []

if isinstance(index_parsed, tuple):
    leg_indices = list(index_parsed)
elif isinstance(index_parsed, int):
    leg_indices.append(index_parsed)
    if isinstance(routine_parsed, tuple) or isinstance(shift_parsed, tuple):
        raise Exception('one leg cannot be driven by multiple routines')
else:
    raise Exception('index must be a single integer, or a tuple of integers')

if isinstance(routine_parsed, tuple):
    assert len(routine_parsed) == len(index_parsed), (
        'when driving multiple legs, the number of routines must be ' +
        'either 0 or equal to the number of legs')
    routines = [lib.motion.read_routine(routine) for routine in routine_parsed]
elif isinstance(routine_parsed, str):
    routines = [lib.motion.read_routine(routine_parsed)] * len(index_parsed)
else:
    raise Exception('routine must be a single path, or a tuple of paths')

if isinstance(shift_parsed, tuple):
    assert len(shift_parsed) == len(index_parsed), (
        'when driving multiple legs, the number of shifts must be ' +
        'either 0 or equal to the number of legs')
    shifts = list(shift_parsed)
elif isinstance(shift_parsed, str):
    shifts = [shift_parsed] * len(index_parsed)
else:
    raise Exception('shift must be a single shift, or a tuple of shifts')

mcs = [hexapod.motion_controllers[i] for i in leg_indices]
legs = [hexapod.legs[i] for i in leg_indices]

command_spoolers = [
    lib.util.ControlLoopSpooler(lib.motion.rotate_t(routine, shift), mc.nq)
    for routine, shift, mc in zip(routines, shifts, mcs)
]

refill_tasks = [
    lib.util.make_refill_task(command_spooler, mc, 100)
    for command_spooler, mc in zip(command_spoolers, mcs)
]

multiplier = args.multiplier


def scaled_motion_plan_task(t, dt):
    for mc in mcs:
        mc.update(multiplier * dt)


for leg in legs:
    leg.enable = True
lib.util.looper(
    lib.util.round_robin_dispatcher(
        *(refill_tasks + [scaled_motion_plan_task])), args.time)
for leg in legs:
    leg.enable = False
