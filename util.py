import time


def clamp(val, low, high):
    return min((max((val, low)), high))


def map(val, ilow, ihigh, olow, ohigh):
    return olow + (ohigh - olow) * (val - ilow) / (ihigh - ilow)


def lerp(a, b, t):
    t = float(t)
    return b * t + a * (1 - t)


def lerp_tuple(at, bt, t):
    t = float(t)
    return tuple(be * t + ae * (1 - t) for ae, be in zip(at, bt))


def looper(function, total_time):
    start_time = time.time()
    last_time = start_time
    while (True):
        current_time = time.time()
        function(current_time - start_time, current_time - last_time)
        last_time = current_time
        if (current_time - start_time >= total_time):
            break


def round_robin_dispatcher(*loop_functions):

    def _dispatch(t, dt):
        for loop_function in loop_functions:
            loop_function(t, dt)

    return _dispatch


def delay_task(delay):

    def _dispatch(t, dt):
        time.sleep(delay)

    return _dispatch


class PeriodicTimer(object):

    def __init__(self, period):
        self.period = period
        self.count = 0

    def tick(self, dt=1):
        self.count += dt
        if self.count >= self.period:
            self.count = 0
            return True
        return False


def rotate(l, n):
    n = n % len(l)
    return l[n:] + l[:n]

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
