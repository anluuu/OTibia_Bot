import random
import threading
import time
import ctypes
import Addresses
import win32api, win32con, win32gui
mouse_lock = threading.Lock()

# SendInput structures for reliable key simulation
PUL = ctypes.POINTER(ctypes.c_ulong)

class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

def send_input(*inputs):
    nInputs = len(inputs)
    LPINPUT = Input * nInputs
    pInputs = LPINPUT(*inputs)
    ctypes.windll.user32.SendInput(nInputs, pInputs, ctypes.sizeof(Input))

def press_key(key_code):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(key_code, 0, 0, 0, ctypes.pointer(extra))
    x = Input(ctypes.c_ulong(1), ii_)
    send_input(x)

def release_key(key_code):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput(key_code, 0, 0x0002, 0, ctypes.pointer(extra))  # KEYEVENTF_KEYUP
    x = Input(ctypes.c_ulong(1), ii_)
    send_input(x)


def mouse_function(x_source, y_source, x_dest=0, y_dest=0, option=0) ->None:
    with mouse_lock:
        if option == 1: #  Right Click
            win32gui.PostMessage(Addresses.game, win32con.WM_MOUSEMOVE, 0, win32api.MAKELONG(x_source, y_source))
            win32gui.PostMessage(Addresses.game, win32con.WM_RBUTTONDOWN, 2, win32api.MAKELONG(x_source, y_source))
            win32gui.PostMessage(Addresses.game, win32con.WM_RBUTTONUP, 0, win32api.MAKELONG(x_source, y_source))
        if option == 2: #  Left Click
            win32gui.PostMessage(Addresses.game, win32con.WM_MOUSEMOVE, 0, win32api.MAKELONG(x_source, y_source))
            win32gui.PostMessage(Addresses.game, win32con.WM_LBUTTONDOWN, 1, win32api.MAKELONG(x_source, y_source))
            win32gui.PostMessage(Addresses.game, win32con.WM_LBUTTONUP, 0, win32api.MAKELONG(x_source, y_source))
        if option == 3: #  Collect Item
            win32gui.PostMessage(Addresses.game, win32con.WM_MOUSEMOVE, 0, win32api.MAKELONG(x_source, y_source))
            win32gui.PostMessage(Addresses.game, win32con.WM_LBUTTONDOWN, 1, win32api.MAKELONG(x_source, y_source))
            win32gui.PostMessage(Addresses.game, win32con.WM_MOUSEMOVE, 0, win32api.MAKELONG(x_dest, y_dest))
            win32gui.PostMessage(Addresses.game, win32con.WM_LBUTTONUP, 0, win32api.MAKELONG(x_dest, y_dest))
            win32gui.PostMessage(Addresses.game, win32con.WM_MOUSEMOVE, 0, win32api.MAKELONG(x_dest, y_dest))
            win32gui.PostMessage(Addresses.game, win32con.WM_RBUTTONDOWN, 2, win32api.MAKELONG(x_dest, y_dest))
            win32gui.PostMessage(Addresses.game, win32con.WM_RBUTTONUP, 0, win32api.MAKELONG(x_dest, y_dest))
        if option == 4: #  Drag'n'Drop
            win32gui.PostMessage(Addresses.game, win32con.WM_MOUSEMOVE, 0, win32api.MAKELONG(x_source, y_source))
            win32gui.PostMessage(Addresses.game, win32con.WM_LBUTTONDOWN, 1, win32api.MAKELONG(x_source, y_source))
            win32gui.PostMessage(Addresses.game, win32con.WM_MOUSEMOVE, 1, win32api.MAKELONG(x_dest, y_dest))
            win32gui.PostMessage(Addresses.game, win32con.WM_LBUTTONUP, 0, win32api.MAKELONG(x_dest, y_dest))
        if option == 5: #  Use on me
            win32gui.PostMessage(Addresses.game, win32con.WM_MOUSEMOVE, 0, win32api.MAKELONG(x_source, y_source))
            win32gui.PostMessage(Addresses.game, win32con.WM_RBUTTONDOWN, 2, win32api.MAKELONG(x_source, y_source))
            win32gui.PostMessage(Addresses.game, win32con.WM_RBUTTONUP, 0, win32api.MAKELONG(x_source, y_source))
            win32gui.PostMessage(Addresses.game, win32con.WM_MOUSEMOVE, 0,win32api.MAKELONG(x_dest, y_dest))
            win32gui.PostMessage(Addresses.game, win32con.WM_LBUTTONDOWN, 1,win32api.MAKELONG(x_dest, y_dest))
            win32gui.PostMessage(Addresses.game, win32con.WM_LBUTTONUP, 0,win32api.MAKELONG(x_dest, y_dest))
        if option == 6: #  Alt+Click (Attack creature - non-classic controls)
            # Need to use SendInput for Alt+Click - requires window focus
            # Get window rect to convert client coords to screen coords
            rect = win32gui.GetWindowRect(Addresses.game)
            screen_x = rect[0] + x_source
            screen_y = rect[1] + y_source + Addresses.TITLE_BAR_OFFSET

            # Focus the game window first
            win32gui.SetForegroundWindow(Addresses.game)
            time.sleep(0.03)

            # Press and HOLD Alt key first
            press_key(0x12)  # VK_MENU (Alt)
            time.sleep(0.03)

            # Move mouse while Alt is held
            win32api.SetCursorPos((screen_x, screen_y))
            time.sleep(0.03)

            # Click while Alt is still held
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.01)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

            # Keep Alt held a bit longer, then release
            time.sleep(0.03)
            release_key(0x12)


def manage_collect(x, y, action) -> None:
    if action > 0:
        mouse_function(x, y, Addresses.coordinates_x[action], Addresses.coordinates_y[action], option=3)
    elif action == 0:
        mouse_function(x, y, Addresses.coordinates_x[0], Addresses.coordinates_y[0], option=4)
    elif action == -1:
        mouse_function(x, y, option=1)
    elif action == -2:
        mouse_function(x, y, option=2)
        mouse_function(x, y, option=2)
    elif action == -3:
        mouse_function(x, y, Addresses.coordinates_x[0], Addresses.coordinates_y[0], option=5)