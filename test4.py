import test
import os
import util
from math import pi
import math
from scipy.interpolate import LinearNDInterpolator
import pickle
import motion

mcs = test.motion_controllers
legs = test.legs
interp = 0

if os.path.exists('lut_hr2_interp.dat'):
    print "Loading interpolator from file..."
    with open('lut_hr2_interp.dat', 'r') as interpfile:
        interp = pickle.loads(interpfile.read())
    print "Interpolator loaded."
else:
    print "Initializing leg LUT..."
    with open('lut_hr2.dat', 'r') as lutfile:
        d = pickle.loads(lutfile.read())
        interp = LinearNDInterpolator(d['points'], d['pointdata'])
        with open('lut_hr2_interp.dat', 'w') as interpfile:
            interpfile.write(pickle.dumps(interp))
    print "Leg LUT initialized."

#leg_routine = [((120, -40, 100), 0.6),
#               ((80, 40, 100), 0.2),
#               ((80, 40, 40), 0.2),
#               ((120, -40, 40), 0.2)]

leg_routine = [((90, -40, 150), 0.4),
               ((90,  40, 150), 0.4),
               ((10,  40, 150), 0.4),
               ((10, -40, 150), 0.4)]


def get_leg_angles(leg_ee):
    return tuple(x for x in interp(*leg_ee))


leg_routine_subdivided = motion.subdivide_routine(leg_routine, 0.05)
polar_leg_routine = motion.transform_routine(leg_routine_subdivided,
                                             get_leg_angles)

command_looper = util.ControlLoopSpooler(
    polar_leg_routine, lambda c, t: mcs[0].nq(c, t))

legs[0].enable = True
legpos = (0, 0, 0)
legs[0].move(*legpos)
mcs[0].nq(legpos, 0)

command_looper.spool(10)


def refill_task(t, dt):
    while mcs[0].depth() < 10:
        command_looper.spool(10)


def motion_plan_task(t, dt):
    mcs[0].update(dt)


def execute():
    util.looper(util.round_robin_dispatcher(refill_task, motion_plan_task), 2.4)


interp((100, 0, 0))

print "Ready for business"
