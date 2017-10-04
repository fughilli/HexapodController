import util
import sys


class MotionController(object):

    def __init__(self, motion_callback):
        '''Initializes a new MotionController

        @param motion_callback: A callback function which accepts as arguments a
        set of actuator positions as enqueued by enqueue_control_point()'''
        self.motion_queue = []
        self.motion_callback = motion_callback
        self.counter = 0.0
        self.current_dt = 0.0

    def enqueue_control_point(self, control_point, dt):
        self.motion_queue.append((control_point, dt))

    def update(self, dt):
        # If the queue has less than 2 elements, do nothing
        if len(self.motion_queue) < 2:
            return

        # Advance the counter
        self.counter += dt

        # Advance the queue until the segment that counter resides in
        while self.counter > self.motion_queue[1][1]:
            if len(self.motion_queue) <= 2:
                self.motion_callback(*self.motion_queue[1][0])
                return
            self.counter -= self.motion_queue[1][1]
            self.motion_queue.pop(0)

        current = util.lerp_tuple(self.motion_queue[0][0],
                                  self.motion_queue[1][0],
                                  self.counter / self.motion_queue[1][1])

        self.motion_callback(*current)


def debug_callback(*args):
    print "Debug callback invoked with:", ', '.join("%.5f" % x for x in args)
    sys.stdout.flush()
