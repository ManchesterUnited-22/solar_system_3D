import math
import random
from OpenGL.GL import *

_belt_lists = []


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


def _ellipse_point(a, e, E, omega=0.0, incl=0.0, node=0.0):
    """Điểm (x, y, z) trên elip theo góc lệch tâm E; Mặt Trời ở tiêu điểm (gốc toạ độ).

    omega: xoay hướng cận nhật trong mặt phẳng quỹ đạo (radian)
    incl : độ nghiêng của mặt phẳng quỹ đạo so với mặt phẳng XZ (radian)
    node : hướng đường giao (nút lên) giữa hai mặt phẳng (radian)
    """
    b = a * math.sqrt(1.0 - e * e)
    px = a * (math.cos(E) - e)
    pz = b * math.sin(E)
    c, s = math.cos(omega), math.sin(omega)
    x, z = px * c - pz * s, px * s + pz * c

    if incl == 0.0:
        return x, 0.0, z

    # Quay quanh trục n = (cos node, 0, sin node) một góc incl (công thức Rodrigues)
    nx, nz = math.cos(node), math.sin(node)
    ci, si = math.cos(incl), math.sin(incl)
    d = nx * x + nz * z
    return (x * ci + nx * d * (1.0 - ci),
            (nz * x - nx * z) * si,
            z * ci + nz * d * (1.0 - ci))


def orbit_position(semi_major_axis, eccentricity, mean_anomaly,
                   omega=0.0, incl=0.0, node=0.0):
    """Vị trí (x, y, z) hành tinh theo định luật Kepler: nhanh ở cận nhật, chậm ở viễn nhật."""
    E = solve_kepler(mean_anomaly, eccentricity)
    return _ellipse_point(semi_major_axis, eccentricity, E, omega, incl, node)


def draw_orbit(semi_major_axis, eccentricity=0.0, omega=0.0,
               incl=0.0, node=0.0, segments=240):
    """Vẽ quỹ đạo elip (có thể nghiêng so với mặt phẳng XZ)."""
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LINE_SMOOTH)
    glColor4f(0.55, 0.65, 0.90, 0.60)

    glBegin(GL_LINE_LOOP)
    for i in range(segments):
        E = 2.0 * math.pi * i / segments
        x, y, z = _ellipse_point(semi_major_axis, eccentricity, E, omega, incl, node)
        glVertex3f(x, y, z)
    glEnd()

    glDisable(GL_BLEND)


BELT_R_MIN, BELT_R_MAX = 10.9, 12.5     # nằm giữa Sao Hỏa (~10.5) và Sao Mộc (~13.8)
BELT_BANDS = 6                          # chia vành đai thành các dải quay với tốc độ khác nhau
BELT_SIZES = (1.5, 2.2, 3.2)            # kích thước điểm: nhỏ / vừa / lớn


def _build_belt(n=7000):
    global _belt_lists
    rnd = random.Random(5)
    bands = [[] for _ in range(BELT_BANDS)]
    for _ in range(n):
        # Tập trung ở giữa vành đai, thưa dần ra hai mép
        r = min(BELT_R_MAX, max(BELT_R_MIN, rnd.gauss(11.7, 0.38)))
        ang = rnd.uniform(0, 2 * math.pi)
        y = rnd.gauss(0, 0.07)
        b = rnd.uniform(0.35, 0.90)
        k = 2 if b > 0.82 else (1 if b > 0.62 else 0)      # tảng sáng thì to hơn
        band = min(BELT_BANDS - 1,
                   int((r - BELT_R_MIN) / (BELT_R_MAX - BELT_R_MIN) * BELT_BANDS))
        bands[band].append((r * math.cos(ang), y, r * math.sin(ang), b, k))

    _belt_lists = []
    for band, pts in enumerate(bands):
        r_mid = BELT_R_MIN + (band + 0.5) * (BELT_R_MAX - BELT_R_MIN) / BELT_BANDS
        # Định luật Kepler thứ 3: càng xa càng quay chậm (lấy Sao Hỏa làm mốc)
        speed = 9.5 * (9.9 / r_mid) ** 1.5
        lst = glGenLists(1)
        glNewList(lst, GL_COMPILE)
        for k, size in enumerate(BELT_SIZES):
            glPointSize(size)
            glBegin(GL_POINTS)
            for x, y, z, b, kk in pts:
                if kk == k:
                    glColor3f(0.80 * b, 0.72 * b, 0.60 * b)
                    glVertex3f(x, y, z)
            glEnd()
        glEndList()
        _belt_lists.append((lst, speed))


def draw_asteroid_belt(t):
    if not _belt_lists:
        _build_belt()
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_POINT_SMOOTH)
    for lst, speed in _belt_lists:
        glPushMatrix()
        glRotatef(t * speed, 0, 1, 0)
        glCallList(lst)
        glPopMatrix()
    glDisable(GL_POINT_SMOOTH)
    glDisable(GL_BLEND)
    glPointSize(1.0)

