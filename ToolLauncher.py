import tkinter as tk
import configparser
import webbrowser
import threading
import pystray
from pystray import MenuItem as item
from PIL import Image
import keyboard
import os
import sys
import winreg

HOTKEY = "ctrl+shift+b"
CONFIG_FILE = "ToolLauncher.conf"
ICON_FILE = "ToolLauncher_Logo.ico"

# === Check if Windows is in Dark Mode ===
def is_dark_mode():
    try:
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return value == 0
    except:
        return False  # Default to light mode if detection fails

# === Resource Path Resolver ===
def resource_path(filename):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)

# === Load Config ===
def load_tools():
    config = configparser.ConfigParser()
    base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
    config_path = os.path.join(base_dir, CONFIG_FILE)
    config.read(config_path)

    tools = []
    for section in config.sections():
        label = config.get(section, "label", fallback=None)
        url = config.get(section, "url", fallback=None)
        desc = config.get(section, "description", fallback="")
        if label and url:
            tools.append((label, url, desc))
    return tools

# === GUI Popup ===
def launch_popup():
    root.after(0, show_popup)

def show_popup():
    tools = load_tools()
    if not tools:
        return

    dark = is_dark_mode()
    bg_color = "#1e1e1e" if dark else "#f0f0f0"
    fg_color = "#ffffff" if dark else "#000000"
    subtext_color = "#aaaaaa" if dark else "gray"

    height = 100 + len(tools) * 90
    popup = tk.Toplevel()
    popup.title("ToolLauncher")
    popup.geometry(f"320x{height}+600+300")
    popup.configure(bg=bg_color)
    popup.attributes("-topmost", True)
    popup.focus_force()

    tk.Label(popup, text="Launch Tools:", bg=bg_color, fg=fg_color, font=("Segoe UI", 12, "bold")).pack(pady=(10, 5))

    for label, url, desc in tools:
        frame = tk.Frame(popup, bg=bg_color)
        frame.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(frame, text=label, font=("Segoe UI", 10, "bold"), anchor="w", bg=bg_color, fg=fg_color).pack(fill=tk.X)
        tk.Label(frame, text=desc, font=("Segoe UI", 9), fg=subtext_color, anchor="w", bg=bg_color).pack(fill=tk.X)

        btn = tk.Button(frame, text="Launch", width=15, command=lambda u=url: (webbrowser.open(u), popup.destroy()))
        btn.pack(pady=4)


    popup.bind("<Escape>", lambda e: popup.destroy())

# === Tray Icon ===
def open_config():
    os.system(f"notepad.exe {resource_path(CONFIG_FILE)}")

def exit_app(icon, item):
    icon.stop()
    root.quit()
    sys.exit()

def create_tray_icon():
    image = Image.open(resource_path(ICON_FILE))
    menu = (
        item("Open Config", open_config),
        item("Exit", exit_app)
    )
    icon = pystray.Icon("ToolLauncher", image, "ToolLauncher", menu)
    threading.Thread(target=icon.run, daemon=True).start()

# === Hotkey Listener ===
def start_hotkey_listener():
    keyboard.add_hotkey(HOTKEY, launch_popup)

# === Main ===
root = tk.Tk()
root.withdraw()

if __name__ == "__main__":
    create_tray_icon()
    threading.Thread(target=start_hotkey_listener, daemon=True).start()
    root.mainloop()
