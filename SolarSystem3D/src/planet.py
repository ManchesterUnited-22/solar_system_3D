
from OpenGL.GL import *
from OpenGL.GLU import gluSphere, gluNewQuadric, gluDeleteQuadric


PLANETS = [
    {
        "name": "Mercury",
        "radius": 0.25,
        "orbit_radius": 3.0,
        "color": (0.65, 0.65, 0.65)
    },
    {
        "name": "Venus",
        "radius": 0.40,
        "orbit_radius": 4.5,
        "color": (0.9, 0.6, 0.2)
    },
    {
        "name": "Earth",
        "radius": 0.45,
        "orbit_radius": 6.0,
        "color": (0.1, 0.4, 1.0)
    },
    {
        "name": "Mars",
        "radius": 0.35,
        "orbit_radius": 7.5,
        "color": (1.0, 0.2, 0.1)
    },
    {
        "name": "Jupiter",
        "radius": 0.95,
        "orbit_radius": 10.0,
        "color": (0.8, 0.6, 0.4)
    },
    {
        "name": "Saturn",
        "radius": 0.80,
        "orbit_radius": 13.0,
        "color": (0.9, 0.8, 0.5)
    },
    {
        "name": "Uranus",
        "radius": 0.60,
        "orbit_radius": 16.0,
        "color": (0.3, 0.8, 0.9)
    },
    {
        "name": "Neptune",
        "radius": 0.60,
        "orbit_radius": 19.0,
        "color": (0.2, 0.3, 0.9)
    }
]


def draw_sphere(radius, color, slices=24, stacks=24):
    """Ve hinh cau 3D voi mau cho truoc."""

    glColor3f(*color)

    quadric = gluNewQuadric()
    gluSphere(quadric, radius, slices, stacks)
    gluDeleteQuadric(quadric)


def draw_sun():
    """Ve Mat Troi tai goc toa do."""

    draw_sphere(
        radius=1.5,
        color=(1.0, 0.65, 0.0),
        slices=40,
        stacks=40
    )


def draw_planet(planet, x, z):
    """Ve hanh tinh tai toa do x, 0, z."""

    glPushMatrix()

    glTranslatef(x, 0.0, z)

    draw_sphere(
        planet["radius"],
        planet["color"]
    )

    glPopMatrix()
