import hexapod
import lib.util
from math import pi
import sys

mcs = hexapod.motion_controllers
legs = hexapod.legs

hip_front_angle = pi / 10
hip_back_angle = -hip_front_angle
hip_up_angle = 0
hip_down_angle = -pi / 4
knee_up_angle = -pi / 2
knee_down_angle = -pi / 4

command_loop1 = [(hip_front_angle, hip_up_angle, knee_up_angle,
                  0.2), (hip_back_angle, hip_up_angle, knee_up_angle, 0.2),
                 (hip_back_angle, hip_down_angle, knee_down_angle,
                  0.2), (hip_front_angle, hip_down_angle, knee_down_angle, 0.6)]
command_loop2 = lib.util.rotate(command_loop1, 3)

command_looper1 = lib.util.ControlLoopSpooler(
    command_loop1, lambda a, b, c, t:
    [mcs[x].nq((a, b, c), t) for x in [0, 2, 4]])
command_looper2 = lib.util.ControlLoopSpooler(
    command_loop2, lambda a, b, c, t:
    [mcs[x].nq((a, b, c), t) for x in [1, 3, 5]])

print "Planting feet."

for mc, leg in zip(mcs, legs):
    leg.enable = True
    legpos = (0, hip_down_angle, knee_down_angle)
    leg.move(legpos)
    mc.nq(legpos, 0)

command_looper1.spool(8)
command_looper2.spool(8)


def refill_task(t, dt):
    while mcs[0].depth() < 10:
        command_looper1.spool(10)
    while mcs[1].depth() < 10:
        command_looper2.spool(10)


def execute():
    lib.util.looper(
        lib.util.round_robin_dispatcher(refill_task, hexapod.motion_plan_task),
        2.4)


print "Waiting for newline..."
sys.stdin.readline()

execute()
