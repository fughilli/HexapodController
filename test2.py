import test
import util
from math import pi

mcs = test.motion_controllers
legs = test.legs


class ControlLoopSpooler(object):
    def __init__(self, commands, command_func):
        self.command_func = command_func
        self.commands = commands
        self.command_idx = 0

    def spool(self, n=1):
        if len(self.commands):
            for _ in range(n):
                self.command_func(*self.commands[self.command_idx])
                self.command_idx = (self.command_idx + 1) % len(self.commands)

right_command_loop = [
        (pi/20, pi/4, -3 * pi / 4, 0.2),
        (-pi/20, pi/4, -3 * pi / 4, 0.2),
        (-pi/20, 0, -pi/2, 0.6),
        (pi/20, 0, -pi/2, 0.2)
        ][::-1]

hip_front_angle = pi/10
hip_back_angle = -hip_front_angle
hip_up_angle = 0
hip_down_angle = -pi/4
knee_up_angle = -pi/2
knee_down_angle = -pi/4
left_command_loop = [
        (hip_front_angle, hip_up_angle, knee_up_angle, 0.2*5),
        (hip_back_angle, hip_up_angle, knee_up_angle, 0.2*5),
        (hip_back_angle, hip_down_angle, knee_down_angle, 0.2*5),
        (hip_front_angle, hip_down_angle, knee_down_angle, 0.6*5)
        ]

command_loop = left_command_loop

command_loop1 = [
        (hip_front_angle, hip_up_angle, knee_up_angle, 0.2),
        (hip_back_angle, hip_up_angle, knee_up_angle, 0.2),
        (hip_back_angle, hip_down_angle, knee_down_angle, 0.2),
        (hip_front_angle, hip_down_angle, knee_down_angle, 0.6)
        ]
command_loop2 = util.rotate(command_loop1, 3)

command_looper1 = ControlLoopSpooler(command_loop1, lambda a,b,c,t : [mcs[x].nq((a,b,c), t) for x in [0,2,4]])
command_looper2 = ControlLoopSpooler(command_loop2, lambda a,b,c,t : [mcs[x].nq((a,b,c), t) for x in [1,3,5]])

for mc,leg in zip(mcs,legs):
    leg.enable = True
    legpos = (0, hip_down_angle, knee_down_angle)
    leg.move(*legpos)
    mc.nq(legpos, 0)

command_looper1.spool(8)
command_looper2.spool(8)

def refill_task(t, dt):
    while mcs[0].depth() < 10:
        command_looper1.spool(10)
    while mcs[1].depth() < 10:
        command_looper2.spool(10)

def execute():
    util.looper(util.round_robin_dispatcher(refill_task, test.motion_plan_task), 2.4)
