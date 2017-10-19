import numpy

import lib.iksolve
import lib.motion
import lib.util

pi = numpy.pi

leg_armature = lib.iksolve.Armature.fromXml(
    open('spec/leg2_spec.xml', 'r').read())
leg_interp = lib.util.load_interpolator_from_lut('lut/leg2_lut.dat')

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


loop_time = 2.0
down_z = 0.0
up_z = 35.0
radius = 25.0

#loop_time = 2.0
#down_z = 0.0
#up_z = 35.0
#radius = 5.0

directions = 24

#loop_origin = (15.0, 0.0, -100.0)
loop_origin = (55.0, 0.0, -50.0)

loop_transforms = [
    lib.util.translation_matrix(loop_origin).dot(
        lib.util.rotation_matrix((0, 0, -1), 2 * pi / directions * i))
    for i in range(directions)
]

base_walk_routine = [((0,       0, down_z), loop_time * 0.25),
                     ((-radius, 0, down_z), loop_time * 0.1),
                     ((-radius, 0, up_z/2), loop_time * 0.15),
                     ((0,       0, up_z),   loop_time * 0.15),
                     ((radius,  0, up_z/2), loop_time * 0.1),
                     ((radius,  0, down_z), loop_time * 0.25)] # yapf: disable


lower_routine = [((0, 0, up_z),     2),
                 ((0, 0, down_z),   0)] # yapf: disable

raise_routine = [((0, 0, down_z),   2),
                 ((0, 0, up_z),     0)] # yapf: disable

walk_routines = [
    lib.motion.transform_routine(base_walk_routine,
                                 matrix_transform(loop_transform))
    for loop_transform in loop_transforms
]

lower_routine_transformed = lib.motion.transform_routine(
    lower_routine, matrix_transform(loop_transforms[0]))
raise_routine_transformed = lib.motion.transform_routine(
    raise_routine, matrix_transform(loop_transforms[0]))

walk_routines_subdiv = [
    lib.motion.subdivide_routine(walk_routine, 0.05)
    for walk_routine in walk_routines
]

lower_routine_subdiv = lib.motion.subdivide_routine(lower_routine_transformed,
                                                    0.05)
raise_routine_subdiv = lib.motion.subdivide_routine(raise_routine_transformed,
                                                    0.05)

translated_routines = [
    lib.motion.transform_routine(
        walk_routine_subdiv, lambda *args: tuple(leg_interp(*args)))
    for walk_routine_subdiv in walk_routines_subdiv
]

lower_routine_translated = lib.motion.transform_routine(
    lower_routine_subdiv, lambda *args: tuple(leg_interp(*args)))
raise_routine_translated = lib.motion.transform_routine(
    raise_routine_subdiv, lambda *args: tuple(leg_interp(*args)))

for direction, troutine in zip(range(directions), translated_routines):
    assert lib.motion.check_routine(troutine), (
        'routine for direction %d is invalid' % (direction,))
    lib.motion.write_routine(('path/leg2_walk_d%d.dat' % (direction,)),
                             troutine)

lib.motion.write_routine('path/leg2_lower.dat', lower_routine_translated)
lib.motion.write_routine('path/leg2_raise.dat', raise_routine_translated)
