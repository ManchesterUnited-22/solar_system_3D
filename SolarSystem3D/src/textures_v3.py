"""Texture cai tien: may Trai Dat, Mat Trang, Sao Hoa, Mat Troi (+sun_flow), Sao Hai Vuong.

Dung lai cac tien ich trong hand_textures.py (khong sua file do).
Quy uoc giong hand_textures: tinh toan voi hang 0 = cuc BAC, cuoi cung _finish() lat lai.
"""
import numpy as np
from hand_textures import (_smooth, _mix, _Canvas, _fbm, _noise2, _fractal, _ellipse,
                           _finish, _craters, _craters_at, _bands, _storm)


# =====================================================================
#  TIEN ICH CHUNG
# =====================================================================
def _lonlat(W, H):
    lon = ((np.arange(W, dtype=np.float32) + 0.5) / W * 360.0 - 180.0)[None, :] * np.ones((H, 1), np.float32)
    lat = (90.0 - (np.arange(H, dtype=np.float32) + 0.5) / H * 180.0)[:, None] * np.ones((1, W), np.float32)
    return lon, lat


def _warp(a, dx, dy):
    """Lay mau a (H,W) tai (x+dx, y+dy), noi suy song tuyen tinh; lap theo kinh do, kep theo vi do."""
    H, W = a.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    x = (xx + dx) % W
    y = np.clip(yy + dy, 0, H - 1.001)
    x0 = np.floor(x).astype(np.int32)
    y0 = np.floor(y).astype(np.int32)
    fx, fy = x - x0, y - y0
    x1 = (x0 + 1) % W
    y1 = np.minimum(y0 + 1, H - 1)
    top = a[y0, x0] * (1 - fx) + a[y0, x1] * fx
    bot = a[y1, x0] * (1 - fx) + a[y1, x1] * fx
    return top * (1 - fy) + bot * fy


def _blob(lon, lat, lon0, lat0, rx, ry, rot, wx, wy, warp):
    """Truong khoang cach elip (>0 ben trong), mep bi meo boi 2 truong nhieu wx, wy (-1..1)."""
    dl = (lon - lon0 + 180.0) % 360.0 - 180.0
    k = max(np.cos(np.radians(lat0)), 0.3)
    x = dl * k + wx * warp * rx
    y = (lat - lat0) + wy * warp * ry
    c, s = np.cos(np.radians(rot)), np.sin(np.radians(rot))
    u = (x * c + y * s) / rx
    v = (-x * s + y * c) / ry
    return 1.0 - np.sqrt(u * u + v * v)


def _irregular(lon, lat, spec, wlo, whi, n_mid, n_fine, warp=0.55, rough=0.75, soft=0.22):
    """Mat na 0..1 hinh dang BAT QUY TAC (nhieu thuy, vinh, dao) cho 1 vung."""
    lon0, lat0, rx, ry, rot = spec
    f = _blob(lon, lat, lon0, lat0, rx, ry, rot,
              wlo[0] * 0.7 + whi[0] * 0.5, wlo[1] * 0.7 + whi[1] * 0.5, warp)
    f = f + (n_mid - 0.5) * rough + (n_fine - 0.5) * rough * 0.45
    return _smooth(-0.04, soft, f)


# =====================================================================
#  1. MAY TRAI DAT  (RGBA: rgb trang, alpha = do day cua may)
# =====================================================================
def clouds_texture(out_w=2048, out_h=1024, seed=17):
    rng = np.random.default_rng(seed)
    W, H = out_w, out_h
    lon, lat = _lonlat(W, H)
    alat = np.abs(lat)

    # Xoay bao (cyclone): moi bao la 1 xoay quanh tam, keo noise theo dang xoan oc
    swirls = []
    for _ in range(11):
        side = rng.choice([-1, 1])
        la = side * rng.uniform(22, 58)
        swirls.append((rng.uniform(-180, 180), la, rng.uniform(9, 17), -side * rng.uniform(1.4, 2.6)))
    dxs = np.zeros((H, W), np.float32)
    dys = np.zeros((H, W), np.float32)
    px_deg = W / 360.0
    for lo, la, rad, strength in swirls:
        dl = ((lon - lo + 180.0) % 360.0 - 180.0) * max(np.cos(np.radians(la)), 0.35)
        dy = lat - la
        r = np.hypot(dl, dy) / rad
        fall = np.exp(-r * r * 1.1)
        ang = strength * fall                                 # goc xoay (rad) giam dan ra ngoai -> xoan oc
        ca, sa = np.cos(ang), np.sin(ang)
        nx = dl * ca - dy * sa - dl
        ny = dl * sa + dy * ca - dy
        dxs += (nx / max(np.cos(np.radians(la)), 0.35)) * px_deg
        dys += -ny * px_deg

    # Bien dang nhieu de may khong "tron" (domain warping)
    wa = (_fbm(rng, W, H, 6, 4) - 0.5) * 2.0
    wb = (_fbm(rng, W, H, 6, 4) - 0.5) * 2.0
    base_dx = dxs + wa * 26.0
    base_dy = dys + wb * 12.0

    def layer(cells, octs):
        return _warp(_fbm(rng, W, H, cells, octs, 0.55), base_dx, base_dy)

    big = layer(7, 5)                                      # he thong may lon
    mid = layer(22, 5)
    # soi may: noise keo dai theo kinh do (gio Tay-Dong) + ridged
    streak = _noise2(rng, W, H, 70, 26)
    streak = _warp(streak, base_dx * 0.6, base_dy * 0.6)
    ridged = 1.0 - np.abs(2.0 * _warp(_fbm(rng, W, H, 38, 4), base_dx, base_dy) - 1.0)
    detail = _fbm(rng, W, H, 120, 4)

    field = 0.50 * big + 0.28 * mid + 0.12 * streak + 0.10 * ridged
    field = (field - field.min()) / (field.max() - field.min() + 1e-9)

    # Do phu may theo vi do: ITCZ day o xich dao, vung kho ~25 do, dai bao ~50-60 do, it may o cuc
    cover = (0.46
             + 0.22 * np.exp(-(lat / 7.0) ** 2)
             - 0.20 * np.exp(-((alat - 24.0) / 9.0) ** 2)
             + 0.16 * np.exp(-((alat - 55.0) / 11.0) ** 2)
             - 0.10 * _smooth(75.0, 90.0, alat))
    # Vung tam bao: may day dac
    for lo, la, rad, _s in swirls:
        dl = ((lon - lo + 180.0) % 360.0 - 180.0) * max(np.cos(np.radians(la)), 0.35)
        r = np.hypot(dl, lat - la) / rad
        cover = cover + 0.30 * np.exp(-r * r * 0.9)
    # Nguong theo do phu: vung cover cao -> nhieu may hon
    d = field + (cover - 0.5) * 0.85 - np.quantile(field, 0.44)
    alpha = _smooth(0.0, 0.14, d)                         # mep sac hon (khong con mep mo ban dau)
    # Do day: loi may day thi trang hon, mong thi trong suot
    thick = _smooth(0.04, 0.30, d)
    alpha = np.clip(alpha * (0.74 + 0.30 * thick) * (0.90 + 0.18 * detail), 0, 0.97)
    # Vi mo sau: cac soi nho cat vao mep
    alpha *= 0.88 + 0.22 * _smooth(0.35, 0.75, detail)
    alpha = np.clip(alpha, 0, 0.97)

    shade = 0.80 + 0.20 * thick + 0.05 * (detail - 0.5)    # may mong hoi xam
    rgb = np.clip(shade, 0, 1)[..., None] * np.array([1.0, 1.0, 1.0], np.float32)
    rgb = rgb * np.array([1.0, 1.0, 1.02], np.float32)
    img = np.concatenate([rgb, alpha[..., None]], axis=2).astype(np.float32)
    return _finish(img)


# =====================================================================
#  2. MAT TRANG  (bien xam nau, hinh dang bat quy tac)
# =====================================================================
# (kinh do, vi do, rx, ry, xoay, do dam, sac nau 0..1)
MOON_MARIA_V3 = [
    (-17, 33, 17, 12, 0, 0.92, 0.2),   # Imbrium
    (-55, 15, 12, 22, 8, 0.80, 0.5),   # Oceanus Procellarum
    (18, 28, 8, 7, 0, 0.90, 0.1),      # Serenitatis
    (31, 8, 10, 7, 20, 0.88, 0.9),     # Tranquillitatis
    (51, -4, 6, 8, 0, 0.85, 0.3),      # Fecunditatis
    (59, 17, 5, 4, 0, 0.88, 0.2),      # Crisium
    (34, -15, 4.5, 4.5, 0, 0.70, 0.5), # Nectaris
    (-15, -21, 9, 6, 0, 0.80, 0.6),    # Nubium
    (-39, -24, 5, 5, 0, 0.78, 0.7),    # Humorum
    (3, 13, 4.5, 3.5, 0, 0.80, 0.5),   # Vapores
    (-23, -10, 6, 4, 0, 0.72, 0.6),    # Insularum
    (-8, 2, 3.5, 3.5, 0, 0.70, 0.4),   # Sinus Medii
    (-40, 42, 6, 4, 0, 0.75, 0.2),     # Tay Bac Imbrium
    (87, 2, 4, 3, 0, 0.75, 0.6),       # Smythii
    (86, 13, 3.5, 2.5, 0, 0.60, 0.5),  # Marginis
    (147, 27, 5, 4, 0, 0.65, 0.5),     # Moscoviense
    (-95, -19, 5, 5, 0, 0.65, 0.6),    # Orientale
]
# Mare Frigoris: day dut doan, khong con "vet dai" lien tuc
MOON_FRIGORIS = [(-42, 57, 5.0, 2.6, 6), (-18, 60, 4.0, 2.2, -4), (4, 59, 4.5, 2.4, 3),
                 (28, 57, 3.5, 2.0, -8)]
MOON_BIG_CRATERS_V3 = [
    (-11.4, -43.3, 2.6, 28), (-20, 9.6, 1.6, 20), (-38, 8, 1.5, 12), (-47, 23.7, 0.9, 14),
    (-9, -26, 2.0, 0), (24, 4, 1.0, 0), (-3, 42, 1.2, 0),
]


def moon_texture(out_w=2048, out_h=1024, seed=3):
    rng = np.random.default_rng(seed)
    W, H = out_w, out_h
    cv = _Canvas(W, H)
    lon, lat = _lonlat(W, H)
    n_big = _fbm(rng, W, H, 8, 5)
    n_mid, n_fine = _fbm(rng, W, H, 34, 4), _fbm(rng, W, H, 170, 3)
    wlo = ((_fbm(rng, W, H, 12, 4) - 0.5) * 2.0, (_fbm(rng, W, H, 12, 4) - 0.5) * 2.0)
    whi = ((_fbm(rng, W, H, 36, 4) - 0.5) * 2.0, (_fbm(rng, W, H, 36, 4) - 0.5) * 2.0)

    # Cao nguyen: xam sang, hoi am (khong lanh)
    img = _mix((0.52, 0.50, 0.47), (0.78, 0.76, 0.72), n_big * 0.8 + n_mid * 0.2)

    mare_total = np.zeros((H, W), np.float32)
    tint_acc = np.zeros((H, W), np.float32)
    for lo, la, rx, ry, rot, dens, tint in MOON_MARIA_V3:
        m = _irregular(lon, lat, (lo, la, rx * 1.3, ry * 1.3, rot), wlo, whi, n_mid, n_fine) * dens
        tint_acc = np.maximum(tint_acc, m * tint)
        mare_total = np.maximum(mare_total, m)
    for lo, la, rx, ry, rot in MOON_FRIGORIS:
        m = _irregular(lon, lat, (lo, la, rx, ry, rot), wlo, whi, n_mid, n_fine, warp=0.9, rough=1.0) * 0.45
        tint_acc = np.maximum(tint_acc, m * 0.2)
        mare_total = np.maximum(mare_total, m)

    # Mau bien: xam nau (khong den). Mot so bien nau hon, mot so xam xanh hon.
    mare_a = _mix((0.34, 0.29, 0.23), (0.47, 0.40, 0.32), n_mid)          # nau
    mare_b = _mix((0.31, 0.29, 0.26), (0.43, 0.40, 0.36), n_mid)          # xam xanh
    tint_k = np.clip(tint_acc / np.maximum(mare_total, 1e-3), 0, 1)
    mare_col = _mix(mare_b, mare_a, tint_k)
    img = _mix(img, mare_col, mare_total * 0.88)
    img *= (0.90 + 0.20 * n_fine)[..., None]

    _craters(img, rng, 3200, 0.22, 3.6, 0.20, 0.09)

    # Tia sang tu ho lon
    ray = np.zeros((H, W), np.float32)
    for lo, la, r, rays in MOON_BIG_CRATERS_V3:
        for _ in range(rays):
            a = rng.uniform(0, 2 * np.pi)
            L = rng.uniform(8, 32) if rays > 15 else rng.uniform(5, 14)
            p = [(lo, la), (lo + np.cos(a) * L / max(np.cos(np.radians(la)), 0.3), la + np.sin(a) * L)]
            ray = np.maximum(ray, cv.layer(lines=[(p, 0.35)], blur=1.2) * rng.uniform(0.4, 1.0))
    img = _mix(img, (0.88, 0.87, 0.83), ray * 0.45)
    for lo, la, r, _ in MOON_BIG_CRATERS_V3:
        for k in (0, 1):
            _craters_at(img, lo, la, r * (1.0 - 0.3 * k), 0.30 if k == 0 else 0.0, 0.22)
    return _finish(img)


# =====================================================================
#  3. SAO HOA  (vung toi/sang bat quy tac + Valles Marineris + nui lua)
# =====================================================================
# (kinh do, vi do, rx, ry, xoay, do dam)
MARS_DARK_V3 = [
    (69, 9, 7, 16, -10, 0.95),   # Syrtis Major
    (-25, 48, 26, 12, 0, 0.75),  # Acidalia
    (-150, -30, 26, 7, 0, 0.85), # Sirenum
    (-145, -22, 18, 6, 0, 0.75),
    (-90, -26, 9, 6, 0, 0.85),
    (0, -3, 10, 4, 0, 0.80),     # Sinus Meridiani
    (-20, -8, 18, 4, 0, 0.75),
    (105, -15, 15, 8, 0, 0.70),
    (110, -22, 14, 4, 0, 0.70),
    (110, 48, 25, 12, 0, 0.60),
    (160, 22, 12, 7, 0, 0.45),
]
MARS_LIGHT_V3 = [
    (70, -42, 14, 10, 0, (0.92, 0.76, 0.60)),   # Hellas
    (-43, -50, 8, 6, 0, (0.95, 0.88, 0.80)),    # Argyre
    (20, 20, 22, 12, 0, (0.88, 0.58, 0.36)),    # Arabia
    (-155, 20, 16, 10, 0, (0.90, 0.68, 0.46)),  # Elysium nen
]
# (kinh do, vi do, ban kinh do, cao)
MARS_VOLCANOES = [
    (-134, 18.6, 3.8, 1.0),    # Olympus Mons
    (-121, -9.0, 2.2, 0.55),   # Arsia
    (-113, 1.0, 1.8, 0.50),    # Pavonis
    (-104, 11.0, 2.0, 0.55),   # Ascraeus
    (147, 24.0, 2.6, 0.35),    # Elysium Mons
]


def mars_texture(out_w=2048, out_h=1024, seed=21):
    rng = np.random.default_rng(seed)
    W, H = out_w, out_h
    cv = _Canvas(W, H)
    lon, lat = _lonlat(W, H)
    alat = np.abs(lat)
    ppd = W / 360.0
    n_big, n_mid, n_fine = _fbm(rng, W, H, 9, 5), _fbm(rng, W, H, 50, 4), _fbm(rng, W, H, 220, 3)
    wlo = ((_fbm(rng, W, H, 12, 4) - 0.5) * 2.0, (_fbm(rng, W, H, 12, 4) - 0.5) * 2.0)
    whi = ((_fbm(rng, W, H, 34, 4) - 0.5) * 2.0, (_fbm(rng, W, H, 34, 4) - 0.5) * 2.0)

    img = _mix((0.60, 0.31, 0.16), (0.84, 0.50, 0.28), 0.55 * n_big + 0.45 * n_mid)

    # Vung sang (bui): bat quy tac
    for lo, la, rx, ry, rot, col in MARS_LIGHT_V3:
        m = _irregular(lon, lat, (lo, la, rx, ry, rot), wlo, whi, n_mid, n_fine, warp=0.6, rough=0.7)
        img = _mix(img, col, m * 0.80)

    # Vung toi (albedo): bat quy tac + dom keo dai do gio
    streak = _noise2(rng, W, H, 160, 60)
    dark_all = np.zeros((H, W), np.float32)
    for lo, la, rx, ry, rot, k in MARS_DARK_V3:
        m = _irregular(lon, lat, (lo, la, rx, ry, rot), wlo, whi, n_mid, n_fine, warp=0.75, rough=0.85)
        dark_all = np.maximum(dark_all, m * k)
    dark_all *= 0.85 + 0.30 * streak
    img = _mix(img, _mix((0.27, 0.15, 0.10), (0.47, 0.27, 0.18), n_fine), np.clip(dark_all, 0, 1))

    # Vastitas Borealis (dong bang toi phia bac)
    img = _mix(img, (0.40, 0.25, 0.18), _smooth(52, 68, lat + (n_mid - 0.5) * 10) * _smooth(88, 80, alat) * 0.55)

    # ---- Cao do gia lap: Tharsis (vung phong) + nui lua -> do bong ----
    height = np.zeros((H, W), np.float32)
    dl = ((lon + 105 + 180.0) % 360.0 - 180.0)
    height += 0.35 * np.exp(-((dl / 28.0) ** 2 + ((lat - 4.0) / 22.0) ** 2))
    for lo, la, r, h in MARS_VOLCANOES:
        d = np.hypot(((lon - lo + 180.0) % 360.0 - 180.0) * max(np.cos(np.radians(la)), 0.4), lat - la) / r
        cone = np.exp(-(d * 0.9) ** 3.0) * h
        caldera = np.exp(-(d / 0.30) ** 2) * h * 0.25
        height += cone - caldera
    sx = np.gradient(height, axis=1)
    sy = np.gradient(height, axis=0)
    shade = np.clip((-sx * 0.8 + sy * 0.6) * 26.0, -0.35, 0.35)     # anh sang tu Tay Bac
    img = img * (1.0 + shade)[..., None]
    for lo, la, r, h in MARS_VOLCANOES:                           # sap mau nhat (bui) tren than nui
        d = np.hypot(((lon - lo + 180.0) % 360.0 - 180.0) * max(np.cos(np.radians(la)), 0.4), lat - la) / r
        img = _mix(img, (0.84, 0.58, 0.40), np.exp(-(d * 1.2) ** 3.0) * 0.08 * h)
        img = _mix(img, (0.30, 0.16, 0.11), np.exp(-(d / 0.25) ** 2) * 0.35 * h)   # mieng nui lua

    # ---- Valles Marineris: he thong hem nui chinh + nhanh phu + Noctis Labyrinthus ----
    main = [(-92, -7), (-86, -9.5), (-80, -11.5), (-73, -12.5), (-66, -13), (-59, -12), (-53, -9.5)]
    trenches = [
        _fractal(main, rng, 3, 0.05, False),
        _fractal([(-90, -9.5), (-82, -8.4), (-74, -9.0), (-66, -8.8), (-60, -8.0)], rng, 3, 0.05, False),
        _fractal([(-86, -14), (-78, -15.2), (-70, -15), (-62, -14)], rng, 3, 0.05, False),
        _fractal([(-79, -9), (-78, -4.5), (-76, -3), (-71, -2.5)], rng, 3, 0.15, False),   # Ophir / Candor
        _fractal([(-103, -6.5), (-97, -7.8), (-92, -7)], rng, 3, 0.18, False),             # Noctis
        _fractal([(-98, -4), (-94, -6.5)], rng, 2, 0.20, False),
        _fractal([(-55, -9), (-50, -8), (-46, -6.5)], rng, 3, 0.15, False),                # Chryse
    ]
    canyon = cv.layer(lines=[(t, 2.3) for t in trenches[:1]] +
                           [(t, 1.3) for t in trenches[1:3]] + [(t, 1.0) for t in trenches[3:]],
                      blur=0.4 * ppd)
    canyon = np.clip(canyon * (0.8 + 0.5 * n_fine), 0, 1)
    wall = np.clip(cv.layer(lines=[(t, 5.0) for t in trenches[:3]], blur=1.4 * ppd) - canyon * 0.6, 0, 1)
    img = _mix(img, (0.66, 0.40, 0.26), wall * 0.45)         # vach hem nui sang hon
    img = _mix(img, (0.30, 0.14, 0.09), np.clip(canyon * 1.3, 0, 1) * 0.92)       # long hem nui sam mau

    img *= (0.90 + 0.20 * n_fine)[..., None]
    _craters(img, rng, 1700, 0.25, 3.5, 0.18, 0.07)

    # Chom bang cuc, vanh toi quanh chom Bac
    edge = (n_mid - 0.5) * 6.0
    img = _mix(img, (0.34, 0.22, 0.17), np.exp(-((lat - 80.0 + edge) / 2.0) ** 2) * 0.5)
    cap_n = _smooth(83.0, 85.5, lat + edge)
    cap_s = _smooth(-81.5, -84.0, lat - edge)
    img = _mix(img, (0.96, 0.96, 0.98), np.clip(cap_n + cap_s, 0, 1))
    return _finish(img)


# =====================================================================
#  4. MAT TROI  (quang quyen vang trang + hat granulation + vet den)
# =====================================================================
def _cells(rng, W, H, gx, gy):
    """Cellular (Worley) noise khop kin theo chieu ngang. Tra ve (f1, f2, id ngau nhien cua o gan nhat)."""
    pts_x = rng.random((gy, gx)).astype(np.float32)
    pts_y = rng.random((gy, gx)).astype(np.float32)
    cid = rng.random((gy, gx)).astype(np.float32)
    px = (np.arange(W, dtype=np.float32) + 0.5) / W * gx
    py = (np.arange(H, dtype=np.float32) + 0.5) / H * gy
    cx0 = np.floor(px).astype(np.int32)[None, :]
    cy0 = np.floor(py).astype(np.int32)[:, None]
    f1 = np.full((H, W), 9.0, np.float32)
    f2 = np.full((H, W), 9.0, np.float32)
    ident = np.zeros((H, W), np.float32)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            cx = (cx0 + ox) % gx
            cyr = cy0 + oy
            cyc = np.clip(cyr, 0, gy - 1)
            fx = (cx0 + ox) + pts_x[cyc, cx]
            fy = cyr + pts_y[cyc, cx]
            d = np.hypot(px[None, :] - fx, py[:, None] - fy).astype(np.float32)
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))
            ident = np.where(closer, cid[cyc, cx], ident)
            f1 = np.where(closer, d, f1)
    return f1, f2, ident


def sun_texture(out_w=2048, out_h=1024, seed=7):
    rng = np.random.default_rng(seed)
    W, H = out_w, out_h
    lon, lat = _lonlat(W, H)

    # Hat granulation: nhieu o nho, ranh gioi (f2-f1) la vach toi
    f1, f2, ident = _cells(rng, W, H, 300, 150)
    lane = _smooth(0.0, 0.30, f2 - f1)                       # 0 ngoai ranh, 1 giua hat
    g2a, g2b, g2id = _cells(rng, W, H, 70, 35)                # sieu hat (lon hon, mo hon)
    sup = _smooth(0.0, 0.5, g2b - g2a)
    n_big = _fbm(rng, W, H, 6, 5)
    n_fine = _fbm(rng, W, H, 260, 3)

    bright = 0.55 * lane + 0.25 * ident + 0.12 * sup + 0.08 * n_fine
    bright = (bright - bright.min()) / (bright.max() - bright.min() + 1e-9)

    # Mau: vang trang. Vach toi hoi cam, tam hat vang trang.
    lane_col = np.array([0.92, 0.64, 0.28], np.float32)
    mid_col = np.array([1.00, 0.90, 0.58], np.float32)
    hot_col = np.array([1.00, 0.96, 0.78], np.float32)
    img = _mix(lane_col, mid_col, _smooth(0.15, 0.55, bright))
    img = _mix(img, hot_col, _smooth(0.55, 0.95, bright))
    img = img * (0.94 + 0.08 * n_big)[..., None]

    # Vet den (cap, o vi do ~ +-8..20 do) + penumbra + faculae sang xung quanh
    spots = [(-150, 14, 3.6), (-142, 12, 1.8), (-60, -13, 3.2), (-53, -15, 1.6),
             (35, 10, 4.2), (45, 12, 2.0), (120, -9, 2.8), (128, -11, 1.5), (-100, 18, 1.8)]
    for lo, la, r in spots:
        dl = ((lon - lo + 180.0) % 360.0 - 180.0) * max(np.cos(np.radians(la)), 0.5)
        warp = (n_fine - 0.5) * 0.35 + (n_big - 0.5) * 0.4
        d = np.hypot(dl, (lat - la) * 1.15) / r + warp
        fac = np.exp(-((d - 1.9) / 1.2) ** 2) * 0.22
        img = _mix(img, (1.0, 0.97, 0.82), np.clip(fac, 0, 1))
        pen = _smooth(1.9, 1.0, d)
        img = _mix(img, (0.50, 0.24, 0.07), pen * 0.88)
        umb = _smooth(0.95, 0.45, d)
        img = _mix(img, (0.10, 0.04, 0.02), umb * 0.95)
    return _finish(img)


def sun_flow_texture(out_w=1024, out_h=512, seed=23):
    """Lop trong suot cong them (additive) tao hieu ung dong plasma lap lanh tren quang quyen."""
    rng = np.random.default_rng(seed)
    W, H = out_w, out_h
    f1, f2, ident = _cells(rng, W, H, 160, 80)
    lane = _smooth(0.0, 0.35, f2 - f1)
    wa = (_fbm(rng, W, H, 10, 4) - 0.5) * 2.0
    wb = (_fbm(rng, W, H, 10, 4) - 0.5) * 2.0
    pat = _warp(0.6 * lane + 0.4 * ident, wa * 14.0, wb * 8.0)
    mid = _fbm(rng, W, H, 18, 5)
    flow = np.clip(0.6 * pat + 0.4 * mid, 0, 1)
    flow = (flow - flow.min()) / (flow.max() - flow.min() + 1e-9)
    alpha = 0.10 + 0.32 * _smooth(0.35, 0.90, flow)           # phu kin be mat, day dac hon so voi ban cu
    col = _mix((1.0, 0.62, 0.18), (1.0, 0.92, 0.55), _smooth(0.3, 0.9, flow))
    img = np.concatenate([col, alpha[..., None]], axis=2).astype(np.float32)
    return _finish(img)


# =====================================================================
#  5. SAO HAI VUONG  (dai mem, khong con soc deu nhu ton)
# =====================================================================
NEPTUNE_BANDS = [   # (vi do, mau): tuong phan thap, khoang cach khong deu
    (-90, (0.15, 0.29, 0.70)), (-72, (0.20, 0.36, 0.80)), (-58, (0.17, 0.32, 0.75)),
    (-44, (0.26, 0.45, 0.89)), (-33, (0.19, 0.35, 0.80)), (-21, (0.14, 0.27, 0.69)),
    (-9, (0.21, 0.39, 0.84)), (2, (0.24, 0.42, 0.87)), (13, (0.18, 0.33, 0.77)),
    (27, (0.22, 0.39, 0.83)), (41, (0.19, 0.35, 0.78)), (58, (0.21, 0.38, 0.82)),
    (74, (0.17, 0.32, 0.76)), (90, (0.14, 0.27, 0.68)),
]


def neptune_texture(out_w=2048, out_h=1024, seed=51):
    rng = np.random.default_rng(seed)
    W, H = out_w, out_h
    cv = _Canvas(W, H)
    lon, lat = _lonlat(W, H)
    img, _lat, _lon = _bands(rng, W, H, NEPTUNE_BANDS, warp=3.6, streak=0.035)
    # Phan bo mem: mang loang nhe, de khong thanh soc deu
    n_big, n_mid = _fbm(rng, W, H, 7, 5), _fbm(rng, W, H, 28, 4)
    img = img * (0.93 + 0.14 * n_big)[..., None]
    img = _mix(img, (0.30, 0.50, 0.95), _smooth(0.55, 0.9, n_mid) * 0.18)

    # Great Dark Spot + may dong hanh sang
    _storm(img, cv, rng, 40, -22, 11, 5.5, (0.08, 0.15, 0.50), (0.12, 0.23, 0.62), 1.8)
    _storm(img, cv, rng, 62, -28, 4.5, 1.5, (0.90, 0.94, 1.0), None, 0.5)       # scooter
    _storm(img, cv, rng, -60, -62, 6, 3.0, (0.08, 0.15, 0.50), None, 1.0)       # dom toi phu
    # Soi may trang ngan, keo theo kinh tuyen o dai -45..-25
    st = _noise2(rng, W, H, 34, 130)                       # keo dai ngang -> soi may manh
    st2 = _noise2(rng, W, H, 44, 110)
    streak = _smooth(0.60, 0.80, st) * np.exp(-((lat + 33.0) / 8.0) ** 2)
    streak += _smooth(0.64, 0.82, st2) * np.exp(-((lat - 20.0) / 5.0) ** 2) * 0.6
    img = _mix(img, (0.88, 0.94, 1.0), np.clip(streak, 0, 1) * 0.40)
    return _finish(img)