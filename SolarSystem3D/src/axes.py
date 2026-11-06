"""Hệ trục toạ độ XYZ đặt tại tâm (Mặt Trời).

Các hành tinh chuyển động trên mặt phẳng XZ, trục Y hướng lên trên.
"""
import math
from OpenGL.GL import *

AXIS_LEN = 22.0        # độ dài mỗi nửa trục (lớn hơn quỹ đạo Neptune)
TICK_STEP = 2.0        # khoảng cách giữa các vạch chia
TICK_SIZE = 0.15
ARROW_LEN = 1.0
ARROW_RADIUS = 0.35

# (tên, hướng, hai hướng vuông góc, màu)
_AXES = (
    ("X", (1, 0, 0), ((0, 1, 0), (0, 0, 1)), (1.00, 0.30, 0.30)),
    ("Y", (0, 1, 0), ((1, 0, 0), (0, 0, 1)), (0.35, 0.95, 0.35)),
    ("Z", (0, 0, 1), ((1, 0, 0), (0, 1, 0)), (0.40, 0.60, 1.00)),
)

# Nét vẽ của các chữ X, Y, Z (toạ độ -1..1)
_LETTERS = {
    "X": [((-1, -1), (1, 1)), ((-1, 1), (1, -1))],
    "Y": [((-1, 1), (0, 0)), ((1, 1), (0, 0)), ((0, 0), (0, -1))],
    "Z": [((-1, 1), (1, 1)), ((1, 1), (-1, -1)), ((-1, -1), (1, -1))],
}


def _add(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k)


def _draw_label(name, pos, color, size=0.6):
    """Chữ cái luôn quay mặt về phía camera tại vị trí pos."""
    glPushMatrix()
    glTranslatef(*pos)
    m = glGetFloatv(GL_MODELVIEW_MATRIX)
    glLoadIdentity()
    glTranslatef(m[3][0], m[3][1], m[3][2])
    glColor3f(*color)
    glBegin(GL_LINES)
    for (x0, y0), (x1, y1) in _LETTERS[name]:
        glVertex3f(x0 * size, y0 * size, 0.0)
        glVertex3f(x1 * size, y1 * size, 0.0)
    glEnd()
    glPopMatrix()


def draw_axes():
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LINE_SMOOTH)

    n = int(AXIS_LEN / TICK_STEP)
    for name, d, (u, v), color in _AXES:
        glColor3f(*color)

        # Thân trục (qua gốc, cả chiều âm lẫn chiều dương)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glVertex3f(-AXIS_LEN * d[0], -AXIS_LEN * d[1], -AXIS_LEN * d[2])
        glVertex3f(AXIS_LEN * d[0], AXIS_LEN * d[1], AXIS_LEN * d[2])
        glEnd()

        # Vạch chia
        glLineWidth(1.0)
        glBegin(GL_LINES)
        for k in range(-n, n + 1):
            if k == 0:
                continue
            p = tuple(k * TICK_STEP * c for c in d)
            for w in (u, v):
                a = _add(p, w, -TICK_SIZE)
                b = _add(p, w, TICK_SIZE)
                glVertex3f(*a)
                glVertex3f(*b)
        glEnd()

        # Mũi tên ở đầu dương
        base = tuple(AXIS_LEN * c for c in d)
        tip = _add(base, d, ARROW_LEN)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(*tip)
        for j in range(17):
            a = 2.0 * math.pi * j / 16
            p = _add(_add(base, u, ARROW_RADIUS * math.cos(a)),
                     v, ARROW_RADIUS * math.sin(a))
            glVertex3f(*p)
        glEnd()

        # Nhãn X / Y / Z
        glLineWidth(2.0)
        _draw_label(name, _add(base, d, ARROW_LEN + 1.0), color)

    glLineWidth(1.0)
    glDisable(GL_BLEND)