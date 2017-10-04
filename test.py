import smbus
import motor
import time
import math

bus = smbus.SMBus(0)
mc0 = motor.MotorController(bus, 0x40, 9)
mc1 = motor.MotorController(bus, 0x42, 9)

motors = mc0.motors + mc1.motors


def motor_sinusoid(motors, amplitude, offset, frequency):

    def motor_func(t, dt):
        angle = offset + amplitude * math.sin(t * frequency)
        for motor in motors:
            motor.angle = angle

    return motor_func


def looper(function, total_time):
    start_time = time.clock()
    last_time = start_time

    while (True):
        current_time = time.clock()

        function(current_time - start_time, current_time - last_time)

        last_time = current_time

        if (current_time - start_time >= total_time):
            break


for i, m in enumerate(motors):
    m.angle = motor.map(i, 0, len(motors), *m.limits)

def dispatch_loop

looper(motor_sinusoid(motors[0:3], math.radians(90), 0, 0.1), 10)
