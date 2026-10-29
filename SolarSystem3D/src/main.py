import math
import random
import glfw

from OpenGL.GL import *
from OpenGL.GLU import gluPerspective, gluLookAt

from planet import PLANETS, init_planets, draw_sun, draw_planet
from orbit import draw_orbit, draw_asteroid_belt

WIDTH, HEIGHT = 1200, 800

# Camera: điều khiển hoàn toàn bằng chuột
camera_distance = 35.0
camera_yaw = 45.0
camera_pitch = 25.0

dragging = False
last_x = 0
last_y = 0

# Thời gian mô phỏng
sim_time = 0.0
sim_speed = 1.0
paused = False

# Nền trắng (chuột phải hoặc phím B để đổi)
white_bg = False

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

    stars.append((x, y, z, random.uniform(0.3, 1.0)))


def mouse_button_callback(window, button, action, mods):
    global dragging, last_x, last_y, white_bg

    if button == glfw.MOUSE_BUTTON_LEFT:
        if action == glfw.PRESS:
            dragging = True
            last_x, last_y = glfw.get_cursor_pos(window)
        elif action == glfw.RELEASE:
            dragging = False

    elif button == glfw.MOUSE_BUTTON_RIGHT and action == glfw.PRESS:
        white_bg = not white_bg


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


def key_callback(window, key, scancode, action, mods):
    global sim_speed, paused, white_bg

    if action == glfw.RELEASE:
        return

    if key == glfw.KEY_SPACE and action == glfw.PRESS:
        paused = not paused
    elif key == glfw.KEY_UP:
        sim_speed = min(sim_speed * 1.25, 20.0)
    elif key == glfw.KEY_DOWN:
        sim_speed = max(sim_speed / 1.25, 0.05)
    elif key == glfw.KEY_R:
        sim_speed = 1.0
    elif key == glfw.KEY_B and action == glfw.PRESS:
        white_bg = not white_bg
    elif key == glfw.KEY_ESCAPE:
        glfw.set_window_should_close(window, True)


def draw_stars():
    glDisable(GL_LIGHTING)
    glPointSize(2.0)

    glBegin(GL_POINTS)
    for x, y, z, b in stars:
        glColor3f(0.75 * b, 0.80 * b, b)
        glVertex3f(x, y, z)
    glEnd()

    glEnable(GL_LIGHTING)


def setup_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)

    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.10, 0.10, 0.13, 1.0))

    glLightfv(GL_LIGHT0, GL_POSITION, (0, 0, 0, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.92, 0.75, 1.0))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_NORMALIZE)


def main():
    global camera_distance, camera_yaw, camera_pitch, sim_time

    if not glfw.init():
        print("Không thể khởi tạo GLFW")
        return

    glfw.window_hint(glfw.SAMPLES, 4)

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
    glfw.set_key_callback(window, key_callback)

    glClearColor(0.008, 0.012, 0.035, 1.0)
    setup_lighting()
    glEnable(GL_MULTISAMPLE)

    # Tạo texture, display list (cần OpenGL context)
    init_planets()

    last_time = glfw.get_time()

    while not glfw.window_should_close(window):
        glfw.poll_events()

        # Cập nhật thời gian mô phỏng
        now = glfw.get_time()
        dt = now - last_time
        last_time = now
        if not paused:
            sim_time += dt * sim_speed

        width, height = glfw.get_framebuffer_size(window)
        if height == 0:
            height = 1

        glViewport(0, 0, width, height)

        # Màu nền: đen (mặc định) hoặc trắng
        if white_bg:
            glClearColor(1.0, 1.0, 1.0, 1.0)
        else:
            glClearColor(0.008, 0.012, 0.035, 1.0)
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

        # Ánh sáng (đặt sau gluLookAt để đèn đứng đúng tại Mặt Trời)
        setup_lighting()

        # Quỹ đạo và vành đai tiểu hành tinh
        glDisable(GL_LIGHTING)
        for planet in PLANETS:
            draw_orbit(planet["orbit_radius"])
        draw_asteroid_belt(sim_time)
        glEnable(GL_LIGHTING)

        # Mặt Trời và hành tinh
        draw_sun(sim_time)
        for planet in PLANETS:
            draw_planet(planet, sim_time)

        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()