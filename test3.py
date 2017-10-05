import test
import util
from math import pi

for leg,mc in zip(test.legs, test.motion_controllers):
    leg.enable = True
    mc.nq((0,0,0), 0)
    mc.nq((0,0,0), 1)
    mc.nq((0, pi/2, pi/4), 2)

util.looper(test.motion_plan_task, 3)

for leg in test.legs:
    leg.enable = False
