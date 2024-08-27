import math
import random
from particle import Particle

def dot_product(v1, v2):
    return sum(a * b for a, b in zip(v1, v2))

def particle_collision(p1: Particle, p2: Particle) -> bool:
    if not p1.overlaps_with(p2):
        return False
    m1 = p1.mass
    m2 = p2.mass

    normal_vec = (p2.x - p1.x, p2.y - p1.y)
    distance = math.hypot(*normal_vec)

    if distance == 0:
        return False

    normal_unit_vec = (normal_vec[0] / distance, normal_vec[1] / distance)
    tangent_unit_vec = (-normal_unit_vec[1], normal_unit_vec[0])

    relative_velocity = [p2.xv - p1.xv, p2.yv - p1.yv]
    velocity_along_normal = dot_product(relative_velocity, normal_unit_vec)

    if velocity_along_normal >= 0:
        return False

    # x is normal, y is tangent
    u1x = dot_product(normal_unit_vec, (p1.xv, p1.yv))
    u1y = dot_product(tangent_unit_vec, (p1.xv, p1.yv))
    u2x = dot_product(normal_unit_vec, (p2.xv, p2.yv))
    u2y = dot_product(tangent_unit_vec, (p2.xv, p2.yv))

    v1x = ((m1 - m2) / (m1 + m2)) * u1x + ((2 * m2) / (m1 + m2)) * u2x
    v1y = u1y
    v2x = ((2 * m1) / (m1 + m2)) * u1x + ((m2 - m1) / (m1 + m2)) * u2x
    v2y = u2y

    p1.xv = v1x * normal_unit_vec[0] + v1y * tangent_unit_vec[0]
    p1.yv = v1x * normal_unit_vec[1] + v1y * tangent_unit_vec[1]
    p2.xv = v2x * normal_unit_vec[0] + v2y * tangent_unit_vec[0]
    p2.yv = v2x * normal_unit_vec[1] + v2y * tangent_unit_vec[1]

    return True

