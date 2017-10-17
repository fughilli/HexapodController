#!/usr/bin/python

import hexapod
import lib.util
from math import pi

print "Making the hexapod into an egg..."

for leg, mc in zip(hexapod.legs, hexapod.motion_controllers):
    leg.enable = True
    mc.nq((0, 0, 0), 2)
    mc.nq((0, pi / 2, -pi), 1)
    lib.util.looper(hexapod.motion_plan_task, 2)
    leg.enable = False

print "Eggification complete."
