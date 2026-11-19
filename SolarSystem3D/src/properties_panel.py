"""Hộp thông tin hành tinh đang được chọn (vẽ 2D bằng OpenGL, không cần thư viện ngoài).

Toạ độ trong file này tính theo pixel cửa sổ, gốc ở góc trái trên.
"""
from OpenGL.GL import *

PANEL_X, PANEL_Y = 12, 12
PANEL_W = 360
TITLE_H = 44
ROW_H = 22
PAD = 14
SCALE = 2                      # mỗi ô của font 5x7 = 2x2 pixel (chữ thường)
TITLE_SCALE = 3                # tên hành tinh to hơn

WHITE = (1.0, 1.0, 1.0)
LABEL = (0.62, 0.68, 0.82)

# ---------------------------------------------------------------------
#  Font bitmap 5x7 (chỉ chữ in hoa, số và vài ký hiệu)
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
    "/": ["    #", "    #", "   # ", "  #  ", " #   ", "#    ", "#    "],
    ",": ["     ", "     ", "     ", "     ", " ##  ", "  #  ", " #   "],
    "(": ["   # ", "  #  ", " #   ", " #   ", " #   ", "  #  ", "   # "],
    ")": [" #   ", "  #  ", "   # ", "   # ", "   # ", "  #  ", " #   "],
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


# ---------------------------------------------------------------------
#  Hộp thông tin hành tinh đang được chọn (góc trái trên)
# ---------------------------------------------------------------------

_panel_h = TITLE_H             # chiều cao hộp ở khung hình gần nhất (dùng cho hit-test)


def info_panel_rect():
    return PANEL_X, PANEL_Y, PANEL_W, _panel_h


def hit_test_info(x, y):
    """True nếu con trỏ nằm trong hộp thông tin (để không xoay camera / bỏ chọn)."""
    px, py, pw, ph = info_panel_rect()
    return px <= x <= px + pw and py <= y <= py + ph


def draw_info_panel(name, rows, win_w, win_h):
    """Hộp thông tin: tên hành tinh + các dòng (nhãn, giá trị)."""
    global _panel_h
    _panel_h = TITLE_H + 10 + len(rows) * ROW_H + 2
    _begin_2d(win_w, win_h)
    px, py, pw, ph = info_panel_rect()

    _rect(px, py, pw, ph, (0.10, 0.12, 0.18), 0.92)
    glColor4f(0.35, 0.40, 0.55, 1.0)
    glLineWidth(1.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(px, py)
    glVertex2f(px + pw, py)
    glVertex2f(px + pw, py + ph)
    glVertex2f(px, py + ph)
    glEnd()

    # Tên hành tinh + đường kẻ ngăn
    _text(px + PAD, int(py + (TITLE_H - 7 * TITLE_SCALE) / 2), name, WHITE, TITLE_SCALE)
    _rect(px + PAD, py + TITLE_H, pw - 2 * PAD, 1, (0.35, 0.40, 0.55), 1.0)

    # Nhãn căn trái, giá trị căn phải
    y = py + TITLE_H + 10
    for label, value in rows:
        _text(px + PAD, y, label, LABEL)
        _text(px + pw - PAD - _text_width(value), y, value, WHITE)
        y += ROW_H

    _end_2d()