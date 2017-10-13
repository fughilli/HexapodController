import math
import os
import re
import smbus
import time

import linkage
import motion
import motor
import util

bus = smbus.SMBus(0)
mc0 = lib.motor.MotorController(bus, 0x40, 9)
mc1 = lib.motor.MotorController(bus, 0x42, 9)

motors = mc0.motors + mc1.motors

BATTERY_THRESHOLD = 3.6  # Volts

battery_check_timer = lib.util.PeriodicTimer(10)


def battery_check_task(t, dt):
    if battery_check_timer.tick(dt):
        battery_voltage = mc0.battery
        print("Battery level: %fV" % (battery_voltage,))
        if battery_voltage < BATTERY_THRESHOLD:
            print "Battery low! Turning off motors"
            for motor in motors:
                lib.motor.enable = False
            exit(1)


leg_params = [[0, 0, 0] for _ in range(6)]

with open('spec/leg_mapping.dat', 'r') as config_file:
    for line in config_file.readlines():
        motor_idx, leg_idx, leg_segment = [
            t(s)
            for t, s in zip((
                int,) * 3, re.match('(\d+):(\d+)-(\d+)', line).groups())
        ]
        leg_params[leg_idx][leg_segment] = motor_idx

legs = [
    lib.linkage.Linkage(
        [motors[idx] for idx in leg_param],
        limits=[(-math.pi / 3, math.pi / 3), (-math.pi / 3, math.pi / 2),
                (-math.pi * 3 / 4, math.pi / 4)]) for leg_param in leg_params
]

for i, leg in enumerate(legs):
    calfilename = 'leg_%d_cal.dat' % (i,)
    if os.path.exists(calfilename):
        print "Loaded calibration for leg %d from %s" % (i, calfilename)
        leg.load_calibration(calfilename)
    leg.move(0, 0, 0)


def calibrate_legs(indices=range(6)):
    for i, leg in enumerate(legs):
        if not i in indices:
            continue
        calfilename = 'leg_%d_cal.dat' % (i,)
        print "Calibrating leg %d; saving config to %s" % (i, calfilename)
        leg.calibrate()
        leg.save_calibration(calfilename)


lib.motion.controllers = [
    lib.motion.MotionController(lambda pos: leg.move(*pos)) for leg in legs
]


def lib.motion.plan_task(t, dt):
    for lib.motion.controller in lib.motion.controllers:
        lib.motion.controller.update(dt)
