import time
import os
import sys
import winreg
import subprocess
from pynput import mouse, keyboard
from screeninfo import get_monitors
import pystray
from PIL import Image

class DesktopSwitcher:
    def __init__(self):
        self.kb = keyboard.Controller()
        self.screen_height = get_monitors()[0].height
        self.bottom_margin = 10
        self.cooldown = 0.1
        self.ctrl_pressed = False
        self.app_switch_active = False
        self.middle_button_pressed = False
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.keyboard_listener.start()

    def is_at_bottom(self, y):
        return y >= self.screen_height - self.bottom_margin

    def switch_desktop(self, direction):
        with self.kb.pressed(keyboard.Key.cmd, keyboard.Key.ctrl):
            self.kb.tap(keyboard.Key.left if direction > 0 else keyboard.Key.right)

    def open_task_view(self):
        with self.kb.pressed(keyboard.Key.cmd):
            self.kb.tap(keyboard.Key.tab)

    def switch_app(self, direction):
        self.app_switch_active = True
        if direction > 0:
            with self.kb.pressed(keyboard.Key.alt, keyboard.Key.shift):
                self.kb.tap(keyboard.Key.tab)
        else:
            with self.kb.pressed(keyboard.Key.alt):
                self.kb.tap(keyboard.Key.tab)

    def on_scroll(self, x, y, dx, dy):
        if self.is_at_bottom(y):
            if self.ctrl_pressed:
                self.switch_app(dy)
            else:
                self.switch_desktop(dy)
            time.sleep(self.cooldown)

    def on_click(self, x, y, button, pressed):
        if self.is_at_bottom(y) and button == mouse.Button.middle:
            if pressed:
                self.middle_button_pressed = True
            else:
                if self.middle_button_pressed:
                    self.open_task_view()
                    self.middle_button_pressed = False
                    time.sleep(self.cooldown)

    def on_key_press(self, key):
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = True

    def on_key_release(self, key):
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = False
            if self.app_switch_active:
                self.kb.tap(keyboard.Key.enter)
                self.app_switch_active = False

    def run(self):
        with mouse.Listener(on_scroll=self.on_scroll, on_click=self.on_click) as listener:
            listener.join()

def add_to_startup():
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(key, "DesktopSwitcher", 0, winreg.REG_SZ, sys.executable)
        winreg.CloseKey(key)
        return "Added to startup successfully"
    except Exception as e:
        return f"Failed to add to startup: {str(e)}"

def show_donate():
    donate_image = os.path.join(os.path.dirname(sys.executable), "donate.jpg")
    if os.path.exists(donate_image):
        os.startfile(donate_image)
    else:
        return "Donate image not found"

def create_menu(icon):
    return pystray.Menu(
        pystray.MenuItem("Add to Startup", lambda: icon.notify(add_to_startup())),
        pystray.MenuItem("Donate", lambda: icon.notify(show_donate())),
        pystray.MenuItem("Exit", lambda: icon.stop())
    )

def run_tray():
    icon_path = os.path.join(os.path.dirname(sys.executable), "desktop_switcher.png")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(os.path.dirname(__file__), "desktop_switcher.png")
    
    image = Image.open(icon_path)
    
    def setup(icon):
        icon.visible = True
        switcher = DesktopSwitcher()
        switcher.run()
    
    icon = pystray.Icon("DesktopSwitcher", image, "Desktop Switcher", menu=create_menu)
    icon.run(setup=setup)

if __name__ == "__main__":
    run_tray()