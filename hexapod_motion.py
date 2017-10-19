import numpy

import lib.iksolve
import lib.motion
import lib.util

pi = numpy.pi

leg_armature = lib.iksolve.Armature.fromXml(
    open('spec/leg_spec.xml', 'r').read())
leg_interp = lib.util.load_interpolator_from_lut('lut/leg_lut.dat')

num_legs = 6
leg_origin = (80, 0, 0)
leg0_angle = 2 * pi / 12

leg_transforms = [
    lib.util.rotation_matrix(
        (0, 0, -1), 2 * pi / num_legs * i +
        leg0_angle).dot(lib.util.translation_matrix(leg_origin))
    for i in range(num_legs)
]


def matrix_transform(m):
    return lambda c: tuple(m.dot(numpy.array(c + (1,)))[:3])


loop_time = 2
down_z = 0
up_z = 20
radius = 50

directions = 18

loop_origin = (100, 0, -90)

loop_transforms = [
    lib.util.translation_matrix(loop_origin).dot(
        lib.util.rotation_matrix((0, 0, -1), 2 * pi / directions * i))
    for i in range(directions)
]

walk_routine = [((radius, 0, down_z), loop_time / 2),
                ((-radius, 0, down_z), loop_time / 4), ((0, 0, up_z),
                                                        loop_time / 4)]

walk_routines = [
    lib.motion.transform_routine(walk_routine, matrix_transform(loop_transform))
    for loop_transform in loop_transforms
]

translated_routines = [
    lib.motion.transform_routine(
        lib.motion.subdivide_routine(
            linear_routine, 0.05), lambda *args: tuple(leg_interp(*args)))
    for linear_routine in walk_routines
]

for direction, troutine in zip(range(directions), translated_routines):
    lib.motion.write_routine(('leg_walk_d%d.dat' % (direction,)), troutine)
