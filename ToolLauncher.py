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

CONFIG_FILE = "ToolLauncher.conf"
HOTKEY = "ctrl+shift+v"

# === Load Config ===
def load_tools():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    tools = []
    for section in config.sections():
        label = config.get(section, "label", fallback=None)
        url = config.get(section, "url", fallback=None)
        if label and url:
            tools.append((label, url))
    return tools

# === GUI Popup ===
def launch_popup():
    tools = load_tools()
    if not tools:
        return

    popup = tk.Toplevel()
    popup.title("ToolLauncher")
    popup.geometry("300x400+600+300")
    popup.configure(bg="#f0f0f0")
    popup.focus_force()

    tk.Label(popup, text="Launch Tools:", bg="#f0f0f0", font=("Segoe UI", 12, "bold")).pack(pady=10)

    for label, url in tools:
        tk.Button(
            popup,
            text=label,
            command=lambda u=url: (webbrowser.open(u), popup.destroy())
        ).pack(fill=tk.X, padx=20, pady=5)

    tk.Button(popup, text="Cancel", command=popup.destroy).pack(fill=tk.X, padx=20, pady=10)
    popup.bind("<Escape>", lambda e: popup.destroy())

# === Tray Icon ===
def open_config():
    os.system(f"notepad.exe {CONFIG_FILE}")

def exit_app(icon, item):
    icon.stop()
    root.quit()
    sys.exit()

def create_tray_icon():
    image = Image.open("ToolLauncher_Logo.ico")  # Replace with your icon path
    menu = (
        item("Open Config", open_config),
        item("Exit", exit_app)
    )
    icon = pystray.Icon("ToolLauncher", image, "ToolLauncher", menu)
    threading.Thread(target=icon.run, daemon=True).start()

# === Hotkey Listener ===
def start_hotkey_listener():
    keyboard.add_hotkey(HOTKEY, launch_popup)
    print(f"🛠️ ToolLauncher hotkey active — Press {HOTKEY} to launch.")
    keyboard.wait()

# === Main ===
root = tk.Tk()
root.withdraw()

if __name__ == "__main__":
    create_tray_icon()
    threading.Thread(target=start_hotkey_listener, daemon=True).start()
    root.mainloop()
