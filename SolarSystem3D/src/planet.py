import math
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import (gluNewQuadric, gluDeleteQuadric, gluQuadricTexture,
                        gluQuadricNormals, gluSphere,
                        gluBuild2DMipmaps, GLU_SMOOTH)
from orbit import orbit_position

TEX_W, TEX_H = 1024, 512


# =====================================================================
#  NOISE / TIEN ICH TAO TEXTURE
# =====================================================================

def _smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _norm(a):
    return (a - a.min()) / (a.max() - a.min() + 1e-9)


def _lerp(c1, c2, t):
    c1 = np.asarray(c1, dtype=float)
    c2 = np.asarray(c2, dtype=float)
    if c1.ndim == 1:
        c1 = c1[None, None, :]
    if c2.ndim == 1:
        c2 = c2[None, None, :]
    t = t[..., None]
    return c1 * (1.0 - t) + c2 * t


def _noise(gx, gy, rng):
    """Value noise, lap kin theo chieu ngang (khong lo duong noi texture)."""
    grid = rng.random((gy + 1, gx))
    xs = np.linspace(0, gx, TEX_W, endpoint=False)
    ys = np.linspace(0, gy, TEX_H)
    x0 = np.floor(xs).astype(int)
    x1 = (x0 + 1) % gx
    y0 = np.minimum(np.floor(ys).astype(int), gy - 1)
    y1 = y0 + 1
    fx = (xs - x0); fx = (fx * fx * (3 - 2 * fx))[None, :]
    fy = (ys - y0); fy = (fy * fy * (3 - 2 * fy))[:, None]
    a = grid[y0][:, x0]
    b = grid[y0][:, x1]
    c = grid[y1][:, x0]
    d = grid[y1][:, x1]
    top = a + (b - a) * fx
    bot = c + (d - c) * fx
    return top + (bot - top) * fy


def _fbm(rng, base=4, octaves=5, persistence=0.5):
    total = np.zeros((TEX_H, TEX_W))
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        gx = base * (2 ** o)
        total += amp * _noise(gx, max(2, gx // 2), rng)
        norm += amp
        amp *= persistence
    return total / norm


def _lat():
    """Vi do -1 (cuc nam) .. +1 (cuc bac), shape (H, W)."""
    return np.linspace(-1, 1, TEX_H)[:, None] * np.ones((1, TEX_W))


def _craters(img, rng, count, rmin, rmax, dark=0.5):
    h, w, _ = img.shape
    for _ in range(count):
        r = rng.uniform(rmin, rmax)
        cx = rng.uniform(0, w)
        cy = rng.uniform(0.12 * h, 0.88 * h)
        x0, x1 = int(max(cx - r * 1.5, 0)), int(min(cx + r * 1.5, w))
        y0, y1 = int(max(cy - r * 1.5, 0)), int(min(cy + r * 1.5, h))
        if x1 <= x0 or y1 <= y0:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = np.hypot(xx - cx, yy - cy) / r
        floor = np.clip(1.0 - d, 0, 1) ** 0.5
        rim = np.exp(-((d - 1.0) / 0.12) ** 2)
        img[y0:y1, x0:x1] *= (1.0 - dark * floor)[..., None]
        img[y0:y1, x0:x1] += (0.14 * rim)[..., None]


# =====================================================================
#  TEXTURE TUNG HANH TINH
# =====================================================================

def tex_sun(rng):
    broad = _norm(_fbm(rng, 5, 6, 0.58))
    cells = _norm(_fbm(rng, 28, 5, 0.48))
    fine = _norm(_fbm(rng, 92, 4, 0.45))

    heat = np.clip(0.50 * broad + 0.32 * cells + 0.18 * fine, 0, 1)
    img = _lerp((0.92, 0.018, 0.002), (1.00, 0.32, 0.008), heat)
    hot = _smoothstep(0.62, 0.94, cells + fine * 0.28)
    img = _lerp(img, (1.00, 0.58, 0.055), hot * 0.72)
    white_hot = _smoothstep(0.82, 0.98, fine * 0.45 + cells * 0.55)
    img = _lerp(img, (1.00, 0.96, 0.72), white_hot * 0.58)

    yy, xx = np.mgrid[0:TEX_H, 0:TEX_W]
    for cx, cy, rx, ry in (
        (0.14 * TEX_W, 0.30 * TEX_H, 9, 4),
        (0.31 * TEX_W, 0.68 * TEX_H, 8, 5),
        (0.58 * TEX_W, 0.41 * TEX_H, 11, 5),
        (0.72 * TEX_W, 0.24 * TEX_H, 7, 4),
        (0.80 * TEX_W, 0.72 * TEX_H, 12, 6),
        (0.46 * TEX_W, 0.82 * TEX_H, 6, 4),
    ):
        d = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
        spot = np.exp(-d * 2.1)
        img = _lerp(img, (1.0, 0.78, 0.12), spot * 0.88)

    grain = _smoothstep(0.88, 0.98, fine)
    img = _lerp(img, (1.0, 0.62, 0.06), grain * 0.12)
    return np.clip(img, 0, 1)


def tex_sun_flow(rng):
    """Very subtle transparent convection on the photosphere."""
    fine = _norm(_fbm(rng, 58, 4, 0.48))
    medium = _norm(_fbm(rng, 16, 5, 0.52))
    flow = np.clip(0.68 * fine + 0.32 * medium, 0, 1)
    alpha = _smoothstep(0.62, 0.94, flow) * 0.42
    img = np.zeros((TEX_H, TEX_W, 4), np.float32)
    img[..., 0:3] = _lerp((1.0, 0.16, 0.002), (1.0, 0.82, 0.14), flow)
    img[..., 3] = alpha
    return img


def tex_mercury(rng):
    n = _norm(_fbm(rng, 6, 6, 0.55))
    img = _lerp((0.30, 0.28, 0.26), (0.68, 0.64, 0.58), n)
    _craters(img, rng, 160, 4, 22, 0.45)
    return img


def tex_moon(rng):
    n = _norm(_fbm(rng, 5, 6, 0.55))
    img = _lerp((0.38, 0.38, 0.40), (0.78, 0.78, 0.76), n)
    mare = _smoothstep(np.quantile(n, 0.55), np.quantile(n, 0.30), n)
    img = _lerp(img, (0.22, 0.22, 0.25), mare * 0.6)
    _craters(img, rng, 120, 3, 18, 0.35)
    return img


def tex_venus(rng):
    lat = _lat()
    n = _fbm(rng, 3, 6, 0.55)
    swirl = 0.5 + 0.5 * np.sin(lat * 9.0 + (n - 0.5) * 14.0)
    t = np.clip(0.55 * swirl + 0.45 * _norm(n), 0, 1)
    return _lerp((0.72, 0.48, 0.20), (0.98, 0.87, 0.58), t)


def tex_earth(rng):
    n = _norm(_fbm(rng, 3, 7, 0.55))
    dry = _norm(_fbm(rng, 5, 4, 0.5))
    lat = np.abs(_lat())
    sea = np.quantile(n, 0.66)

    depth = _smoothstep(sea - 0.25, sea, n)
    ocean = _lerp((0.01, 0.05, 0.22), (0.06, 0.38, 0.64), depth)

    elev = np.clip((n - sea) / (1.0 - sea + 1e-9) * 2.2, 0, 1)
    land = _lerp((0.10, 0.38, 0.10), (0.40, 0.33, 0.16), elev)
    desert = _smoothstep(0.55, 0.78, dry) * (1 - _smoothstep(0.45, 0.8, lat))
    land = _lerp(land, (0.80, 0.68, 0.42), desert * 0.85)

    m = _smoothstep(sea - 0.01, sea + 0.01, n)
    img = _lerp(ocean, land, m)

    edge = _norm(_fbm(rng, 10, 3, 0.5)) - 0.5
    ice = _smoothstep(0.80, 0.90, lat + edge * 0.15)
    return _lerp(img, (0.95, 0.97, 1.0), ice)


def tex_clouds(rng):
    n = _norm(_fbm(rng, 4, 6, 0.55))
    a = _smoothstep(np.quantile(n, 0.55), np.quantile(n, 0.86), n) * 0.85
    img = np.ones((TEX_H, TEX_W, 4))
    img[..., 3] = a
    return img


def tex_earth_lights(rng):
    img = np.zeros((TEX_H, TEX_W, 4), np.float32)
    yy, xx = np.mgrid[0:TEX_H, 0:TEX_W]

    city_groups = (
        (0.24 * TEX_W, 0.58 * TEX_H, 0.10 * TEX_W, 0.16 * TEX_H),
        (0.34 * TEX_W, 0.62 * TEX_H, 0.055 * TEX_W, 0.08 * TEX_H),
        (0.54 * TEX_W, 0.53 * TEX_H, 0.10 * TEX_W, 0.10 * TEX_H),
        (0.68 * TEX_W, 0.54 * TEX_H, 0.07 * TEX_W, 0.08 * TEX_H),
        (0.79 * TEX_W, 0.58 * TEX_H, 0.08 * TEX_W, 0.08 * TEX_H),
        (0.50 * TEX_W, 0.69 * TEX_H, 0.06 * TEX_W, 0.10 * TEX_H),
    )

    for cx, cy, rx, ry in city_groups:
        dx = (xx - cx) / rx
        dy = (yy - cy) / ry
        envelope = np.exp(-(dx * dx + dy * dy) * 1.4)
        phase = rng.uniform(0.0, math.pi * 2.0)
        street = (0.5 + 0.5 * np.sin(xx / 7.0 + yy / 11.0 + phase))
        street *= (0.5 + 0.5 * np.sin(xx / 13.0 - yy / 9.0 - phase))
        lights = _smoothstep(0.48, 0.82, street) * envelope
        img[..., 0] = np.maximum(img[..., 0], lights)
        img[..., 1] = np.maximum(img[..., 1], lights * 0.76)
        img[..., 2] = np.maximum(img[..., 2], lights * 0.28)

    img[..., 3] = np.clip(img[..., 0] * 1.8, 0, 1)
    return img


def tex_mars(rng):
    n = _norm(_fbm(rng, 4, 7, 0.55))
    d = _norm(_fbm(rng, 8, 5, 0.5))
    lat = np.abs(_lat())
    img = _lerp((0.42, 0.17, 0.07), (0.86, 0.46, 0.22), n)
    dark = _smoothstep(np.quantile(d, 0.62), np.quantile(d, 0.80), d) * 0.7
    img = _lerp(img, (0.22, 0.10, 0.07), dark)
    edge = _norm(_fbm(rng, 10, 3, 0.5)) - 0.5
    cap = _smoothstep(0.88, 0.95, lat + edge * 0.1)
    img = _lerp(img, (0.96, 0.96, 0.98), cap)
    _craters(img, rng, 70, 3, 16, 0.25)
    return img


def tex_jupiter(rng):
    lat = _lat()
    turb = _fbm(rng, 6, 5, 0.55) - 0.5
    n2 = _norm(_fbm(rng, 10, 4, 0.5))
    v = lat + turb * 0.12
    zone = 0.5 + 0.5 * np.sin(v * np.pi * 6.5)
    fine = 0.5 + 0.5 * np.sin(v * np.pi * 21.0 + turb * 10.0)
    t = np.clip(0.7 * zone + 0.3 * fine + (n2 - 0.5) * 0.4, 0, 1)
    img = _lerp((0.52, 0.30, 0.18), (0.93, 0.84, 0.68), t)

    # Vet Do Lon
    yy, xx = np.mgrid[0:TEX_H, 0:TEX_W]
    cx, cy = 0.30 * TEX_W, 0.36 * TEX_H
    d = ((xx - cx) / (0.075 * TEX_W)) ** 2 + ((yy - cy) / (0.050 * TEX_H)) ** 2
    spot = _smoothstep(1.0, 0.25, d)
    halo = np.exp(-((np.sqrt(d) - 1.05) / 0.18) ** 2) * 0.5
    img = _lerp(img, (0.96, 0.88, 0.78), halo * (1 - spot))
    return _lerp(img, (0.72, 0.25, 0.12), spot * 0.95)


def tex_saturn(rng):
    lat = _lat()
    turb = _fbm(rng, 6, 4, 0.5) - 0.5
    n = _norm(_fbm(rng, 10, 4, 0.5))
    v = lat + turb * 0.05
    bands = 0.5 + 0.5 * np.sin(v * np.pi * 11.0)
    fine = 0.5 + 0.5 * np.sin(v * np.pi * 37.0)
    t = np.clip(0.55 * bands + 0.25 * fine + 0.2 * n, 0, 1)
    img = _lerp((0.66, 0.55, 0.36), (0.94, 0.85, 0.62), t)
    pole = _smoothstep(0.8, 1.0, np.abs(lat)) * 0.35
    return _lerp(img, (0.50, 0.56, 0.62), pole)


def tex_uranus(rng):
    lat = _lat()
    n = _norm(_fbm(rng, 5, 4, 0.5))
    bands = 0.5 + 0.5 * np.sin(lat * np.pi * 5.0)
    t = np.clip(0.5 + (bands - 0.5) * 0.4 + (n - 0.5) * 0.25, 0, 1)
    img = _lerp((0.50, 0.78, 0.82), (0.72, 0.92, 0.93), t)
    cap = _smoothstep(0.5, 1.0, np.abs(lat)) * 0.35
    return _lerp(img, (0.88, 0.98, 0.98), cap)


def tex_neptune(rng):
    lat = _lat()
    turb = _fbm(rng, 6, 4, 0.5) - 0.5
    n = _norm(_fbm(rng, 8, 4, 0.5))
    v = lat + turb * 0.10
    bands = 0.5 + 0.5 * np.sin(v * np.pi * 6.0)
    img = _lerp((0.08, 0.16, 0.62), (0.22, 0.42, 0.95), 0.6 * bands + 0.4 * n)

    yy, xx = np.mgrid[0:TEX_H, 0:TEX_W]
    cx, cy = 0.65 * TEX_W, 0.33 * TEX_H
    d = ((xx - cx) / (0.07 * TEX_W)) ** 2 + ((yy - cy) / (0.055 * TEX_H)) ** 2
    img = _lerp(img, (0.03, 0.06, 0.30), _smoothstep(1.0, 0.3, d) * 0.9)

    st = _norm(_fbm(rng, 14, 4, 0.55))
    streak = _smoothstep(np.quantile(st, 0.90), np.quantile(st, 0.97), st)
    streak *= np.exp(-((lat + 0.40) / 0.30) ** 2)
    return _lerp(img, (0.85, 0.92, 1.0), streak * 0.7)


_BUILDERS = {
    "sun": tex_sun, "moon": tex_moon, "mercury": tex_mercury,
    "venus": tex_venus, "earth": tex_earth, "clouds": tex_clouds,
    "mars": tex_mars, "jupiter": tex_jupiter, "saturn": tex_saturn,
    "uranus": tex_uranus, "neptune": tex_neptune,
    "sun_flow": tex_sun_flow,
    "earth_lights": tex_earth_lights,
}

# Texture VE TAY (hand_textures.py) thay cho noise o cac hanh tinh co be mat dac trung.
# Lan chay dau se ve va luu vao assets/textures/*.png, cac lan sau doc lai rat nhanh.
import hand_textures as _ht

_BUILDERS.update({
    "earth":   lambda rng: _ht.load_or_build("earth_day_v1", _ht.earth_texture),
    "moon":    lambda rng: _ht.load_or_build("moon_v1", _ht.moon_texture),
    "mercury": lambda rng: _ht.load_or_build("mercury_v1", _ht.mercury_texture),
    "mars":    lambda rng: _ht.load_or_build("mars_v1", _ht.mars_texture),
    "jupiter": lambda rng: _ht.load_or_build("jupiter_v1", _ht.jupiter_texture),
    "saturn":  lambda rng: _ht.load_or_build("saturn_v1", _ht.saturn_texture),
})
# Tất cả quỹ đạo nằm trên cùng một mặt phẳng (mặt phẳng hoàng đạo) như thực tế.
# Khoảng cách và độ lệch tâm được chọn để các hành tinh (kể cả Mặt Trăng, vành đai) không chạm nhau.
PLANETS = [
    {"name": "Mercury", "texture": "mercury", "radius": 0.25,
     "orbit_radius": 3.6, "orbit_eccentricity": 0.21, "orbit_omega": 30,
     "orbit_speed": 36.3, "phase": 20,
     "spin": 1.5, "tilt": 0.03},

    {"name": "Venus", "texture": "venus", "radius": 0.40,
     "orbit_radius": 5.4, "orbit_eccentricity": 0.02, "orbit_omega": 100,
     "orbit_speed": 20.9, "phase": 110,
     "spin": -1.2, "tilt": 177.0,
     "halo": (1.0, 0.80, 0.45, 0.16)},

    {"name": "Earth", "texture": "earth", "radius": 0.45,
     "orbit_radius": 7.5, "orbit_eccentricity": 0.03, "orbit_omega": 170,
     "orbit_speed": 14.0, "phase": 200,
     "spin": 15.0, "tilt": 23.4, "clouds": True,
     "halo": (0.35, 0.60, 1.0, 0.22),
     "moon": {"radius": 0.13, "dist": 0.95, "speed": 110.0}},

    {"name": "Mars", "texture": "mars", "radius": 0.35,
     "orbit_radius": 9.9, "orbit_eccentricity": 0.06, "orbit_omega": 250,
     "orbit_speed": 9.5, "phase": 300,
     "spin": 14.4, "tilt": 25.2,
     "halo": (1.0, 0.55, 0.35, 0.08)},

    {"name": "Jupiter", "texture": "jupiter", "radius": 0.95,
     "orbit_radius": 14.5, "orbit_eccentricity": 0.05, "orbit_omega": 40,
     "orbit_speed": 4.5, "phase": 60,
     "spin": 36.0, "tilt": 3.1},

    {"name": "Saturn", "texture": "saturn", "radius": 0.80,
     "orbit_radius": 19.5, "orbit_eccentricity": 0.05, "orbit_omega": 320,
     "orbit_speed": 3.5, "phase": 250,
     "spin": 33.0, "tilt": 26.7,
     "rings": {"kind": "saturn", "inner": 1.25, "outer": 2.3}},

    {"name": "Uranus", "texture": "uranus", "radius": 0.60,
     "orbit_radius": 25.0, "orbit_eccentricity": 0.03, "orbit_omega": 200,
     "orbit_speed": 2.9, "phase": 150,
     "spin": -20.0, "tilt": 97.8,
     "halo": (0.50, 0.90, 0.95, 0.12),
     "rings": {"kind": "uranus", "inner": 1.5, "outer": 2.1}},

    {"name": "Neptune", "texture": "neptune", "radius": 0.60,
     "orbit_radius": 28.5, "orbit_eccentricity": 0.01, "orbit_omega": 120,
     "orbit_speed": 2.5, "phase": 330,
     "spin": 22.0, "tilt": 28.3,
     "halo": (0.30, 0.50, 1.0, 0.16)},
]
PLANET_INFO = {
    "Mercury": {"a": 57.91, "period": "88 NGAY", "rotation": "58.6 NGAY",
                "diameter": "4,879 KM", "temp": "167 C"},
    "Venus":   {"a": 108.21, "period": "224.7 NGAY", "rotation": "243 NGAY (NGUOC)",
                "diameter": "12,104 KM", "temp": "464 C"},
    "Earth":   {"a": 149.60, "period": "365.25 NGAY", "rotation": "24 GIO",
                "diameter": "12,742 KM", "temp": "15 C"},
    "Mars":    {"a": 227.94, "period": "687 NGAY", "rotation": "24.6 GIO",
                "diameter": "6,779 KM", "temp": "-65 C"},
    "Jupiter": {"a": 778.57, "period": "11.86 NAM", "rotation": "9.9 GIO",
                "diameter": "139,820 KM", "temp": "-110 C"},
    "Saturn":  {"a": 1433.5, "period": "29.46 NAM", "rotation": "10.7 GIO",
                "diameter": "116,460 KM", "temp": "-140 C"},
    "Uranus":  {"a": 2872.5, "period": "84.0 NAM", "rotation": "17.2 GIO (NGUOC)",
                "diameter": "50,724 KM", "temp": "-195 C"},
    "Neptune": {"a": 4495.1, "period": "164.8 NAM", "rotation": "16.1 GIO",
                "diameter": "49,244 KM", "temp": "-200 C"},
}

SUN_GM = 1.32712e11          # km^3/s^2


# =====================================================================
#  OPENGL: UPLOAD TEXTURE, DISPLAY LIST
# =====================================================================

_sphere_list = None
_tex = {}
_glow_tex = None
_halo_tex = None
_corona_tex = None


def _upload(img, mip=True, clamp_s=False):
    data = np.ascontiguousarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    h, w, c = data.shape
    fmt = GL_RGBA if c == 4 else GL_RGB
    tex = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S,
                    GL_CLAMP_TO_EDGE if clamp_s else GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    if mip:
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                        GL_LINEAR_MIPMAP_LINEAR)
        gluBuild2DMipmaps(GL_TEXTURE_2D, c, w, h, fmt, GL_UNSIGNED_BYTE, data)
    else:
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, fmt, w, h, 0, fmt,
                     GL_UNSIGNED_BYTE, data)
    return tex


def _radial_texture(fn):
    yy, xx = np.mgrid[-1:1:256j, -1:1:256j]
    r = np.hypot(xx, yy)
    img = np.ones((256, 256, 4))
    img[..., 3] = np.clip(fn(r), 0, 1)
    return _upload(img, mip=False, clamp_s=True)


def _saturn_alpha(u):
    if u < 0.14:
        return 0.10 + 0.20 * u / 0.14
    if u < 0.22:
        return 0.30
    if u < 0.58:
        return 0.85
    if u < 0.64:
        return 0.04          # khe Cassini
    if u < 0.90:
        return 0.65
    if u < 0.915:
        return 0.10          # khe Encke
    if u < 0.97:
        return 0.60
    return 0.05


def _uranus_alpha(u):
    a = 0.0
    for c, w, h in ((0.06, 0.012, 0.35), (0.16, 0.010, 0.40),
                    (0.28, 0.010, 0.40), (0.42, 0.012, 0.50),
                    (0.55, 0.010, 0.45), (0.72, 0.012, 0.50),
                    (0.90, 0.025, 0.85)):
        a = max(a, h * math.exp(-((u - c) / w) ** 2))
    return a


def _build_rings(kind, inner, outer, rng, steps=200, seg=128):
    lst = glGenLists(1)
    glNewList(lst, GL_COMPILE)
    glNormal3f(0.0, 0.0, 1.0)
    for i in range(steps):
        u = (i + 0.5) / steps
        if kind == "saturn":
            a = _saturn_alpha(u) * rng.uniform(0.78, 1.0)
            b = rng.uniform(0.82, 1.05)
            col = (min(0.93 * b, 1.0), min(0.82 * b, 1.0), min(0.62 * b, 1.0))
        else:
            a = _uranus_alpha(u)
            col = (0.62, 0.74, 0.78)
        r0 = inner + (outer - inner) * i / steps
        r1 = inner + (outer - inner) * (i + 1) / steps
        glColor4f(col[0], col[1], col[2], a)
        glBegin(GL_QUAD_STRIP)
        for j in range(seg + 1):
            ang = 2.0 * math.pi * j / seg
            c, s = math.cos(ang), math.sin(ang)
            glVertex3f(r0 * c, r0 * s, 0.0)
            glVertex3f(r1 * c, r1 * s, 0.0)
        glEnd()
    glEndList()
    return lst


def init_planets():
    """Goi 1 lan SAU khi da co OpenGL context."""
    global _sphere_list, _glow_tex, _halo_tex, _corona_tex

    rng = np.random.default_rng(7)

    q = gluNewQuadric()
    gluQuadricTexture(q, GL_TRUE)
    gluQuadricNormals(q, GLU_SMOOTH)
    _sphere_list = glGenLists(1)
    glNewList(_sphere_list, GL_COMPILE)
    gluSphere(q, 1.0, 96, 64)
    glEndList()
    gluDeleteQuadric(q)

    for key, fn in _BUILDERS.items():
        _tex[key] = _upload(fn(rng))

    _glow_tex = _radial_texture(lambda r: np.where(r < 1, np.clip(1 - r, 0, None) ** 2.4, 0))
    _halo_tex = _radial_texture(lambda r: np.exp(-((r - 0.72) / 0.10) ** 2))
    yy, xx = np.mgrid[-1:1:256j, -1:1:256j]
    r = np.hypot(xx, yy)
    angle = np.arctan2(yy, xx)
    filaments = (0.82
                 + 0.10 * np.sin(angle * 9.0 + r * 13.0)
                 + 0.08 * np.sin(angle * 19.0 - r * 21.0))
    corona = np.exp(-((r - 1.10) / 0.40) ** 2) * np.clip(filaments, 0.35, 1.0)
    corona_img = np.ones((256, 256, 4), np.float32)
    corona_img[..., 3] = np.clip(corona, 0, 1)
    _corona_tex = _upload(corona_img, mip=False, clamp_s=True)

    for p in PLANETS:
        p["tex"] = _tex[p["texture"]]
        if p.get("clouds"):
            p["clouds_tex"] = _tex["clouds"]
            p["lights_tex"] = _tex["earth_lights"]
        if p.get("moon"):
            p["moon"]["tex"] = _tex["moon"]
        if p.get("rings"):
            rg = p["rings"]
            p["ring_list"] = _build_rings(rg["kind"], rg["inner"],
                                          rg["outer"], rng)


# =====================================================================
#  VE
# =====================================================================

def _textured_sphere(tex, radius, spin=0.0):
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex)
    glColor3f(1.0, 1.0, 1.0)
    glPushMatrix()
    glRotatef(spin, 0, 0, 1)
    glScalef(radius, radius, radius)
    glCallList(_sphere_list)
    glPopMatrix()
    glDisable(GL_TEXTURE_2D)


def _draw_atmosphere(radius, color):
    """Lop mao khi trong suot: danh sang mem o ranh gioi thay vi neon deu."""
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glEnable(GL_CULL_FACE)
    glCullFace(GL_FRONT)
    glDepthMask(GL_FALSE)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, _halo_tex)
    glColor4f(*color)
    glPushMatrix()
    glScalef(radius * 1.09, radius * 1.09, radius * 1.09)
    glCallList(_sphere_list)
    glPopMatrix()
    glBindTexture(GL_TEXTURE_2D, 0)
    glDisable(GL_TEXTURE_2D)
    glDepthMask(GL_TRUE)
    glDisable(GL_CULL_FACE)
    glDisable(GL_BLEND)
    glEnable(GL_LIGHTING)


def _draw_billboard(tex, half, color):
    """Quad luon huong ve camera tai goc toa do hien tai (hao quang)."""
    m = glGetFloatv(GL_MODELVIEW_MATRIX)
    glPushMatrix()
    glLoadIdentity()
    glTranslatef(m[3][0], m[3][1], m[3][2])

    glDisable(GL_LIGHTING)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glDepthMask(GL_FALSE)
    glColor4f(*color)

    glBegin(GL_QUADS)
    glTexCoord2f(0, 0); glVertex3f(-half, -half, 0)
    glTexCoord2f(1, 0); glVertex3f(half, -half, 0)
    glTexCoord2f(1, 1); glVertex3f(half, half, 0)
    glTexCoord2f(0, 1); glVertex3f(-half, half, 0)
    glEnd()

    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_LIGHTING)
    glPopMatrix()


def draw_sun(t):
    glDisable(GL_LIGHTING)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    _textured_sphere(_tex["sun"], 1.5, t * 1.4)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glDepthMask(GL_FALSE)
    _textured_sphere(_tex["sun_flow"], 1.508, -t * 2.2)
    _textured_sphere(_tex["sun_flow"], 1.516, t * 1.1)
    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)
    glPopMatrix()

    glPushMatrix()
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glEnable(GL_CULL_FACE)
    glCullFace(GL_FRONT)
    glDepthMask(GL_FALSE)

    for scale, alpha, red, green in (
        (1.035, 0.28, 1.0, 0.58),
        (1.090, 0.18, 1.0, 0.36),
        (1.180, 0.09, 1.0, 0.20),
    ):
        glColor4f(red, green, 0.025, alpha)
        glPushMatrix()
        glScalef(scale * 1.50, scale * 1.50, scale * 1.50)
        glCallList(_sphere_list)
        glPopMatrix()
    glDepthMask(GL_TRUE)
    glDisable(GL_CULL_FACE)
    glDisable(GL_BLEND)
    glEnable(GL_LIGHTING)
    glPopMatrix()
    glEnable(GL_LIGHTING)


def _draw_moon(m, t):
    a = math.radians(t * m["speed"])
    glPushMatrix()
    glTranslatef(m["dist"] * math.cos(a), 0.0, m["dist"] * math.sin(a))
    glRotatef(-90, 1, 0, 0)
    _textured_sphere(m["tex"], m["radius"], math.degrees(a) + 180.0)
    glPopMatrix()


def _draw_rings(planet):
    glPushMatrix()
    s = planet["radius"]
    glScalef(s, s, s)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_LIGHTING)
    glDepthFunc(GL_LEQUAL)
    glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
    glCallList(planet["ring_list"])
    glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_FALSE)
    glEnable(GL_LIGHTING)
    glDepthFunc(GL_LESS)
    glDisable(GL_BLEND)
    glPopMatrix()


def planet_position(planet, t):
    """Toạ độ (x, y, z) của tâm hành tinh tại thời điểm mô phỏng t.

    Dùng chung cho vẽ hành tinh và camera bám theo nên luôn cho cùng một vị trí.
    Quỹ đạo nằm trên mặt phẳng XZ (y = 0).
    """
    ang = math.radians(planet["phase"] + t * planet["orbit_speed"])
    return orbit_position(
        planet["orbit_radius"],
        planet["orbit_eccentricity"],
        ang,
        math.radians(planet.get("orbit_omega", 0.0)),
    )

def planet_stats(planet, t):
    """(khoảng cách tới Mặt Trời [triệu km], vận tốc [km/s]) tại thời điểm mô phỏng t.

    Tỉ lệ r/a lấy từ chính quỹ đạo elip đang vẽ; vận tốc theo công thức vis-viva
    v = sqrt(GM * (2/r - 1/a)) nên nhanh ở cận nhật, chậm ở viễn nhật.
    """
    a = PLANET_INFO[planet["name"]]["a"] * 1e6            # km
    x, y, z = planet_position(planet, t)
    r = math.sqrt(x * x + y * y + z * z) / planet["orbit_radius"] * a
    v = math.sqrt(SUN_GM * (2.0 / r - 1.0 / a))
    return r / 1e6, v

def draw_planet(planet, t):
    x, y, z = planet_position(planet, t)
    r = planet["radius"]
    spin = t * planet["spin"]

    glPushMatrix()
    glTranslatef(x, y, z)

    glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, (72.0,))
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.48, 0.48, 0.52, 1.0))

    if planet.get("moon"):
        _draw_moon(planet["moon"], t)

    glRotatef(planet["tilt"], 0, 0, 1)   # nghieng truc
    glRotatef(-90, 1, 0, 0)              # cuc cua quadric -> truc Y

    _textured_sphere(planet["tex"], r, spin)

    if planet.get("clouds_tex"):
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        _textured_sphere(planet["clouds_tex"], r * 1.025, spin * 1.2)
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)

    if planet.get("lights_tex"):
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glDepthMask(GL_FALSE)
        _textured_sphere(planet["lights_tex"], r * 1.012, spin)
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    if planet.get("ring_list"):
        _draw_rings(planet)

    if planet.get("halo"):
        halo = planet["halo"]
        _draw_atmosphere(r, (halo[0], halo[1], halo[2], halo[3]))

    glPopMatrix()