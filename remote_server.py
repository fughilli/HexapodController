#!/usr/bin/python
import math
import numpy
import threading
import signal
import sys
import datetime

import lib.control
import lib.motion
import lib.util

from steamcontroller import SteamController, SCButtons

import hexapod


def log(*args):
    sys.stdout.write('%s: %s\n' % (str(datetime.datetime.now()),
                                   ''.join(str(a) for a in args)))
    sys.stdout.flush()


current_state = 0


def log_state(state):
    global current_state
    if state != current_state:
        log('state:', {
            MotionPlanner.STATE_SHUTDOWN: 'shutdown',
            MotionPlanner.STATE_EGG: 'egg',
            MotionPlanner.STATE_SITTING: 'sitting',
            MotionPlanner.STATE_IDLE: 'idle',
            MotionPlanner.STATE_WALKING: 'walking'
        }[state])
        current_state = state


num_directions = 24
droutines = [
    lib.motion.read_routine('path/leg2_walk_d%d.dat' % (direction,))
    for direction in range(num_directions)
]
raise_routine = lib.motion.read_routine('path/leg2_raise.dat')
lower_routine = lib.motion.read_routine('path/leg2_lower.dat')

THRESHOLD_FILL_LEVEL = 2

# these needs to be updated by the control socket
input_direction = 0
input_walk = False

mcs = hexapod.motion_controllers
dominant_mcs = [mcs[x] for x in [0, 2, 4]]
nondominant_mcs = [mcs[x] for x in [1, 3, 5]]


class MotionPlanner(object):
    STATE_IDLE = 0  # all legs planted
    STATE_WALKING = 1
    STATE_SITTING = 2
    STATE_EGG = 3
    STATE_SHUTDOWN = 4

    def __init__(self, mcs, dominants, nondominants, doffsets, droutines,
                 raise_routine, lower_routine):
        self.state = self.STATE_EGG
        self.waitset = mcs

        self.droutines = droutines
        self.droutines_flipped = [
            lib.motion.rotate_t(droutine, lib.motion.routine_time(droutine) / 2)
            for droutine in droutines
        ]
        self.raise_routine = raise_routine
        self.lower_routine = lower_routine

        parked_pos = (math.pi / 3, math.pi / 2, -math.pi)

        self.de_eggify_routine = [(parked_pos, 1), (lower_routine[0][0], 0)]
        self.eggify_routine = [(lower_routine[0][0], 1), (parked_pos, 0)]

        self.doffsets = doffsets

        self.mcs = mcs
        self.dominant_mcs = [mcs[x] for x in dominants]
        self.dominant_doffsets = [doffsets[x] for x in dominants]
        self.nondominant_mcs = [mcs[x] for x in nondominants]
        self.nondominant_doffsets = [doffsets[x] for x in nondominants]

        self.direction = 0
        self.walk = False

        self.shutting_down = False

    def shutdown(self):
        self.shutting_down = True

    def wakeup(self):
        self.shutting_down = False

    def need_update(self):
        if self.waitset == []:
            return True

        for mc in self.waitset:
            if mc.depth() < THRESHOLD_FILL_LEVEL:
                return True
        return False

    def get_next_plan(self):
        log_state(self.state)
        if self.state == self.STATE_SHUTDOWN:
            if self.shutting_down:
                if not hexapod.legs[0].enable:
                    return
                for leg in hexapod.legs:
                    leg.enable = False
                return
            else:
                for leg in hexapod.legs:
                    leg.enable = True
                self.waitset = []
                self.state = self.STATE_EGG
        elif self.state == self.STATE_EGG:
            if self.shutting_down:
                self.state = self.STATE_SHUTDOWN
            else:
                self.waitset = self.mcs
                self.state = self.STATE_SITTING
                for mc in self.mcs:
                    mc.nqr(self.de_eggify_routine)
        elif self.state == self.STATE_SITTING:
            if self.shutting_down:
                self.waitset = self.mcs
                self.state = self.STATE_EGG
                for mc in self.mcs:
                    mc.nqr(self.eggify_routine)
            else:
                self.waitset = self.mcs
                self.state = self.STATE_IDLE
                for mc in self.mcs:
                    mc.nqr(self.lower_routine)
        elif self.state == self.STATE_IDLE:
            if self.shutting_down:
                self.waitset = self.mcs
                self.state = self.STATE_SITTING
                for mc in self.mcs:
                    mc.nqr(self.raise_routine)
            elif not self.walk:
                self.waitset = []
            else:
                self.state = self.STATE_WALKING
                self.waitset = self.nondominant_mcs
                for mc in self.nondominant_mcs:
                    mc.nqr(self.raise_routine)
        elif self.state == self.STATE_WALKING:
            if self.walk and not self.shutting_down:
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


mp = MotionPlanner(mcs, [0, 2, 4], [1, 3, 5], [-2, -6, -10, -14, -18, -22],
                   droutines, raise_routine, lower_routine)

run_flag = True


def update_control(_, control):
    global run_flag
    walk = math.sqrt(control.rpad_y**2 + control.rpad_x**2) > 2048
    if walk:
        angle = int(
            math.atan2(control.rpad_y, -control.rpad_x) * num_directions /
            (2 * math.pi)) % num_directions
    else:
        angle = 0

    if control.buttons & SCButtons.START:
        mp.wakeup()
    if control.buttons & SCButtons.BACK:
        mp.shutdown()
    if control.buttons & SCButtons.STEAM:
        mp.shutdown()
        run_flag = False
    mp.direction = angle
    mp.walk = walk


def server_thread():
    sc = SteamController(callback=update_control)
    while (run_flag):
        try:
            sc.handleEvents()
        except Exception as e:
            log("Exception in listening thread:", e.message)


def motion_plan_task(t, dt):
    for mc in mcs:
        mc.update(dt * 2)


st = threading.Thread(target=server_thread)


def signal_handler(signal, frame):
    global run_flag
    run_flag = False
    mp.shutdown()
    log("Caught Ctrl-C. Exiting...")


signal.signal(signal.SIGINT, signal_handler)

log("Starting listening thread")
st.start()

log("Enabling legs")
for leg in hexapod.legs:
    leg.enable = True

log("Starting loop")

try:
    lib.util.looper(
        lib.util.round_robin_dispatcher(mp.get_update_task(), motion_plan_task),
        run_test=(lambda: run_flag or not mp.state == mp.STATE_SHUTDOWN))
except Exception as e:
    log("Caught FATAL top level exception!")

log("Disabling legs")
for leg in hexapod.legs:
    leg.enable = False

run_flag = False

log("Joining listening thread")
st.join()
