import math
import random
from OpenGL.GL import *

_belt_list = None


def solve_kepler(mean_anomaly, eccentricity):
    """Giải M = E - e*sin(E) bằng Newton, trả về góc lệch tâm E."""
    M = math.fmod(mean_anomaly, 2.0 * math.pi)
    E = M if eccentricity < 0.8 else math.pi
    for _ in range(12):
        d = (E - eccentricity * math.sin(E) - M) / (1.0 - eccentricity * math.cos(E))
        E -= d
        if abs(d) < 1e-9:
            break
    return E


def _ellipse_point(a, e, E, omega=0.0):
    """Điểm trên elip (góc lệch tâm E), Mặt Trời ở tiêu điểm, xoay hướng cận nhật một góc omega."""
    b = a * math.sqrt(1.0 - e * e)
    x = a * (math.cos(E) - e)
    z = b * math.sin(E)
    c, s = math.cos(omega), math.sin(omega)
    return x * c - z * s, x * s + z * c


def orbit_position(semi_major_axis, eccentricity, mean_anomaly, omega=0.0):
    """Vị trí hành tinh theo định luật Kepler: nhanh ở cận nhật, chậm ở viễn nhật."""
    E = solve_kepler(mean_anomaly, eccentricity)
    return _ellipse_point(semi_major_axis, eccentricity, E, omega)


def draw_orbit(semi_major_axis, eccentricity=0.0, omega=0.0, segments=240):
    """Vẽ quỹ đạo elip trên mặt phẳng XZ."""
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LINE_SMOOTH)
    glColor4f(0.55, 0.65, 0.90, 0.35)

    glBegin(GL_LINE_LOOP)
    for i in range(segments):
        E = 2.0 * math.pi * i / segments
        x, z = _ellipse_point(semi_major_axis, eccentricity, E, omega)
        glVertex3f(x, 0.0, z)
    glEnd()

    glDisable(GL_BLEND)


def _build_belt(n=2200, r_in=11.3, r_out=12.0):
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