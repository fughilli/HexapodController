import motor
import curses
import math
import json


def calibrate_limits(motor, limit_angles):
    print "Starting calibration..."
    motor.reset_limits()
    motor.enable = True

    stdscr = curses.initscr()
    curses.cbreak()
    stdscr.keypad(1)

    outlimits = []

    for angle in limit_angles:
        write_angle = 0
        stdscr.addstr(0, 10, "Use the arrow keys to move the motor")
        stdscr.addstr(1, 10, "to %f degrees" % (math.degrees(angle)))
        stdscr.addstr(2, 10, "Press right arrow key when done")
        stdscr.refresh()

        key = ''
        while key != curses.KEY_RIGHT:
            key = stdscr.getch()
            stdscr.refresh()
            if key == curses.KEY_UP:
                write_angle += math.radians(0.5)
                if write_angle > motor.limits[1]:
                    stdscr.addstr(4, 10, "Reached max limit")
                    write_angle = motor.limits[1]
            if key == curses.KEY_DOWN:
                write_angle -= math.radians(0.5)
                if write_angle < motor.limits[0]:
                    stdscr.addstr(4, 10, "Reached min limit")
                    write_angle = motor.limits[0]
            motor.angle = write_angle

        outlimits.append(motor.get_out(write_angle))

    motor.enable = False

    curses.endwin()

    motor.recalibrate(limit_angles, outlimits)

    print "Finished calibration"


def scale_limits(motor, limit_angles):
    pass


class Linkage(object):

    def __init__(self, motors, limits=None):
        self.motors = motors

        if limits == None:
            self.limits = [m.limits for m in self.motors]
        else:
            self.limits = limits
            for m, limit in zip(self.motors, self.limits):
                m.limits = limit

    def serialize_calibration(self):
        return json.dumps({
            'limits': self.limits,
            'motor_ilimits': [m.limits for m in self.motors],
            'motor_olimits': [m.outlimits for m in self.motors]
        })

    def deserialize_calibration(self, string):
        calibration = json.loads(string)
        self.limits = calibration['limits']
        for m, ilimits, olimits in zip(self.motors,
                                       calibration['motor_ilimits'],
                                       calibration['motor_olimits']):
            m.recalibrate(ilimits, olimits)

    def save_calibration(self, filename):
        with open(filename, 'w+') as f:
            f.write(self.serialize_calibration())

    def load_calibration(self, filename):
        with open(filename, 'r') as f:
            self.deserialize_calibration(f.read())

    def calibrate(self):
        for m, l in zip(self.motors, self.limits):
            calibrate_limits(m, l)

    @property
    def enable(self):
        return self._enable

    @enable.setter
    def enable(self, enable):
        self._enable = enable
        for m in self.motors:
            m.enable = enable

    def move(self, angles):
        for m, a in zip(self.motors, angles):
            m.angle = a
