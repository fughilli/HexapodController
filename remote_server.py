import numpy
import socket
import threading

import lib.control
import lib.motion
import lib.util

import hexapod

num_directions = 24
droutines = [
    lib.motion.read_routine('leg2_walk_d%d.dat' % (direction,))
    for direction in range(num_directions)
]
raise_routine = lib.motion.read_routine('leg2_raise.dat')
lower_routine = lib.motion.read_routine('leg2_lower.dat')

THRESHOLD_FILL_LEVEL = 3

# these needs to be updated by the control socket
input_direction = 0
input_walk = False

mcs = hexapod.motion_controllers
dominant_mcs = [mcs[x] for x in [0, 2, 4]]
nondominant_mcs = [mcs[x] for x in [1, 3, 5]]


class MotionPlanner(object):
    STATE_IDLE = 0  # all legs planted
    STATE_WALKING = 1
    THRESHOLD_FILL_LEVEL = 3

    def __init__(self, mcs, dominants, nondominants, doffsets, droutines,
                 raise_routine, lower_routine):
        self.state = STATE_IDLE
        self.waitset = mcs

        self.droutines = droutines
        self.droutines_flipped = [
            lib.motion.rotate_t(droutine, lib.motion.routine_time(droutine) / 2)
            for droutine in droutines
        ]
        self.raise_routine = raise_routine
        self.lower_routine = lower_routine

        self.doffsets = doffsets

        self.mcs = mcs
        self.dominant_mcs = [mcs[x] for x in dominants]
        self.dominant_doffsets = [doffsets[x] for x in dominants]
        self.nondominant_mcs = [mcs[x] for x in nondominants]
        self.nondominant_doffsets = [doffsets[x] for x in nondominants]

        self.direction = 0
        self.walk = False

    def need_update(self):
        for mc in self.waitset:
            if mc.queue_depth() < THRESHOLD_FILL_LEVEL:
                return True
        return False

    def get_next_plan(self):
        if self.state == STATE_IDLE:
            if walk == False:
                pass
            else:
                self.state = STATE_WALKING
                self.waitset = self.nondominant_mcs
                for mc in self.nondominant_mcs:
                    mc.nqr(self.raise_routine)
        elif self.state == STATE_WALKING:
            if walk == True:
                self.waitset = self.mcs
                for mc, doffset in zip(self.dominant_mcs,
                                       self.dominant_doffsets):
                    mc.nqr(self.droutines[(doffset + self.direction) % len(
                        self.droutines)])
                for mc, doffset in zip(self.nondominant_mcs,
                                       self.nondominant_doffsets):
                    mc.nqr(self.droutines_flipped[(doffset + self.direction) %
                                                  len(self.droutines)])
            else:
                self.state = STATE_IDLE
                self.waitset = self.nondominant_mcs
                for mc in self.nondominant_mcs:
                    mc.nqr(self.lower_routine)

    def update_task(t, dt):
        if not self.need_update():
            return

        self.get_next_plan()


mp = MotionPlanner(mcs, [0, 2, 4], [1, 3, 5], [0, -4, -8, -12, -16, -20],
                   droutines, raise_routine, lower_routine)

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind((socket.gethostname(), 1337))
serversocket.listen(1)


def server_thread():
    while (1):
        clientsocket, address = serversocket.accept()
        try:
            cs = util.control.ControlSocket(clientsocket)
            while (1):
                c = cs.receiveControl()
                mp.direction = c['direction']
                mp.walk = bool(c['walk'])
        except Exception as e:
            print e.message
            continue


threading.Thread(target=server_thread).start()

lib.util.looper(
    lib.util.round_robin_dispatcher((control_update_task, mp.update_task,
                                     hexapod.motion_plan_task)))
