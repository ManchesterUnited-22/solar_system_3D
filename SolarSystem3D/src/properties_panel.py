"""Bảng Properties vẽ bằng OpenGL (không cần thư viện giao diện ngoài).

Gồm 2 tab:
    0 = SHOW AXES : hiện hệ trục XYZ, ẩn quỹ đạo và vành đai thiên thạch
    1 = HIDE AXES : không hiện trục, hiện quỹ đạo và vành đai thiên thạch
Toạ độ trong file này tính theo pixel cửa sổ, gốc ở góc trái trên.
"""
import math
from OpenGL.GL import *

PANEL_X, PANEL_Y = 12, 12
PANEL_W = 270
TITLE_H = 32
TAB_H = 32
LINE_H = 24
PAD = 12
SCALE = 2                      # mỗi ô của font 5x7 = 2x2 pixel

TAB_NAMES = ("SHOW AXES", "HIDE AXES")

WHITE = (1.0, 1.0, 1.0)
GRAY = (0.72, 0.76, 0.85)
RED = (1.0, 0.30, 0.30)
GREEN = (0.35, 0.95, 0.35)
BLUE = (0.40, 0.60, 1.0)

# Nội dung (chữ, màu, có vẽ mẫu màu hay không) của từng tab
TAB_CONTENT = {
    0: [("X AXIS", RED, True),
        ("Y AXIS", GREEN, True),
        ("Z AXIS", BLUE, True),
        ("ORIGIN: SUN", GRAY, False),
        ("ORBITS: OFF", GRAY, False),
        ("BELT: OFF", GRAY, False)],
    1: [("NO AXES", GRAY, False),
        ("ORBITS: ON", GRAY, False),
        ("ASTEROID BELT: ON", GRAY, False)],
}

# ---------------------------------------------------------------------
#  Font bitmap 5x7 (chỉ chữ in hoa và vài ký hiệu)
# ---------------------------------------------------------------------
FONT = {
    "A": [" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
    "B": ["#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "],
    "C": [" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"],
    "D": ["#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "],
    "E": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"],
    "F": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "],
    "G": [" ####", "#    ", "#    ", "# ###", "#   #", "#   #", " ####"],
    "H": ["#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
    "I": ["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"],
    "J": ["  ###", "    #", "    #", "    #", "    #", "#   #", " ### "],
    "K": ["#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"],
    "L": ["#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"],
    "M": ["#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"],
    "N": ["#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"],
    "O": [" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "P": ["#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "],
    "Q": [" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"],
    "R": ["#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"],
    "S": [" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "],
    "U": ["#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "V": ["#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "],
    "W": ["#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"],
    "X": ["#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"],
    "Y": ["#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "],
    "Z": ["#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"],
    ":": ["     ", "  #  ", "  #  ", "     ", "  #  ", "  #  ", "     "],
    "+": ["     ", "  #  ", "  #  ", "#####", "  #  ", "  #  ", "     "],
    "-": ["     ", "     ", "     ", "#####", "     ", "     ", "     "],
    ".": ["     ", "     ", "     ", "     ", "     ", " ##  ", " ##  "],
    "0": [" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "],
    "1": ["  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "],
    "2": [" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"],
    "3": ["#### ", "    #", "    #", " ### ", "    #", "    #", "#### "],
    "4": ["   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "],
    "5": ["#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "],
    "6": ["  ## ", " #   ", "#    ", "#### ", "#   #", "#   #", " ### "],
    "7": ["#####", "    #", "   # ", "  #  ", " #   ", " #   ", " #   "],
    "8": [" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "],
    "9": [" ### ", "#   #", "#   #", " ####", "    #", "   # ", " ##  "],
    " ": ["     "] * 7,
}


def _text_width(text, scale=SCALE):
    return len(text) * 6 * scale - scale


def _rect(x, y, w, h, color, alpha=1.0):
    glColor4f(color[0], color[1], color[2], alpha)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()


def _text(x, y, text, color, scale=SCALE):
    glColor4f(color[0], color[1], color[2], 1.0)
    glBegin(GL_QUADS)
    for i, ch in enumerate(text.upper()):
        rows = FONT.get(ch, FONT[" "])
        ox = x + i * 6 * scale
        for r, row in enumerate(rows):
            for c, px in enumerate(row):
                if px == "#":
                    x0 = ox + c * scale
                    y0 = y + r * scale
                    glVertex2f(x0, y0)
                    glVertex2f(x0 + scale, y0)
                    glVertex2f(x0 + scale, y0 + scale)
                    glVertex2f(x0, y0 + scale)
    glEnd()


# ---------------------------------------------------------------------
#  Bố cục và tương tác
# ---------------------------------------------------------------------

def panel_rect(tab):
    lines = len(TAB_CONTENT[tab])
    h = TITLE_H + TAB_H + PAD + lines * LINE_H + PAD
    return PANEL_X, PANEL_Y, PANEL_W, h


def hit_test(x, y, tab):
    """None: ngoài bảng | 0 / 1: bấm vào tab tương ứng | -1: bấm vào nền bảng."""
    px, py, pw, ph = panel_rect(tab)
    if not (px <= x <= px + pw and py <= y <= py + ph):
        return None
    ty = py + TITLE_H
    if ty <= y < ty + TAB_H:
        return 0 if x < px + pw / 2 else 1
    return -1


def _begin_2d(win_w, win_h):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, win_w, win_h, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


def _end_2d():
    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)

    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()


def draw_panel(tab, win_w, win_h):
    """Vẽ bảng Properties lên trên cùng khung hình (gọi sau khi vẽ xong cảnh 3D)."""
    _begin_2d(win_w, win_h)
    px, py, pw, ph = panel_rect(tab)

    # Nền + viền
    _rect(px, py, pw, ph, (0.05, 0.06, 0.09), 0.88)
    _rect(px, py, pw, TITLE_H, (0.14, 0.16, 0.22), 0.95)
    glColor4f(0.35, 0.40, 0.55, 1.0)
    glLineWidth(1.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(px, py)
    glVertex2f(px + pw, py)
    glVertex2f(px + pw, py + ph)
    glVertex2f(px, py + ph)
    glEnd()

    # Tiêu đề
    _text(px + PAD, py + (TITLE_H - 7 * SCALE) / 2, "PROPERTIES", WHITE)

    # Hai tab
    ty = py + TITLE_H
    tw = pw / 2
    for i, name in enumerate(TAB_NAMES):
        tx = px + i * tw
        active = (i == tab)
        if active:
            _rect(tx, ty, tw, TAB_H, (0.18, 0.34, 0.60), 1.0)
            _rect(tx, ty + TAB_H - 3, tw, 3, (0.45, 0.75, 1.0), 1.0)
        else:
            _rect(tx, ty, tw, TAB_H, (0.11, 0.12, 0.17), 1.0)
        color = WHITE if active else GRAY
        _text(tx + (tw - _text_width(name)) / 2,
              ty + (TAB_H - 7 * SCALE) / 2 - (1 if active else 0),
              name, color)

    # Nội dung của tab
    cy = ty + TAB_H + PAD
    for text, color, swatch in TAB_CONTENT[tab]:
        tx = px + PAD
        if swatch:
            _rect(tx, cy + 5, 22, 4, color, 1.0)
            tx += 32
        _text(tx, cy, text, color)
        cy += LINE_H

    _end_2d()

# ---------------------------------------------------------------------
#  Bảng thông tin hành tinh đang được chọn (nằm ngay dưới bảng Properties)
# ---------------------------------------------------------------------
INFO_GAP = 10
_COORD_ROWS = (("X", RED), ("Y", GREEN), ("Z", BLUE))


def _info_lines(paused):
    """Số dòng nội dung: đang chạy -> 3 dòng gợi ý; đang dừng -> X, Y, Z + 2 dòng phím."""
    return 5 if paused else 3


def info_panel_rect(tab, paused):
    _, py, _, ph = panel_rect(tab)
    h = TITLE_H + PAD + _info_lines(paused) * LINE_H + PAD
    return PANEL_X, py + ph + INFO_GAP, PANEL_W, h


def hit_test_info(x, y, tab, paused):
    """True nếu con trỏ nằm trong bảng thông tin (để không xoay camera / bỏ chọn)."""
    px, py, pw, ph = info_panel_rect(tab, paused)
    return px <= x <= px + pw and py <= y <= py + ph


def _fmt(v):
    return "%+.2f" % (0.0 if abs(v) < 0.005 else v)


def draw_info_panel(name, pos, paused, tab, win_w, win_h):
    """Tên hành tinh; khi đang dừng (PAUSED) hiện toạ độ x, y, z hiện tại."""
    _begin_2d(win_w, win_h)
    px, py, pw, ph = info_panel_rect(tab, paused)

    _rect(px, py, pw, ph, (0.05, 0.06, 0.09), 0.88)
    _rect(px, py, pw, TITLE_H, (0.14, 0.16, 0.22), 0.95)
    glColor4f(0.35, 0.40, 0.55, 1.0)
    glLineWidth(1.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(px, py)
    glVertex2f(px + pw, py)
    glVertex2f(px + pw, py + ph)
    glVertex2f(px, py + ph)
    glEnd()

    ty = py + (TITLE_H - 7 * SCALE) / 2
    _text(px + PAD, ty, name, WHITE)
    status = "PAUSED" if paused else "LIVE"
    _text(px + pw - PAD - _text_width(status), ty, status,
          (1.0, 0.82, 0.35) if paused else GRAY)

    cy = py + TITLE_H + PAD
    if paused:
        for (axis, color), v in zip(_COORD_ROWS, pos):
            _rect(px + PAD, cy + 5, 22, 4, color, 1.0)
            _text(px + PAD + 32, cy, "%s: %s" % (axis, _fmt(v)), WHITE)
            cy += LINE_H
        _text(px + PAD, cy, "SPACE: RESUME", GRAY)
        cy += LINE_H
        _text(px + PAD, cy, "ESC: BACK", GRAY)
    else:
        _text(px + PAD, cy, "PAUSE (SPACE) TO", GRAY)
        cy += LINE_H
        _text(px + PAD, cy, "READ COORDINATES", GRAY)
        cy += LINE_H
        _text(px + PAD, cy, "ESC: BACK", GRAY)

    _end_2d()


def draw_value_tags(tags, win_w, win_h, scale=SCALE):
    """Nhãn nhỏ cạnh một điểm trên màn hình. tags: [(x, y, chữ, màu)], x/y theo
    toạ độ cửa sổ (gốc ở góc trái trên), là vị trí điểm cần gắn nhãn.
    scale: cỡ chữ (mặc định SCALE). Nhãn chồng lên nhau được đẩy xuống để vẫn đọc được."""
    h = 7 * scale + 8
    placed = []                                  # các hình chữ nhật đã đặt (x, y, w, h)
    laid_out = []
    for x, y, text, color in tags:
        w = _text_width(text, scale) + 10
        tx, ty = x + 12, y - h - 6               # chếch lên phía trên bên phải điểm
        moved = True
        while moved:                             # đẩy xuống tới khi hết đè nhãn khác
            moved = False
            for ox, oy, ow, oh in placed:
                if tx < ox + ow and ox < tx + w and ty < oy + oh and oy < ty + h:
                    ty = oy + oh + 3
                    moved = True
        placed.append((tx, ty, w, h))
        laid_out.append((tx, ty, w, text, color))

    _begin_2d(win_w, win_h)
    for tx, ty, w, text, color in laid_out:
        _rect(tx, ty, w, h, (0.05, 0.06, 0.09), 0.92)
        _rect(tx, ty, 3, h, color, 1.0)          # vạch màu bên trái
        _text(tx + 7, ty + 4, text, color, scale)
    _end_2d()


def _disc(cx, cy, r, color, segments=28):
    """Hình tròn đặc (toạ độ cửa sổ), dùng GL_TRIANGLE_FAN nên luôn tròn."""
    glColor3f(color[0], color[1], color[2])
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)
    for i in range(segments + 1):
        a = 2.0 * math.pi * i / segments
        glVertex2f(cx + r * math.cos(a), cy + r * math.sin(a))
    glEnd()


def draw_center_markers(markers, win_w, win_h, core=(1.0, 1.0, 1.0), scale=3):
    """Đánh dấu tâm hành tinh: chấm tròn (viền màu + lõi) và chữ cái cạnh đó.
    markers: [(x, y, chữ, màu)], x/y theo toạ độ cửa sổ (gốc ở góc trái trên)."""
    _begin_2d(win_w, win_h)
    for x, y, text, color in markers:
        _disc(x, y, 8.5, color)
        _disc(x, y, 4.5, core)
        tx, ty = x + 13, y + 5               # chữ nằm chếch xuống dưới bên phải
        w = _text_width(text, scale)
        _rect(tx - 4, ty - 3, w + 8, 7 * scale + 6, (0.05, 0.06, 0.09), 0.85)
        _text(tx, ty, text, color, scale)
    _end_2d()