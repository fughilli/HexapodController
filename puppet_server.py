#!/usr/bin/python
import math
import numpy
import threading
import signal
import sys

import lib.control
import lib.motion
import lib.util

from steamcontroller import SteamController, SCButtons

import hexapod


class WorldLimb(object):

    def __init__(self, lut, motion_callback, rotation, origin, max_v):
        self._lin_motion_controller = lib.motion.MotionController(
            self._lin_callback)
        self._lin_motion_controller.nq((0,0,0), 1)
        self.lut = lut
        self.motion_callback = motion_callback
        self.transform = lib.util.translation_matrix(origin).dot(
            lib.util.rotation_matrix((0, 0, -1), rotation))
        self.max_v = max_v

    def update(self, dt):
        self._lin_motion_controller.update(dt)

    def _lin_callback(self, pos):
        ang_pos = self.lut(*pos)
        if numpy.isnan(ang_pos).any():
            return
        self.motion_callback(ang_pos)

    def nqi(self, pos):
        target = self.transform.dot(numpy.array(pos + (1,)).T)
        self._lin_motion_controller.nqi_v((target[0], target[1], target[2]),
                                          self.max_v)

NOT_TOUCHED = 0
TOUCHED = 1
CLICKED = 2

class SCInputController(object):

    def __init__(self, update_period, world_limbs, lset_idx, rset_idx, radius,
                 up_z, down_z):
        self.l_world_limbs = [world_limbs[x] for x in lset_idx]
        self.r_world_limbs = [world_limbs[x] for x in rset_idx]

        self.radius = radius
        self.up_z = up_z
        self.down_z = down_z

        self._run_flag = True
        self._update_flag = False
        self.update_timer = lib.util.PeriodicTimer(update_period)

        self.steam_controller = SteamController(
            callback=self._steam_controller_hook)
        self.poll_thread = threading.Thread(target=self._poll_thread)

    def start(self):
        self.poll_thread.start()

    def stop(self):
        self._run_flag = False
        self.poll_thread.join()

    def update(self, dt):
        self._update_flag = self.update_timer.tick(dt) or self._update_flag

    def _poll_thread(self):
        while (self._run_flag):
            try:
                self.steam_controller.handleEvents()
            except Exception as e:
                print e.message

    def _axis_control_hook(self, x, y, pressed, world_limbs):
        for wl in world_limbs:
            if pressed == NOT_TOUCHED:
                wl.nqi((0, 0, 0))
            elif pressed == TOUCHED:
                wl.nqi((x * self.radius, y * self.radius, self.up_z))
            elif pressed == CLICKED:
                wl.nqi((x * self.radius, y * self.radius, self.down_z))

    def _control_hook(self, lx, ly, lp, rx, ry, rp):
        if not self._update_flag:
            return
        self._update_flag = False
        self._axis_control_hook(lx, ly, lp, self.l_world_limbs)
        self._axis_control_hook(rx, ry, rp, self.r_world_limbs)

    def _steam_controller_hook(self, _, data):
        lx = data.lpad_x / 32768.0
        ly = data.lpad_y / 32768.0
        if (data.buttons & SCButtons.LPAD):
            lp = CLICKED
        elif (data.buttons & SCButtons.LPADTOUCH):
            lp = TOUCHED
        else:
            lp = NOT_TOUCHED
        rx = data.rpad_x / 32768.0
        ry = data.rpad_y / 32768.0
        if (data.buttons & SCButtons.RPAD):
            rp = CLICKED
        elif (data.buttons & SCButtons.RPADTOUCH):
            rp = TOUCHED
        else:
            rp = NOT_TOUCHED
        self._control_hook(lx, ly, lp, rx, ry, rp)

print "Loading lookup table..."
leg_interp = lib.util.load_interpolator_from_lut('lut/leg2_lut.dat')

num_legs = 6
leg_origin = (55, 0, -50)
leg0_angle = 2 * numpy.pi / 12
leg_angles = [2 * numpy.pi / num_legs * i + leg0_angle for i in range(num_legs)]

world_limbs = []
for leg, leg_angle in zip(hexapod.legs, leg_angles):
    world_limbs.append(
        WorldLimb(leg_interp, leg.move, leg_angle, leg_origin, 30))

if __name__ == '__main__':

    print "Starting input controller..."
    scic = SCInputController(0.1, world_limbs, [0, 2, 4], [1, 3, 5], 20, 35, 0)


    def motion_plan_task(t, dt):
        for wl in world_limbs:
            wl.update(dt)
        scic.update(dt)


    def signal_handler(signal, frame):
        scic.stop()
        print "Caught Ctrl-C. Exiting..."

    signal.signal(signal.SIGINT, signal_handler)

    print "Starting listening thread"
    scic.start()

    print "Enabling legs"
    for leg in hexapod.legs:
        leg.enable = True

    print "Starting loop"
    lib.util.looper(
        lib.util.round_robin_dispatcher(motion_plan_task),
        run_test=(lambda: scic._run_flag))

    print "Disabling legs"
    for leg in hexapod.legs:
        leg.enable = False
