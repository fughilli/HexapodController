#!/usr/bin/python

import argparse
import math
import numpy
import smbus
import sys

import lib.iksolve
import lib.motion
import lib.motor
import lib.util

parser = argparse.ArgumentParser(
    description='Determine the motor pin assignments on the robot.')
parser.add_argument(
    '-n',
    '--numarmatures',
    type=int,
    required=True,
    help='The number of armatures on the robot.')
parser.add_argument(
    '-x',
    '--xml',
    type=str,
    help='The xml specification file for the armatures.')
parser.add_argument(
    '-b',
    '--smbus',
    type=int,
    default=0,
    help='The index of the smbus to open.')
parser.add_argument(
    '-c',
    '--numchannels',
    type=int,
    default=9,
    help='The number of channels on the servo controllers.')
parser.add_argument(
    '-a',
    '--address',
    type=str,
    default='(0x40,0x42)',
    help='A tuple of I2C addresses for the motor controllers.')
parser.add_argument(
    '-s',
    '--spec',
    type=str,
    required=True,
    help='The assignment spec file to save the assignments to.')


def readtype(t):
    val = None
    while True:
        try:
            val = t(sys.stdin.readline().strip())
            break
        except:
            print 'Value cannot be interpreted as %s' % (t,)
    return val


def readyn(default='y'):
    while True:
        line = sys.stdin.readline().strip()
        if line == '':
            line = default
        if line.lower() in ('yes', 'y', 'ye'):
            return True
        elif line.lower() in ('no', 'n'):
            return False
        else:
            sys.stdout.write('Please enter "y(es)" or "n(o)" (default=%s): ' %
                             (default,))


args = parser.parse_args(sys.argv[1:])

# Figure out the armature geometry
armature = lib.iksolve.Armature.fromXml(open(args.xml).read())
numjoints = len(armature.joints)

bus = smbus.SMBus(args.smbus)
addresses = lib.util.evaluate_arithmetic(args.address)
mcs = [
    lib.motor.MotorController(bus, address, args.numchannels)
    for address in addresses
]

motors = reduce(lambda a, b: a + b, (mc.motors for mc in mcs))

outbuf = ''

print 'Starting assignment determination...'

for i, motor in enumerate(motors):
    sys.stdout.write('Press ENTER when ready')
    sys.stdin.readline()
    while True:
        print 'Twitching motor %d (%d on controller at %s)...' % (
            i, motor.index, hex(motor.mc.address))
        motor.twitch()
        sys.stdout.write('Repeat twitch? (y/N): ')
        if readyn(default='n'):
            break
    sys.stdout.write('Which armature was that (0-%d): ' %
                     (args.numchannels - 1,))
    armature_idx = readtype(int)
    sys.stdout.write('Which joint on the armature was that (0-%d): ' %
                     (numjoints - 1,))
    joint_idx = readtype(int)
    outbuf += ('%d-%d:%d-%d' % (motor.mc.address, motor.index, armature_idx,
                                joint_idx))
