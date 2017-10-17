import json
import math
import numpy
import sys
import util


class MotionController(object):

    def __init__(self, motion_callback):
        '''Initializes a new MotionController

        @param motion_callback: A callback function which accepts as arguments a
        set of actuator positions as enqueued by nq()'''
        self.motion_queue = []
        self.motion_callback = motion_callback
        self.counter = 0.0
        self.current_dt = 0.0

    def nq(self, control_point, dt):
        self.motion_queue.append((control_point, dt))

    def depth(self):
        return len(self.motion_queue)

    def total_time(self):
        return routine_time(self.motion_queue)

    def update(self, dt):
        # If the queue has one element left, do nothing
        if len(self.motion_queue) <= 1:
            return

        # Advance the counter
        self.counter += dt

        # Advance the queue until the segment that counter resides in
        while self.counter > self.motion_queue[0][1]:
            self.counter -= self.motion_queue[0][1]
            self.motion_queue.pop(0)
            if len(self.motion_queue) <= 1:
                self.motion_callback(self.motion_queue[0][0])
                return

        current = util.lerp_tuple(self.motion_queue[0][0],
                                  self.motion_queue[1][0],
                                  self.counter / self.motion_queue[0][1])

        self.motion_callback(current)

    def dump_motion_queue(self):
        print 'motion queue contains:'
        for point, deadline in self.motion_queue:
            print 'going to %s in %04.3fs' % (','.join('%04.3f' % p
                                                       for p in point),
                                              deadline)


def debug_callback(control_point):
    print "Debug callback invoked with:", ', '.join("%.5f" % x
                                                    for x in control_point)
    sys.stdout.flush()


def test_motion_controllers(time, *mcs):

    def _update(t, dt):
        for mc in mcs:
            mc.update(dt)

    util.looper(_update, time)


def subdivide_routine(routine, dt):
    ret = []

    def append_callback(control_point):
        ret.append((control_point, dt))

    mc = MotionController(append_callback)
    mc.motion_queue = routine[:]
    result_points = mc.total_time() / dt
    mc.motion_queue.append(routine[0])
    mc.update(0)  # Dump the first control point to ret
    for _ in range(int(result_points) - 1):
        mc.update(dt)
    return ret


def transform_routine(routine, transform):
    return [(transform(cp), dt) for cp, dt in routine]


def planar_ellipse_routine(x0, y0, z0, xr, yr, sub, dt):
    ret = []
    for i in range(sub):
        angle = i * 2 * math.pi / sub
        ret.append(((x0 + xr * math.cos(angle), y0 + yr * math.sin(angle), z0),
                    dt))
    return ret


def check_routine(routine):
    for cp, dt in routine:
        if True in numpy.isnan(cp):
            return False
    return True


def write_routine(filename, routine):
    with open(filename, 'w') as routinefile:
        routinefile.write(json.dumps(routine))


def read_routine(filename):
    return json.loads(open(filename, 'r').read())


def routine_time(routine):
    return sum(t for c, t in routine)


def rotate_t(r, t):
    if len(r) <= 1:
        return r
    t = float(t)
    front = r[:]
    back = []
    while t > float(front[0][1]):
        t -= front[0][1]
        back.append(front.pop(0))
    if not float(t) == 0.0:
        back.append((front[0][0], t))
        front[0] = (util.lerp_tuple(front[0][0], front[1][0], t / front[0][1]),
                    front[0][1] - t)
    return front + back

    n = n % len(l)
    return l[n:] + l[:n]
