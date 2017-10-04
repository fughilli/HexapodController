import bits
import time
import smbus
import math
import struct


class MotorController(object):

    class Motor(object):

        def __init__(self,
                     mc,
                     index,
                     limits=(-math.pi / 2, math.pi / 2),
                     outlimits=(0, 1000)):
            self.mc = mc
            self.index = index
            self.recalibrate(limits, outlimits)
            self._enable = False

        def _write_out(self):
            self.mc.write(self.index, self._out, self._enable)

        @property
        def angle(self):
            return self._angle

        @angle.setter
        def angle(self, angle):
            self._angle = angle
            self._out = self.get_out(self._angle)
            self._write_out()

        @property
        def out(self):
            return self._out

        @property
        def enable(self):
            return self._enable

        @enable.setter
        def enable(self, enable):
            self._enable = enable
            self._write_out()

        def recalibrate(self, limits, outlimits):
            self.limits = limits
            self.outlimits = outlimits
            self._angle = (limits[0] + limits[1]) / 2
            self._out = (outlimits[0] + outlimits[1]) / 2

        def get_out(self, angle):
            return map(angle, *(self.limits + self.outlimits))

    def __init__(self, bus, address, num_motors):
        self.bus = bus
        self.address = address
        self.num_motors = num_motors

        self.read_limits()

        self.motors = [
            self.Motor(
                self, index=i, outlimits=(0, self.limits[1] - self.limits[0]))
            for i in range(self.num_motors)
        ]

        self._values = [motor.out for motor in self.motors]

    def read_limits(self):
        limits_data = self.bus.read_i2c_block_data(self.address,
                                                   self.num_motors * 2, 4)
        limits_data_buf = ''.join(chr(x) for x in limits_data)
        self.limits = struct.unpack('HH', limits_data_buf)

    def read_adc(self):
        adc_data = self.bus.read_i2c_block_data(self.address,
                                                (self.num_motors * 2) + 4, 2)
        adc_data_buf = ''.join(chr(x) for x in adc_data)
        self.raw_adc = struct.unpack('H', adc_data_buf)[0]

    @property
    def battery(self):
        self.read_adc()
        ADC_PRECISION = 2**10.0
        VCC = 3.3
        R1 = 100e3
        R2 = 47e3
        FUDGE = 0.03
        return self.raw_adc / ADC_PRECISION * VCC * (R1 + R2) / R2 + FUDGE

    def _write_buffer(self, position, buf):
        bytes_out = [ord(c) for c in buf]
        self.bus.write_i2c_block_data(self.address, position, bytes_out)

    def _write_out(self):
        buf = struct.pack('H' * len(self._values), *self._values)
        self._write_buffer(0, buf)

    def write(self, index, value, enable):
        value = int(value)
        enable = bool(enable)

        self.write_noflush(
            index,
            bits.make_field(value, 0, 15) | bits.make_field(enable, 15, 1))
        self._write_buffer(index * 2, struct.pack('H', self._values[index]))

    def write_noflush(self, index, value):
        self._values[index] = value

    def flush(self):
        self._write_out()
