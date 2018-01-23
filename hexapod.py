import math
import os
import re
import smbus
import time

import lib.linkage
import lib.motion
import lib.motor
import lib.util

bus = smbus.SMBus(1)
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

with open('spec/leg2_mapping.dat', 'r') as config_file:
    for line in config_file.readlines():
        bus_address, motor_idx, leg_idx, leg_segment = [
            t(s)
            for t, s in zip((
                int,) * 4, re.match('(\d+)-(\d+):(\d+)-(\d+)', line).groups())
        ]
        leg_params[leg_idx][leg_segment] = (bus_address, motor_idx)

legs = [
    lib.linkage.Linkage(
        [
            filter(lambda x: x.address == addr, (mc0, mc1))[0].motors[idx]
            for addr, idx in leg_param
        ],
        limits=[(-math.pi / 3, math.pi / 3), (-math.pi / 2, math.pi / 2),
                (-math.pi, 0)]) for leg_param in leg_params
]

for i, leg in enumerate(legs):
    calfilename = 'cal/leg2_%d_cal.dat' % (i,)
    if os.path.exists(calfilename):
        print "Loaded calibration for leg %d from %s" % (i, calfilename)
        leg.load_calibration(calfilename)
    leg.move((0, 0, 0))


def calibrate_legs(indices=range(6)):
    for i, leg in enumerate(legs):
        if not i in indices:
            continue
        calfilename = 'cal/leg2_%d_cal.dat' % (i,)
        print "Calibrating leg %d; saving config to %s" % (i, calfilename)
        leg.calibrate()
        leg.save_calibration(calfilename)


motion_controllers = [lib.motion.MotionController(leg.move) for leg in legs]


def motion_plan_task(t, dt):
    for motion_controller in motion_controllers:
        motion_controller.update(dt)


def run_routine(routinefname, leg_idx, t):
    routine = lib.motion.read_routine(routinefname)
    routine_spooler = lib.util.ControlLoopSpooler(
        routine, lambda c, dt: motion_controllers[leg_idx].nq(c, dt))

    def spool_task(t, dt):
        if motion_controllers[leg_idx].depth() < 10:
            routine_spooler.spool(10)

    legs[leg_idx].enable = True
    lib.util.looper(
        lib.util.round_robin_dispatcher(
            spool_task, (lambda t, dt: motion_controllers[leg_idx].update(dt))),
        t)
    legs[leg_idx].enable = False
