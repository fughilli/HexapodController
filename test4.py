import test
import util
from math import pi
from scipy.interpolate import LinearNDInterpolator
import pickle
import motion

mcs = test.motion_controllers
legs = test.legs
interp = 0

with open('lut_hr.dat', 'r') as lutfile:
    d = pickle.loads(lutfile.read())
    interp = LinearNDInterpolator(d['points'], d['pointdata'])

leg_routine = [
        (50,-40,-30,0.6),
        (50,40,-30,0.2),
        (50,40,0,0.2),
        (50,-40,0,0.2)
        ]

def get_leg_angles(*leg_ee):
    return interp(*leg_ee)

def move_linear(*linear):
    legs[0].move(*get_leg_angles(*linear))

mc = motion.MotionController(move_linear)


command_looper = ControlLoopSpooler(leg_routine, lambda a,b,c,t : mc.nq((a,b,c), t))

legs[0].enable = True
legpos = (0, hip_down_angle, knee_down_angle)
legs[0].move(*legpos)
mc.nq(legpos, 0)

command_looper.spool(8)

def refill_task(t, dt):
    while mc.depth() < 10:
        command_looper.spool(10)

def execute():
    util.looper(util.round_robin_dispatcher(refill_task, test.motion_plan_task), 10)
