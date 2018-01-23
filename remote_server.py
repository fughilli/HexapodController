#!/usr/bin/python

import numpy
import socket
import threading
import signal
import sys

import lib.control
import lib.motion
import lib.util

import hexapod

num_directions = 24
droutines = [
    lib.motion.read_routine('path/leg2_walk_d%d.dat' % (direction,))
    for direction in range(num_directions)
]
raise_routine = lib.motion.read_routine('path/leg2_raise.dat')
lower_routine = lib.motion.read_routine('path/leg2_lower.dat')

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
        self.state = self.STATE_IDLE
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
        if self.waitset == []:
            return True

        for mc in self.waitset:
            if mc.depth() < THRESHOLD_FILL_LEVEL:
                return True
        return False

    def get_next_plan(self):
        if self.state == self.STATE_IDLE:
            if self.walk == False:
                self.waitset = []
            else:
                self.state = self.STATE_WALKING
                self.waitset = self.nondominant_mcs
                for mc in self.nondominant_mcs:
                    mc.nqr(self.raise_routine)
        elif self.state == self.STATE_WALKING:
            if self.walk == True:
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
                self.state = self.STATE_IDLE
                self.waitset = self.nondominant_mcs
                for mc in self.nondominant_mcs:
                    mc.nqr(self.lower_routine)

    def get_update_task(self):
        def _update_task(t, dt):
            if not self.need_update():
                return

            self.get_next_plan()
        return _update_task


mp = MotionPlanner(mcs, [0, 2, 4], [1, 3, 5], [0, -4, -8, -12, -16, -20],
                   droutines, raise_routine, lower_routine)

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(('', 1337))
serversocket.listen(1)

run_flag = True


def server_thread():
    while (run_flag):
        print "Listening thread starting new socket"
        clientsocket, address = serversocket.accept()
        try:
            cs = lib.control.ControlSocket(clientsocket)
            while (run_flag):
                c = cs.receiveControl()
                mp.direction = c['direction']
                mp.walk = bool(c['walk'])
        except Exception as e:
            print "Exception in listening thread:", e.message
        clientsocket.close()

def motion_plan_task(t, dt):
    for mc in mcs:
        mc.update(dt * 2)


st = threading.Thread(target=server_thread)

def signal_handler(signal, frame):
    global run_flag
    run_flag = False
    print "Caught Ctrl-C. Exiting..."

signal.signal(signal.SIGINT, signal_handler)

print "Starting listening thread"
st.start()

print "Enabling legs"
for leg in hexapod.legs:
    leg.enable = True

print "Starting loop"
lib.util.looper(lib.util.round_robin_dispatcher(mp.get_update_task(),
                                                motion_plan_task
                                                ),
                run_test=(lambda : run_flag))

print "Disabling legs"
for leg in hexapod.legs:
    leg.enable = False

run_flag = False

print "Joining listening thread"
st.join()

serversocket.close()
