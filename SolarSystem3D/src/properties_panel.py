"""Bảng Properties vẽ bằng OpenGL (không cần thư viện giao diện ngoài).

Gồm 2 tab:
    0 = SHOW AXES : hiện hệ trục XYZ, ẩn quỹ đạo và vành đai thiên thạch
    1 = HIDE AXES : không hiện trục, hiện quỹ đạo và vành đai thiên thạch
Toạ độ trong file này tính theo pixel cửa sổ, gốc ở góc trái trên.
"""
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


def draw_panel(tab, win_w, win_h):
    """Vẽ bảng Properties lên trên cùng khung hình (gọi sau khi vẽ xong cảnh 3D)."""
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

    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)

    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()