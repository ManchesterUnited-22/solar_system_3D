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


def _draw_label(name, pos, color, size=0.6, alpha=1.0):
    """Chữ cái luôn quay mặt về phía camera tại vị trí pos."""
    glPushMatrix()
    glTranslatef(*pos)
    m = glGetFloatv(GL_MODELVIEW_MATRIX)
    glLoadIdentity()
    glTranslatef(m[3][0], m[3][1], m[3][2])
    glColor4f(color[0], color[1], color[2], alpha)
    glBegin(GL_LINES)
    for (x0, y0), (x1, y1) in _LETTERS[name]:
        glVertex3f(x0 * size, y0 * size, 0.0)
        glVertex3f(x1 * size, y1 * size, 0.0)
    glEnd()
    glPopMatrix()


def draw_axes(alpha=None):
    """Vẽ hệ trục. alpha = {"X": a, "Y": a, "Z": a} (0..1) làm mờ từng trục."""
    alpha = alpha or {}
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LINE_SMOOTH)

    n = int(AXIS_LEN / TICK_STEP)
    for name, d, (u, v), color in _AXES:
        a_ = alpha.get(name, 1.0)
        glColor4f(color[0], color[1], color[2], a_)

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
        _draw_label(name, _add(base, d, ARROW_LEN + 1.0), color, alpha=a_)

    glLineWidth(1.0)
    glDisable(GL_BLEND)


def coord_end_points(x, y, z):
    """Điểm cuối của đoạn toạ độ trên mỗi trục: (x,0,0), (0,y,0), (0,0,z)."""
    return (x, 0.0, 0.0), (0.0, y, 0.0), (0.0, 0.0, z)


def draw_coord_path(x, y, z):
    """Hộp toạ độ của điểm (x, y, z), dựng từ gốc dọc theo CẢ BA trục.

    - Ba đoạn đặc kéo ra từ gốc dọc trục X (đỏ), Y (xanh lá), Z (xanh dương);
      độ dài mỗi đoạn chính là giá trị toạ độ trên trục đó.
    - Các cạnh còn lại của hình hộp vẽ nét đứt, mỗi cạnh mang màu của trục song
      song với nó, nối các đầu đoạn tới hành tinh.
    - Một chấm tròn đánh dấu đầu của mỗi đoạn.
    Vẽ đè lên các trục đang bị làm mờ.
    """
    vals = (x, y, z)
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LINE_SMOOTH)
    # Đường này trùng đúng vị trí với trục (đang mờ). Thu nhẹ độ sâu để nó luôn
    # thắng phép thử độ sâu, tránh đứt nét (z-fighting). Không dùng
    # glPolygonOffset vì nó không áp dụng cho đường GL_LINES.
    glDepthRange(0.0, 0.99999)

    def edges(solid):
        """Các cạnh của hộp: với mỗi trục k, 4 cạnh song song với k."""
        for k in range(3):
            if abs(vals[k]) < 1e-9:
                continue                      # toạ độ bằng 0: cạnh có độ dài 0
            i, j = [m for m in range(3) if m != k]
            for ci in (0.0, vals[i]):
                for cj in (0.0, vals[j]):
                    is_leg = (ci == 0.0 and cj == 0.0)   # cạnh xuất phát từ gốc
                    if is_leg != solid:
                        continue
                    a = [0.0, 0.0, 0.0]
                    b = [0.0, 0.0, 0.0]
                    a[i] = b[i] = ci
                    a[j] = b[j] = cj
                    b[k] = vals[k]
                    yield k, a, b

    # 1) Cạnh nét đứt (vẽ trước để đoạn đặc nằm trên)
    glEnable(GL_LINE_STIPPLE)
    glLineStipple(2, 0x0F0F)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    for k, a, b in edges(solid=False):
        c = _AXES[k][3]
        glColor4f(c[0], c[1], c[2], 0.9)
        glVertex3f(*a)
        glVertex3f(*b)
    glEnd()
    glDisable(GL_LINE_STIPPLE)

    # 2) Ba đoạn đặc từ gốc dọc từng trục
    glLineWidth(3.5)
    glBegin(GL_LINES)
    for k, a, b in edges(solid=True):
        c = _AXES[k][3]
        glColor4f(c[0], c[1], c[2], 1.0)
        glVertex3f(*a)
        glVertex3f(*b)
    glEnd()

    # 3) Chấm tròn ở đầu mỗi đoạn (kể cả trục có toạ độ 0: chấm nằm tại gốc)
    glEnable(GL_POINT_SMOOTH)
    glPointSize(9.0)
    glBegin(GL_POINTS)
    for (_, _, _, c), p in zip(_AXES, coord_end_points(x, y, z)):
        glColor4f(c[0], c[1], c[2], 1.0)
        glVertex3f(*p)
    glEnd()

    glDepthRange(0.0, 1.0)
    glLineWidth(1.0)
    glPointSize(1.0)
    glDisable(GL_BLEND)
    glEnable(GL_LIGHTING)