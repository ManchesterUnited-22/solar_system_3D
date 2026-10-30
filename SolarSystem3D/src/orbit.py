import math
import random
from OpenGL.GL import *

_belt_list = None


def orbit_position(semi_major_axis, eccentricity, angle):
    """Return an elliptical orbit position with the Sun at one focus."""
    semi_minor_axis = semi_major_axis * math.sqrt(1.0 - eccentricity ** 2)
    center_offset = semi_major_axis * eccentricity
    x = semi_major_axis * math.cos(angle) - center_offset
    z = semi_minor_axis * math.sin(angle)
    return x, z


def draw_orbit(semi_major_axis, eccentricity=0.0, segments=180):
    """Draw an elliptical orbit on the XZ plane."""
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LINE_SMOOTH)
    glColor4f(0.55, 0.65, 0.90, 0.28)

    glBegin(GL_LINE_LOOP)
    for i in range(segments):
        angle = 2.0 * math.pi * i / segments
        x, z = orbit_position(semi_major_axis, eccentricity, angle)
        glVertex3f(x, 0.0, z)
    glEnd()

    glDisable(GL_BLEND)


def _build_belt(n=2200, r_in=8.4, r_out=9.2):
    global _belt_list
    rnd = random.Random(5)
    _belt_list = glGenLists(1)
    glNewList(_belt_list, GL_COMPILE)
    glPointSize(1.8)
    glBegin(GL_POINTS)
    for _ in range(n):
        ang = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(r_in, r_out)
        y = rnd.gauss(0, 0.05)
        b = rnd.uniform(0.35, 0.8)
        glColor3f(0.75 * b, 0.68 * b, 0.58 * b)
        glVertex3f(r * math.cos(ang), y, r * math.sin(ang))
    glEnd()
    glEndList()


def draw_asteroid_belt(t):
    if _belt_list is None:
        _build_belt()
    glPushMatrix()
    glRotatef(t * 2.0, 0, 1, 0)
    glCallList(_belt_list)
    glPopMatrix()