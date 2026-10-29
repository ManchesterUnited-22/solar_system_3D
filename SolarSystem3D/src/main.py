
import math
import random
import glfw

from OpenGL.GL import *
from OpenGL.GLU import gluPerspective, gluLookAt

from planet import PLANETS, draw_sun, draw_planet
from orbit import draw_orbit

WIDTH, HEIGHT = 1200, 800

# Camera: điều khiển hoàn toàn bằng chuột
camera_distance = 35.0
camera_yaw = 45.0
camera_pitch = 25.0

dragging = False
last_x = 0
last_y = 0

# Tạo sao nền
random.seed(10)
stars = []

for _ in range(900):
    theta = random.uniform(0, 2 * math.pi)
    phi = random.uniform(0, math.pi)
    radius = random.uniform(65, 100)

    x = radius * math.sin(phi) * math.cos(theta)
    y = radius * math.cos(phi)
    z = radius * math.sin(phi) * math.sin(theta)

    stars.append((x, y, z))


def mouse_button_callback(window, button, action, mods):
    global dragging, last_x, last_y

    if button == glfw.MOUSE_BUTTON_LEFT:
        if action == glfw.PRESS:
            dragging = True
            last_x, last_y = glfw.get_cursor_pos(window)
        elif action == glfw.RELEASE:
            dragging = False


def cursor_position_callback(window, xpos, ypos):
    global camera_yaw, camera_pitch, last_x, last_y

    if dragging:
        dx = xpos - last_x
        dy = ypos - last_y

        camera_yaw += dx * 0.35
        camera_pitch -= dy * 0.35
        camera_pitch = max(-80, min(80, camera_pitch))

    last_x, last_y = xpos, ypos


def scroll_callback(window, xoffset, yoffset):
    global camera_distance

    camera_distance -= yoffset * 2.0
    camera_distance = max(8.0, min(90.0, camera_distance))


def draw_stars():
    glDisable(GL_LIGHTING)
    glPointSize(2.0)

    glBegin(GL_POINTS)
    for x, y, z in stars:
        glColor3f(0.75, 0.80, 1.0)
        glVertex3f(x, y, z)
    glEnd()

    glEnable(GL_LIGHTING)


def setup_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)

    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    glLightfv(GL_LIGHT0, GL_POSITION, (0, 0, 0, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.92, 0.75, 1.0))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_NORMALIZE)


def main():
    global camera_distance, camera_yaw, camera_pitch

    if not glfw.init():
        print("Không thể khởi tạo GLFW")
        return

    window = glfw.create_window(
        WIDTH, HEIGHT,
        "Solar System 3D",
        None, None
    )

    if not window:
        glfw.terminate()
        print("Không thể tạo cửa sổ")
        return

    glfw.make_context_current(window)
    glfw.swap_interval(1)

    glfw.set_mouse_button_callback(window, mouse_button_callback)
    glfw.set_cursor_pos_callback(window, cursor_position_callback)
    glfw.set_scroll_callback(window, scroll_callback)

    glClearColor(0.008, 0.012, 0.035, 1.0)
    setup_lighting()

    while not glfw.window_should_close(window):
        glfw.poll_events()

        width, height = glfw.get_framebuffer_size(window)
        if height == 0:
            height = 1

        glViewport(0, 0, width, height)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Phép chiếu phối cảnh
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, width / height, 0.1, 200.0)

        # Camera xoay quanh tâm hệ Mặt Trời
        yaw = math.radians(camera_yaw)
        pitch = math.radians(camera_pitch)

        cam_x = camera_distance * math.cos(pitch) * math.sin(yaw)
        cam_y = camera_distance * math.sin(pitch)
        cam_z = camera_distance * math.cos(pitch) * math.cos(yaw)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(
            cam_x, cam_y, cam_z,
            0, 0, 0,
            0, 1, 0
        )

        # Sao nền
        draw_stars()

        # Ánh sáng
        setup_lighting()

        # Quỹ đạo và hành tinh
        glDisable(GL_LIGHTING)

        for planet in PLANETS:
            draw_orbit(planet["orbit_radius"])

        glEnable(GL_LIGHTING)

        draw_sun()

        for planet in PLANETS:
            x = planet["orbit_radius"]
            z = 0

            draw_planet(planet, x, z)

        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()
