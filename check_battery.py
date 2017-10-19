#!/usr/bin/python

import smbus

import lib.motor

bus = smbus.SMBus(0)
mc0 = lib.motor.MotorController(bus, 0x40, 9)
mc1 = lib.motor.MotorController(bus, 0x42, 9)

print "Battery is at %fV" % (mc0.battery,)
