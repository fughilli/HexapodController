import smbus
import motor
import time
import math
import linkage

bus = smbus.SMBus(0)
mc0 = motor.MotorController(bus, 0x40, 9)
mc1 = motor.MotorController(bus, 0x42, 9)

motors = mc0.motors + mc1.motors

BATTERY_THRESHOLD = 7  # Volts


def motor_sinusoid(motors, amplitude, offset, frequency):

    def motor_func(t, dt):
        angle = offset + amplitude * math.sin(t * frequency)
        for motor in motors:
            motor.angle = angle

    return motor_func


battery_check_timer = PeriodicTimer(10)


def battery_check_task(t, dt):
    if battery_check_timer.tick(dt):
        battery_voltage = mc0.battery
        print("Battery level: %fV" % (battery_voltage,))
        if battery_voltage < BATTERY_THRESHOLD:
            print "Battery low! Turning off motors"
            for motor in motors:
                motor.enable = False
                exit(1)


def motion_plan_task(t, dt):
    for motion_controller in motion_controllers:
        motion_controller.update(dt)


leg_params = [[0, 0, 0] for _ in range(6)]

with open('leg-spec.dat', 'r') as config_file:
    for line in config_file.readlines():
        motor_idx, leg_idx, leg_segment = [
            t(s)
            for t, s in zip((
                int,) * 3, re.match('(\d+):(\d+)-(\d+)', line).groups())
        ]
        leg_params[leg_idx][leg_segment] = motor_idx

legs = [
    linkage.Linkage(
        [motors[idx] for idx in leg_param],
        limits=[(-math.pi / 4, math.pi / 4), (-math.pi / 2, math.pi / 2),
                (-math.pi * 3 / 4, math.pi / 4)]) for leg_param in leg_params
]
