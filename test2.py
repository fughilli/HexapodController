import test
import util
from math import pi

mcs = test.motion_controllers
legs = test.legs

legs[0].enable = True
legs[1].enable = True

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

command_loop = [
        (pi/8, pi/4, -3 * pi / 4, 0.2),
        (-pi/8, pi/4, -3 * pi / 4, 0.2),
        (-pi/8, 0, -pi/2, 0.6),
        (pi/8, 0, -pi/2, 0.2)
        ][::-1]

command_looper1 = ControlLoopSpooler(command_loop, lambda a,b,c,t : mcs[0].nq((a,b,c), t))
command_looper2 = ControlLoopSpooler(util.rotate(command_loop, 1), lambda a,b,c,t : mcs[1].nq((a,b,c), t))

def refill_task(t, dt):
    while mcs[0].depth() < 10:
        command_looper1.spool(10)
    while mcs[1].depth() < 10:
        command_looper2.spool(10)


util.looper(util.round_robin_dispatcher(refill_task, test.motion_plan_task), 10)

legs[0].enable = False
legs[1].enable = False
