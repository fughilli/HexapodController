import util
import sys


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
        return sum(x[1] for x in self.motion_queue)

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


def debug_callback(*args):
    print "Debug callback invoked with:", ', '.join("%.5f" % x for x in args)
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
    mc.motion_queue = routine
    result_points = mc.total_time() / dt
    mc.motion_queue.append(routine[0])
    mc.update(0)  # Dump the first control point to ret
    for _ in range(int(result_points)):
        mc.update(dt)
    return ret


def transform_routine(routine, transform):
    return [(transform(cp), dt) for cp, dt in routine]
