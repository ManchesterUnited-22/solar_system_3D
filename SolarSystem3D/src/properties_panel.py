"""Hộp hiển thị tên hành tinh đang được chọn (vẽ 2D bằng OpenGL, không cần thư viện ngoài).

Toạ độ trong file này tính theo pixel cửa sổ, gốc ở góc trái trên.
"""
from OpenGL.GL import *

PANEL_X, PANEL_Y = 12, 12
PANEL_W = 270
TITLE_H = 32
PAD = 12
SCALE = 2                      # mỗi ô của font 5x7 = 2x2 pixel

WHITE = (1.0, 1.0, 1.0)

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
#  Hộp tên hành tinh đang được chọn (góc trái trên)
# ---------------------------------------------------------------------

def info_panel_rect():
    return PANEL_X, PANEL_Y, PANEL_W, TITLE_H


def hit_test_info(x, y):
    """True nếu con trỏ nằm trong hộp tên (để không xoay camera / bỏ chọn)."""
    px, py, pw, ph = info_panel_rect()
    return px <= x <= px + pw and py <= y <= py + ph


def draw_info_panel(name, win_w, win_h):
    """Chỉ hiển thị tên hành tinh đang được chọn."""
    _begin_2d(win_w, win_h)
    px, py, pw, ph = info_panel_rect()

    _rect(px, py, pw, ph, (0.14, 0.16, 0.22), 0.95)
    glColor4f(0.35, 0.40, 0.55, 1.0)
    glLineWidth(1.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(px, py)
    glVertex2f(px + pw, py)
    glVertex2f(px + pw, py + ph)
    glVertex2f(px, py + ph)
    glEnd()

    _text(px + PAD, py + (ph - 7 * SCALE) / 2, name, WHITE)

    _end_2d()