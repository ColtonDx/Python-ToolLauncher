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

DEFAULT_HOTKEY = "ctrl+alt+f"  # Default hotkey if not specified in config
CONFIG_FILE = "ToolLauncher.conf"
ICON_FILE = "ToolLauncher_Logo.ico"
CURRENT_POPUP = None  # Track the current popup window
CURRENT_HOTKEY = DEFAULT_HOTKEY  # Will be updated from config if specified

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

# === Launch Handler ===
def launch_tool(target):
    """Launch either a URL or an executable."""
    if target.lower().startswith(('http://', 'https://', 'www.')):
        # Handle URLs
        webbrowser.open(target)
    else:
        # Handle executable paths
        try:
            # Resolve relative paths from the config file location
            if not os.path.isabs(target):
                base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
                target = os.path.join(base_dir, target)
            
            # Use startfile on Windows, subprocess for other platforms
            if sys.platform == 'win32':
                os.startfile(target)
            else:
                # For Linux/Mac, use appropriate open command
                if sys.platform == 'darwin':  # macOS
                    os.system(f'open "{target}"')
                else:  # Linux
                    os.system(f'xdg-open "{target}"')
        except Exception as e:
            print(f"Error launching {target}: {e}")

# === Load Config ===
def load_tools():
    global CURRENT_HOTKEY
    
    config = configparser.ConfigParser()
    base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
    config_path = os.path.join(base_dir, CONFIG_FILE)
    print(f"Loading config from: {config_path}")
    
    # Check if config file exists
    if not os.path.exists(config_path):
        print(f"Config file not found at: {config_path}")
        return []
    
    config.read(config_path)
    print(f"Sections found in config: {config.sections()}")
    
    # Get settings if specified in [Settings] section
    if 'Settings' in config:
        print("Found Settings section")
        # Update hotkey if specified
        hotkey = config['Settings'].get('hotkey', DEFAULT_HOTKEY)
        print(f"Settings - Hotkey: {hotkey}")
        if hotkey != CURRENT_HOTKEY:
            update_hotkey(hotkey)
    
    tools = []
    # Skip Settings section when processing tools
    for section in [s for s in config.sections() if s != 'Settings']:
        # Use section name as label, but allow override with explicit label
        label = config.get(section, "label", fallback=section)
        
        # Try url first, then path, then command
        target = (config.get(section, "url", fallback=None) or
                 config.get(section, "path", fallback=None) or
                 config.get(section, "command", fallback=None))
        desc = config.get(section, "description", fallback="")
        category = config.get(section, "category", fallback="")
        
        # Only require target now, since label will always have a value
        if target:
            tools.append((label, target, desc, category))
    return tools

# === GUI Popup ===
def launch_popup():
    root.after(0, show_popup)

def show_popup():
    global CURRENT_POPUP
    
    # If there's an existing popup, destroy it
    if CURRENT_POPUP is not None and CURRENT_POPUP.winfo_exists():
        CURRENT_POPUP.destroy()
    
    tools = load_tools()
    if not tools:
        return

    # Group tools by category (empty category -> "General")
    categories = {}
    for label, url, desc, category in tools:
        key = category.strip() if category and category.strip() else "General"
        categories.setdefault(key, []).append((label, url, desc))

    dark = is_dark_mode()
    bg_color = "#1e1e1e" if dark else "#f0f0f0"
    fg_color = "#ffffff" if dark else "#000000"
    subtext_color = "#aaaaaa" if dark else "gray"

    # Calculate max width needed for each category's content
    col_padding = 20
    min_col_width = 200  # Minimum width per column
    num_cols = max(1, len(categories))
    
    # First pass: calculate needed width for each category
    col_widths = {}
    for cat, items in categories.items():
        # Get max width needed for this category's items
        cat_width = len(cat) * 10  # Estimate pixels needed for category name
        for label, _, desc in items:
            # Estimate pixels needed for longest line (label or description)
            item_width = max(len(label) * 8, len(desc) * 6)  # Rough pixel estimate
            cat_width = max(cat_width, item_width)
        col_widths[cat] = max(min_col_width, cat_width + 40)  # Add padding
    
    # compute max rows and total width
    max_rows = max(len(items) for items in categories.values())
    height = 100 + max_rows * 90
    width = sum(col_widths.values()) + (num_cols + 1) * col_padding

    CURRENT_POPUP = tk.Toplevel()
    CURRENT_POPUP.title("ToolLauncher")
    # place near center-ish; geometry requires int
    CURRENT_POPUP.geometry(f"{int(width)}x{int(height)}+600+300")
    CURRENT_POPUP.configure(bg=bg_color)
    CURRENT_POPUP.attributes("-topmost", True)
    CURRENT_POPUP.focus_force()

    header = tk.Label(CURRENT_POPUP, text="Launch Tools:", bg=bg_color, fg=fg_color, font=("Segoe UI", 14, "bold"))
    header.pack(pady=(10, 15))

    content_frame = tk.Frame(CURRENT_POPUP, bg=bg_color)
    content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    # Create a column for each category
    for col_index, (cat, items) in enumerate(categories.items()):
        col_frame = tk.Frame(content_frame, bg=bg_color)
        col_frame.grid(row=0, column=col_index, sticky="n", padx=(10, 10))

        # Category header with underline
        cat_label = tk.Label(col_frame, text=cat, 
                            font=("Segoe UI", 12, "bold"), 
                            bg=bg_color, fg=fg_color)
        cat_label.pack(anchor="w", pady=(0, 2))
        
        # Simple underline
        tk.Frame(col_frame, height=1, 
                bg="#404040" if dark else "#cccccc").pack(fill=tk.X, pady=(0, 12))

        # Calculate fixed box dimensions based on column width
        box_width = col_widths[cat] - 20  # Account for padding
        box_height = 80  # Fixed height for all boxes
        
        for label, url, desc in items:
            # Create clickable frame with border and fixed size
            tool_frame = tk.Frame(col_frame, bg=bg_color, relief="solid",
                                borderwidth=1, cursor="hand2",
                                width=box_width, height=box_height)
            tool_frame.pack(pady=4)
            tool_frame.pack_propagate(False)  # Maintain fixed size
            
            # Border color
            border_color = "#404040" if dark else "#dddddd"
            tool_frame.configure(highlightbackground=border_color,
                               highlightthickness=1)
            
            # Inner padding frame
            inner_frame = tk.Frame(tool_frame, bg=bg_color)
            inner_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
            
            # Labels with wrapping
            title_label = tk.Label(inner_frame, text=label, 
                                 font=("Segoe UI", 10, "bold"),
                                 anchor="w", bg=bg_color, fg=fg_color,
                                 wraplength=box_width - 20)  # Account for padding
            title_label.pack(fill=tk.X)
            
            desc_frame = tk.Frame(inner_frame, bg=bg_color)
            desc_frame.pack(fill=tk.BOTH, expand=True)
            
            desc_label = tk.Label(desc_frame, text=desc, 
                                font=("Segoe UI", 9),
                                fg=subtext_color, anchor="nw", 
                                justify=tk.LEFT, bg=bg_color,
                                wraplength=box_width - 20)  # Account for padding
            desc_label.pack(fill=tk.BOTH, expand=True)
            
            # Bind click and hover events
            def on_click(target=url):
                launch_tool(target)
                CURRENT_POPUP.destroy()
            
            def on_enter(e, frame=tool_frame):
                hover_bg = "#2d2d2d" if dark else "#e8e8e8"
                frame.configure(bg=hover_bg)
                for widget in frame.winfo_children():
                    widget.configure(bg=hover_bg)
                    for subwidget in widget.winfo_children():
                        subwidget.configure(bg=hover_bg)
                    # Handle nested frames (desc_frame)
                    if isinstance(widget, tk.Frame):
                        for sub in widget.winfo_children():
                            sub.configure(bg=hover_bg)
            
            def on_leave(e, frame=tool_frame):
                frame.configure(bg=bg_color)
                for widget in frame.winfo_children():
                    widget.configure(bg=bg_color)
                    for subwidget in widget.winfo_children():
                        subwidget.configure(bg=bg_color)
                    # Handle nested frames (desc_frame)
                    if isinstance(widget, tk.Frame):
                        for sub in widget.winfo_children():
                            sub.configure(bg=bg_color)
            
            # Bind events to the main frame
            tool_frame.bind("<Button-1>", lambda e, u=url: on_click(u))
            tool_frame.bind("<Enter>", on_enter)
            tool_frame.bind("<Leave>", on_leave)
            
            # Make all widgets in the hierarchy clickable
            def make_clickable(widget):
                widget.bind("<Button-1>", lambda e, u=url: on_click(u))
                widget.bind("<Enter>", lambda e, f=tool_frame: on_enter(e, f))
                widget.bind("<Leave>", lambda e, f=tool_frame: on_leave(e, f))
                widget.configure(cursor="hand2")
                if isinstance(widget, tk.Frame):
                    for child in widget.winfo_children():
                        make_clickable(child)
            
            make_clickable(inner_frame)

    CURRENT_POPUP.bind("<Escape>", lambda e: CURRENT_POPUP.destroy())

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
def update_hotkey(new_hotkey):
    global CURRENT_HOTKEY
    # Remove old hotkey if it exists
    try:
        keyboard.remove_hotkey(CURRENT_HOTKEY)
    except:
        pass
    # Set new hotkey
    CURRENT_HOTKEY = new_hotkey
    keyboard.add_hotkey(CURRENT_HOTKEY, launch_popup)
    print(f"ToolLauncher hotkey updated to: {CURRENT_HOTKEY}")

def start_hotkey_listener():
    # Load config first to get initial hotkey
    config = configparser.ConfigParser()
    config_path = resource_path(CONFIG_FILE)
    if os.path.exists(config_path):
        config.read(config_path)
        if 'Settings' in config:
            initial_hotkey = config['Settings'].get('hotkey', DEFAULT_HOTKEY)
        else:
            initial_hotkey = DEFAULT_HOTKEY
    else:
        initial_hotkey = DEFAULT_HOTKEY
    
    update_hotkey(initial_hotkey)

# === Main ===
root = tk.Tk()
root.withdraw()

if __name__ == "__main__":
    create_tray_icon()
    threading.Thread(target=start_hotkey_listener, daemon=True).start()
    root.mainloop()
