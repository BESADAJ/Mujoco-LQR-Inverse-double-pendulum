import mujoco as mj
from mujoco.glfw import glfw
import matplotlib.pyplot as plt
import numpy as np
import os
import control

# plotting data
times = []
qpos0_list = []
qpos1_list = []
qvel0_list = []
qvel1_list = []

xml_path = '2D_double_pendulum.xml' #xml file (assumes this is in the same folder as this file)
simend = 40 #simulation time
print_camera_config = 0 #set to 1 to print camera config
                        #this is useful for initializing view of the model)

# For callback functions
button_left = False
button_middle = False
button_right = False
lastx = 0
lasty = 0

#create the function xdot = f(x,u)
def f(x,u):
    #x=q0,q1,qdot0,qdot1
    #u=torque

    data.qpos[0] = x[0]
    data.qpos[1] = x[1]
    data.qvel[0] = x[2]
    data.qvel[1] = x[3]
    data.ctrl[0] = u[0]
    mj.mj_forward(model,data)

    #qddot = inv(M)*(data_ctrl-frc_bias)
    M = np.zeros((2,2))
    mj.mj_fullM(model,M,data.qM)
    invM = np.linalg.inv(M)
    frc_bias = np.array([data.qfrc_bias[0],data.qfrc_bias[1]])
    tau = np.array([u[0],0])
    qddot = np.matmul(invM,np.subtract(tau,frc_bias))

    xdot = np.array([data.qvel[0],data.qvel[1],qddot[0],qddot[1]])
    return xdot


def linearize():

    n = 4
    m = 1
    A = np.zeros((n,n))
    B = np.zeros((n,m))

    x0 = np.array([0,0,0,0])
    u0 = np.array([0])
    xdot0 = f(x0,u0)
    #print(xdot0)

    pert = 1e-2
    #get A matrix
    for i in range(0,n):
        x = [0]*n
        u = u0
        for j in range(0,n):
            x[j] = x0[j]
        x[i] = x[i]+pert
        xdot = f(x,u)
        for k in range(0,n):
            A[k,i] = (xdot[k]-xdot0[k])/pert

    #get B matrix
    for i in range(0,m):
        x = x0
        u = [0]*m
        for j in range(0,m):
            u[j] = u0[j]
        u[i] = u[i]+pert
        xdot = f(x,u)
        for k in range(0,n):
            B[k,i] = (xdot[k]-xdot0[k])/pert

    return A,B


def init_controller(model,data):
    #initialize the controller here. This function is called once, in the beginning
    #pass
    global K

    n = 4
    m = 1

    #1. linearization
    A,B = linearize()
    # print(A)
    # print(B)

    #2. linear quadratic regulator
    Q = [[1,0,0,0],
         [0,1,0,0],
         [0,0,1,0],
         [0,0,0,1]]
    R = 1*np.eye((m))
    K,S,E = control.lqr(A,B,Q,R)
    print(E)
    print("K = ",K)
    print("S =", S )
    print("E =", E )

def controller(model, data):
    #put the controller here. This function is called inside the simulation.
    # pass
    global K

    #1. apply control u = -K*x
    x = np.array([data.qpos[0],data.qpos[1],data.qvel[0],data.qvel[1]])
    u = -K.dot(x)
    data.ctrl[0] = u

    #2 apply disturbance torque
    tau_disturb_mean = -0.3
    tau_disturb_dev = 8
    tau_d0 = np.random.normal(tau_disturb_mean,tau_disturb_dev)
    tau_d1 = np.random.normal(tau_disturb_mean,0.25*tau_disturb_dev)
    data.qfrc_applied[0] = tau_d0
    data.qfrc_applied[1] = tau_d1

def keyboard(window, key, scancode, act, mods):
    if act == glfw.PRESS and key == glfw.KEY_BACKSPACE:
        mj.mj_resetData(model, data)
        mj.mj_forward(model, data)

def mouse_button(window, button, act, mods):
    # update button state 
    global button_left
    global button_middle
    global button_right

    button_left = (glfw.get_mouse_button(
        window, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS)
    button_middle = (glfw.get_mouse_button(
        window, glfw.MOUSE_BUTTON_MIDDLE) == glfw.PRESS)
    button_right = (glfw.get_mouse_button(
        window, glfw.MOUSE_BUTTON_RIGHT) == glfw.PRESS)

    # update mouse position
    glfw.get_cursor_pos(window)

def mouse_move(window, xpos, ypos):
    # compute mouse displacement, save
    global lastx
    global lasty
    global button_left
    global button_middle
    global button_right

    dx = xpos - lastx
    dy = ypos - lasty
    lastx = xpos
    lasty = ypos

    # no buttons down: nothing to do
    if (not button_left) and (not button_middle) and (not button_right):
        return

    # get current window size
    width, height = glfw.get_window_size(window)

    # get shift key state
    PRESS_LEFT_SHIFT = glfw.get_key(
        window, glfw.KEY_LEFT_SHIFT) == glfw.PRESS
    PRESS_RIGHT_SHIFT = glfw.get_key(
        window, glfw.KEY_RIGHT_SHIFT) == glfw.PRESS
    mod_shift = (PRESS_LEFT_SHIFT or PRESS_RIGHT_SHIFT)

    # determine action based on mouse button
    if button_right:
        if mod_shift:
            action = mj.mjtMouse.mjMOUSE_MOVE_H
        else:
            action = mj.mjtMouse.mjMOUSE_MOVE_V
    elif button_left:
        if mod_shift:
            action = mj.mjtMouse.mjMOUSE_ROTATE_H
        else:
            action = mj.mjtMouse.mjMOUSE_ROTATE_V
    else:
        action = mj.mjtMouse.mjMOUSE_ZOOM

    mj.mjv_moveCamera(model, action, dx/height,
                      dy/height, scene, cam)

def scroll(window, xoffset, yoffset):
    action = mj.mjtMouse.mjMOUSE_ZOOM
    mj.mjv_moveCamera(model, action, 0.0, -0.05 *
                      yoffset, scene, cam)

#get the full path
dirname = os.path.dirname(__file__)
abspath = os.path.join(dirname + "/" + xml_path)
xml_path = abspath

# MuJoCo data structures
model = mj.MjModel.from_xml_path(xml_path)  # MuJoCo model
data = mj.MjData(model)                # MuJoCo data
cam = mj.MjvCamera()                        # Abstract camera
opt = mj.MjvOption()                        # visualization options

# Init GLFW, create window, make OpenGL context current, request v-sync
glfw.init()
window = glfw.create_window(1200, 900, "Demo", None, None)
glfw.make_context_current(window)
glfw.swap_interval(1)

# initialize visualization data structures
mj.mjv_defaultCamera(cam)
mj.mjv_defaultOption(opt)
scene = mj.MjvScene(model, maxgeom=10000)
context = mj.MjrContext(model, mj.mjtFontScale.mjFONTSCALE_150.value)

# install GLFW mouse and keyboard callbacks
glfw.set_key_callback(window, keyboard)
glfw.set_cursor_pos_callback(window, mouse_move)
glfw.set_mouse_button_callback(window, mouse_button)
glfw.set_scroll_callback(window, scroll)

# Example on how to set camera configuration
# cam.azimuth = 90
# cam.elevation = -45
#cam.distance =2
# cam.lookat = np.array([0.0, 0.0, 0])
cam.azimuth = 45 ; cam.elevation = 0 ; cam.distance =  6
cam.lookat =np.array([ -0, -0.0 , 0])

#initialize the controller
init_controller(model,data)

#set the controller
mj.set_mjcb_control(controller)

while not glfw.window_should_close(window):
    time_prev = data.time

    while (data.time - time_prev < 1.0/60.0):
        mj.mj_step(model, data)
    #data storage
    times.append(data.time)
    qpos0_list.append(data.qpos[0])
    qpos1_list.append(data.qpos[1])
    qvel0_list.append(data.qvel[0])
    qvel1_list.append(data.qvel[1])

    if (data.time>=simend):
        break;

    # get framebuffer viewport
    viewport_width, viewport_height = glfw.get_framebuffer_size(
        window)
    viewport = mj.MjrRect(0, 0, viewport_width, viewport_height)

    #print camera configuration (help to initialize the view)
    if (print_camera_config==1):
        print('cam.azimuth =',cam.azimuth,';','cam.elevation =',cam.elevation,';','cam.distance = ',cam.distance)
        print('cam.lookat =np.array([',cam.lookat[0],',',cam.lookat[1],',',cam.lookat[2],'])')

    # Update scene and render
    mj.mjv_updateScene(model, data, opt, None, cam,
                       mj.mjtCatBit.mjCAT_ALL.value, scene)
    mj.mjr_render(viewport, scene, context)

    # swap OpenGL buffers (blocking call due to v-sync)
    glfw.swap_buffers(window)

    # process pending GUI events, call GLFW callbacks
    glfw.poll_events()


plt.figure(figsize=(10, 8))

plt.subplot(2, 1, 1)
plt.plot(times, qpos0_list, label='qpos[0]')
plt.plot(times, qpos1_list, label='qpos[1]')
plt.ylabel('Position (rad)')
plt.legend()
plt.title('Joint Positions')

plt.subplot(2, 1, 2)
plt.plot(times, qvel0_list, label='qvel[0]')
plt.plot(times, qvel1_list, label='qvel[1]')
plt.xlabel('Time (s)')
plt.ylabel('Velocity (rad/s)')
plt.legend()
plt.title('Joint Velocities')

plt.tight_layout()
plt.show()

glfw.terminate()
