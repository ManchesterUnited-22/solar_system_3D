import math
import random
import glfw

from OpenGL.GL import *
from OpenGL.GLU import gluPerspective, gluLookAt, gluProject

from planet import (PLANETS, init_planets, draw_sun, draw_planet,
                    set_wire_background, planet_position)
from orbit import draw_orbit, draw_asteroid_belt
from axes import draw_axes, draw_coord_path, coord_end_points
import properties_panel as ui

WIDTH, HEIGHT = 1200, 800

# Camera: điều khiển hoàn toàn bằng chuột
camera_distance = 40.0
camera_yaw = 45.0
camera_pitch = 25.0

dragging = False
last_x = 0
last_y = 0
press_x = 0
press_y = 0

# Thời gian mô phỏng
sim_time = 0.0
sim_speed = 1.0
paused = False

# Nền trắng (phím B để đổi)
white_bg = False

# Hiện/ẩn các vòng quỹ đạo (phím O để đổi)
show_orbits = False

# Chế độ khung mô hình hóa (chuột phải để bật/tắt)
wireframe = False

# Tab đang chọn của bảng Properties:
#   0 = SHOW AXES (hiện trục XYZ, ẩn quỹ đạo và thiên thạch)
#   1 = HIDE AXES (không hiện trục, hiện quỹ đạo và thiên thạch)
ui_tab = 1

# ---------------------------------------------------------------------
#  Chọn hành tinh: bấm vào hành tinh -> camera phóng to và bám theo nó
# ---------------------------------------------------------------------
CLICK_TOLERANCE = 5.0        # pixel: di chuyển ít hơn mức này giữa nhấn và thả = "bấm"
TRANSITION_TIME = 0.9        # giây
DIM_ALPHA = 0.15             # độ đậm của trục bị làm mờ
FOV = 45.0

focus = None                 # chỉ số hành tinh đang chọn (None = nhìn toàn hệ)
focus_distance = 4.0         # khoảng cách camera khi đang zoom vào hành tinh
trans_t = 1.0                # tiến độ chuyển cảnh 0..1
trans_from_target = (0.0, 0.0, 0.0)
trans_from_dist = camera_distance
axis_alpha = {"X": 1.0, "Y": 1.0, "Z": 1.0}   # độ đậm hiện tại của từng trục
prev_tab = 1                 # tab trước khi tự chuyển sang SHOW AXES
forced_tab = False

# Ma trận của khung hình gần nhất (để đổi toạ độ 3D -> pixel khi bấm chuột)
cam_eye = (0.0, 0.0, 0.0)
view_mats = None

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


def _ease(t):
    return t * t * (3.0 - 2.0 * t)          # smoothstep


def current_camera():
    """(tâm nhìn, khoảng cách) hiện tại, đã nội suy mượt giữa 2 chế độ camera."""
    if focus is None:
        goal_t, goal_d = (0.0, 0.0, 0.0), camera_distance
    else:
        goal_t = planet_position(PLANETS[focus], sim_time)   # luôn là vị trí MỚI NHẤT
        goal_d = focus_distance
    e = _ease(trans_t)
    target = tuple(f + (g - f) * e for f, g in zip(trans_from_target, goal_t))
    return target, trans_from_dist + (goal_d - trans_from_dist) * e


def _begin_transition():
    """Ghi lại camera hiện tại làm điểm xuất phát để chuyển cảnh không bị giật."""
    global trans_t, trans_from_target, trans_from_dist
    trans_from_target, trans_from_dist = current_camera()
    trans_t = 0.0


def select_planet(i):
    global focus, focus_distance, ui_tab, prev_tab, forced_tab
    _begin_transition()
    if focus is None:
        # Cần thấy hệ trục: tự chuyển sang tab SHOW AXES (nhớ lại để trả về sau)
        forced_tab = (ui_tab != 0)
        if forced_tab:
            prev_tab, ui_tab = ui_tab, 0
    focus = i
    # Zoom đủ gần để hành tinh lớn, nhưng vẫn giữ các trục gần đó trong khung hình.
    # Tính theo kích thước quỹ đạo (không theo vị trí lúc bấm) nên khoảng cách ổn
    # định khi hành tinh tiếp tục chạy. Người dùng cuộn chuột để zoom thêm / lùi ra.
    base = max(3.5, PLANETS[i]["radius"] * 7.0)
    focus_distance = max(base, min(10.0, 1.4 * PLANETS[i]["orbit_radius"]))


def clear_focus():
    global focus, ui_tab, forced_tab
    _begin_transition()
    focus = None
    if forced_tab:
        ui_tab, forced_tab = prev_tab, False


def project_to_window(window, pos):
    """Toạ độ 3D -> toạ độ cửa sổ (pixel, gốc ở góc trái trên), None nếu sau camera."""
    if view_mats is None:
        return None
    mv, proj, view = view_mats
    wx, wy, wz = gluProject(pos[0], pos[1], pos[2], mv, proj, view)
    if wz >= 1.0:
        return None
    win_w, win_h = glfw.get_window_size(window)
    fb_w, fb_h = glfw.get_framebuffer_size(window)
    return wx * win_w / fb_w, (fb_h - wy) * win_h / fb_h


def pick_planet(window, x, y):
    """Hành tinh nằm dưới con trỏ (x, y theo toạ độ cửa sổ), hoặc None."""
    if view_mats is None:
        return None
    mv, proj, view = view_mats
    win_w, win_h = glfw.get_window_size(window)
    fb_w, fb_h = glfw.get_framebuffer_size(window)
    sx = x * fb_w / win_w                    # đổi sang pixel của framebuffer
    sy = fb_h - y * fb_h / win_h             # OpenGL: gốc ở góc trái dưới
    px_per_unit = fb_h / (2.0 * math.tan(math.radians(FOV / 2)))

    best, best_dist = None, 1e9
    for i, p in enumerate(PLANETS):
        pos = planet_position(p, sim_time)
        wx, wy, wz = gluProject(pos[0], pos[1], pos[2], mv, proj, view)
        if wz >= 1.0:                        # nằm sau camera
            continue
        dist = math.dist(cam_eye, pos)
        # Bán kính trên màn hình, tối thiểu 14px để hành tinh nhỏ/xa vẫn dễ bấm
        hit_r = max(p["radius"] * px_per_unit / dist * 1.2, 14.0 * fb_w / win_w)
        if math.hypot(wx - sx, wy - sy) <= hit_r and dist < best_dist:
            best, best_dist = i, dist
    return best


def mouse_button_callback(window, button, action, mods):
    global dragging, last_x, last_y, wireframe, ui_tab, forced_tab
    global press_x, press_y

    if button == glfw.MOUSE_BUTTON_LEFT:
        if action == glfw.PRESS:
            x, y = glfw.get_cursor_pos(window)
            hit = ui.hit_test(x, y, ui_tab)
            if hit is not None:
                # Bấm vào bảng Properties: chọn tab, không xoay camera
                if hit in (0, 1):
                    ui_tab = hit
                    forced_tab = False       # người dùng đã tự chọn tab
                return
            if focus is not None and ui.hit_test_info(x, y, ui_tab, paused):
                return                       # bấm vào bảng thông tin hành tinh
            dragging = True
            last_x, last_y = x, y
            press_x, press_y = x, y
        elif action == glfw.RELEASE:
            if dragging:
                x, y = glfw.get_cursor_pos(window)
                if math.hypot(x - press_x, y - press_y) < CLICK_TOLERANCE:
                    # Nhấn và thả gần như cùng chỗ = bấm (không phải kéo xoay)
                    idx = pick_planet(window, x, y)
                    if idx is not None:
                        if idx != focus:
                            select_planet(idx)
                    elif focus is not None:
                        clear_focus()        # bấm vào khoảng trống: về toàn hệ
            dragging = False

    elif button == glfw.MOUSE_BUTTON_RIGHT and action == glfw.PRESS:
        # Bật/tắt khung mô hình hóa (hình cầu dạng lưới)
        wireframe = not wireframe
        title = "Solar System 3D - Khung mô hình hóa" if wireframe else "Solar System 3D"
        glfw.set_window_title(window, title)


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
    global camera_distance, focus_distance

    if focus is None:
        camera_distance -= yoffset * 2.0
        camera_distance = max(8.0, min(90.0, camera_distance))
    else:
        # Đang zoom vào hành tinh: bước nhỏ, tỉ lệ theo khoảng cách hiện tại
        focus_distance -= yoffset * max(0.3, focus_distance * 0.12)
        focus_distance = max(PLANETS[focus]["radius"] * 2.5, min(40.0, focus_distance))


def key_callback(window, key, scancode, action, mods):
    global sim_speed, paused, white_bg, show_orbits

    if action == glfw.RELEASE:
        return

    if key == glfw.KEY_SPACE and action == glfw.PRESS:
        paused = not paused
    elif key == glfw.KEY_O and action == glfw.PRESS:
        show_orbits = not show_orbits
    elif key == glfw.KEY_UP:
        sim_speed = min(sim_speed * 1.25, 20.0)
    elif key == glfw.KEY_DOWN:
        sim_speed = max(sim_speed / 1.25, 0.05)
    elif key == glfw.KEY_R:
        sim_speed = 1.0
    elif key == glfw.KEY_B and action == glfw.PRESS:
        white_bg = not white_bg
    elif key == glfw.KEY_ESCAPE:
        if focus is not None:
            clear_focus()                    # ESC lần 1: về toàn hệ
        else:
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


def setup_lighting(full_bright=False):
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)

    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    glLightfv(GL_LIGHT0, GL_POSITION, (0, 0, 0, 1))

    if full_bright:
        # Nền trắng: sáng phẳng, mọi hành tinh hiện đủ màu
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (1.0, 1.0, 1.0, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.0, 0.0, 0.0, 1.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, (0.0, 0.0, 0.0, 1.0))
    else:
        # Nền đen: chiếu sáng theo Mặt Trời
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.10, 0.10, 0.13, 1.0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.92, 0.75, 1.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_NORMALIZE)


def main():
    global camera_distance, camera_yaw, camera_pitch, sim_time
    global trans_t, cam_eye, view_mats

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
        if trans_t < 1.0:
            trans_t = min(1.0, trans_t + dt / TRANSITION_TIME)

        # Làm mờ dần các trục mà hành tinh đang chọn nằm trên đó
        # (hành tinh ở mặt phẳng XZ -> trục X và Z mờ, trục Y vẫn rõ)
        focus_pos = planet_position(PLANETS[focus], sim_time) if focus is not None else None
        for k, name in enumerate("XYZ"):
            goal = DIM_ALPHA if (focus_pos and abs(focus_pos[k]) > 1e-6) else 1.0
            axis_alpha[name] += (goal - axis_alpha[name]) * min(1.0, dt * 6.0)

        width, height = glfw.get_framebuffer_size(window)
        if height == 0:
            height = 1

        glViewport(0, 0, width, height)

        # Màu nền: đen (mặc định) hoặc trắng
        if white_bg:
            bg = (1.0, 1.0, 1.0)
        else:
            bg = (0.008, 0.012, 0.035)
        glClearColor(bg[0], bg[1], bg[2], 1.0)
        set_wire_background(bg)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Phép chiếu phối cảnh
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(FOV, width / height, 0.1, 200.0)

        # Camera xoay quanh tâm nhìn: tâm hệ Mặt Trời, hoặc hành tinh đang chọn
        yaw = math.radians(camera_yaw)
        pitch = math.radians(camera_pitch)
        (tx, ty, tz), dist = current_camera()

        cam_x = tx + dist * math.cos(pitch) * math.sin(yaw)
        cam_y = ty + dist * math.sin(pitch)
        cam_z = tz + dist * math.cos(pitch) * math.cos(yaw)
        cam_eye = (cam_x, cam_y, cam_z)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(
            cam_x, cam_y, cam_z,
            tx, ty, tz,
            0, 1, 0
        )

        # Lưu ma trận để đổi toạ độ 3D -> pixel khi bấm chuột chọn hành tinh
        view_mats = (glGetDoublev(GL_MODELVIEW_MATRIX),
                     glGetDoublev(GL_PROJECTION_MATRIX),
                     glGetIntegerv(GL_VIEWPORT))

        # Sao nền
        draw_stars()

        # Ánh sáng (đặt sau gluLookAt để đèn đứng đúng tại Mặt Trời)
        setup_lighting(white_bg)

        # Quỹ đạo và vành đai tiểu hành tinh
        glDisable(GL_LIGHTING)
        if ui_tab != 0:
            # Tab HIDE AXES: hiện thiên thạch (và quỹ đạo nếu bật bằng phím O)
            if show_orbits:
                for planet in PLANETS:
                    draw_orbit(
                        planet["orbit_radius"],
                        planet["orbit_eccentricity"],
                        math.radians(planet.get("orbit_omega", 0.0)),
                    )
            draw_asteroid_belt(sim_time)
        glEnable(GL_LIGHTING)

        # Mặt Trời và hành tinh
        draw_sun(sim_time, wireframe)
        for planet in PLANETS:
            draw_planet(planet, sim_time, wireframe)

        # Tab SHOW AXES: hệ trục XYZ (bỏ quỹ đạo và thiên thạch). Vẽ SAU hành tinh để
        # quầng sáng Mặt Trời (cộng sáng) không bị trục khoét thủng hay phủ lên trục.
        if ui_tab == 0:
            glDisable(GL_LIGHTING)
            draw_axes(axis_alpha)
            if focus_pos and paused:
                # Đang dừng: đường đi dọc từng trục tới vị trí hành tinh
                draw_coord_path(*focus_pos)
            glEnable(GL_LIGHTING)

        # Bảng Properties (vẽ đè lên trên cùng)
        win_w, win_h = glfw.get_window_size(window)
        ui.draw_panel(ui_tab, win_w, win_h)
        if focus is not None:
            ui.draw_info_panel(PLANETS[focus]["name"].upper(), focus_pos,
                               paused, ui_tab, win_w, win_h)
            if paused and ui_tab == 0:
                # Nhãn số ở đầu đoạn toạ độ trên mỗi trục X, Y, Z
                tags = []
                for name, color, p3, v in zip("XYZ", (ui.RED, ui.GREEN, ui.BLUE),
                                              coord_end_points(*focus_pos), focus_pos):
                    pt = project_to_window(window, p3)
                    if pt:
                        tags.append((pt[0], pt[1], "%s %s" % (name, ui._fmt(v)), color))
                ui.draw_value_tags(tags, win_w, win_h)

        glfw.swap_buffers(window)

    glfw.terminate()


if __name__ == "__main__":
    main()