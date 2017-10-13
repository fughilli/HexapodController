import hexapod
import lib.util
from math import pi

print "Making the hexapod into an egg..."

for leg, mc in zip(hexapod.legs, hexapod.motion_controllers):
    leg.enable = True
    mc.nq((0, 0, 0), 0)
    mc.nq((0, 0, 0), 1)
    mc.nq((0, pi / 2, pi / 4), 2)

util.looper(hexapod.motion_plan_task, 3)

for leg in test.legs:
    leg.enable = False

print "Eggification complete."
