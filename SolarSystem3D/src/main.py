
import glfw
from OpenGL.GL import *

def main():
    if not glfw.init():
        raise RuntimeError("Khong khoi tao duoc GLFW")

    window = glfw.create_window(
        1000, 700, "Solar System 3D", None, None
    )

    if not window:
        glfw.terminate()
        raise RuntimeError("Khong tao duoc cua so")

    glfw.make_context_current(window)
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.0, 0.0, 0.02, 1.0)

    while not glfw.window_should_close(window):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

if __name__ == "__main__":
    main()
