
import math
from OpenGL.GL import *


def draw_orbit(radius, segments=120):
    """Ve quy dao tron tren mat phang XZ."""

    glColor3f(0.35, 0.35, 0.35)
    glBegin(GL_LINE_LOOP)

    for i in range(segments):
        angle = 2.0 * math.pi * i / segments

        x = radius * math.cos(angle)
        z = radius * math.sin(angle)

        glVertex3f(x, 0.0, z)

    glEnd()
