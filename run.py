import tkinter as tk
import configparser
import webbrowser
import os

CONFIG_FILE = "config.conf"

# === Load Config ===
if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError(f"{CONFIG_FILE} not found. Please create it with tool definitions.")

config = configparser.ConfigParser()
config.read(CONFIG_FILE)

# === GUI ===
root = tk.Tk()
root.title("ClipPilot Launcher")
root.geometry("300x400+600+300")
root.configure(bg="#f0f0f0")

tk.Label(root, text="Launch Tools:", bg="#f0f0f0", font=("Segoe UI", 12, "bold")).pack(pady=10)

# === Dynamic Buttons ===
for section in config.sections():
    label = config.get(section, "label", fallback=None)
    url = config.get(section, "url", fallback=None)

    if label and url:
        tk.Button(
            root,
            text=label,
            command=lambda u=url: webbrowser.open(u)
        ).pack(fill=tk.X, padx=20, pady=5)

tk.Button(root, text="Exit", command=root.quit).pack(fill=tk.X, padx=20, pady=10)

root.mainloop()
