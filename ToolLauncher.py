import tkinter as tk
import configparser
import webbrowser
import threading
import subprocess
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
def get_config_path():
    """Get the full path to the config file in AppData."""
    appdata_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "ToolLauncher")
    return os.path.join(appdata_dir, CONFIG_FILE)

def ensure_config_exists():
    """Ensure the config file exists and create default one if not."""
    config_path = get_config_path()
    config_dir = os.path.dirname(config_path)
    
    # Create AppData directory if it doesn't exist
    if not os.path.exists(config_dir):
        try:
            os.makedirs(config_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating config directory: {e}")
            return
    
    # Create default config if it doesn't exist
    if not os.path.exists(config_path):
        try:
            config = configparser.ConfigParser()
            
            # Add Settings section with default hotkey
            config['Settings'] = {
                'hotkey': DEFAULT_HOTKEY
            }
            
            # Add a sample tool section
            config['Sample_Tool'] = {
                'label': 'Open Notepad',
                'path': 'notepad.exe',
                'description': 'Launch Windows Notepad',
                'category': 'Utilities'
            }
            
            # Save the default config
            with open(config_path, 'w') as f:
                config.write(f)
            print(f"Created default config at: {config_path}")
        except Exception as e:
            print(f"Error creating default config: {e}")

def load_tools():
    config = configparser.ConfigParser()
    config_path = get_config_path()
    # Check if config file exists
    if not os.path.exists(config_path):
        return []
    config.read(config_path)
    
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

    # Create header frame with title and settings button
    header_frame = tk.Frame(CURRENT_POPUP, bg=bg_color)
    header_frame.pack(pady=(10, 15), padx=10, fill=tk.X)
    
    header = tk.Label(header_frame, text="Launch Tools:", bg=bg_color, fg=fg_color, font=("Segoe UI", 14, "bold"))
    header.pack(side=tk.LEFT, expand=True)
    
    # Settings button (cog icon)
    def open_settings():
        show_settings_dialog(CURRENT_POPUP, dark, bg_color, fg_color)
    
    settings_btn = tk.Button(header_frame, text="⚙", bg=bg_color, fg=fg_color, 
                             font=("Segoe UI", 12), relief=tk.FLAT, 
                             command=open_settings, cursor="hand2")
    settings_btn.pack(side=tk.RIGHT, padx=5)
    settings_btn.configure(activebackground=("#2d2d2d" if dark else "#e8e8e8"))
    settings_btn.configure(activeforeground=fg_color)

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

# === Settings Dialog ===
def save_config(config):
    """Save config to file."""
    config_path = get_config_path()
    try:
        with open(config_path, 'w') as f:
            config.write(f)
        print("Configuration saved successfully")
        return True
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return False

def show_settings_dialog(parent_window, dark, bg_color, fg_color):
    """Show settings dialog for hotkey and adding new tools."""
    settings_window = tk.Toplevel(parent_window)
    settings_window.title("Settings")
    settings_window.geometry("480x420+700+350")
    settings_window.configure(bg=bg_color)
    settings_window.attributes("-topmost", True)
    
    # Load current config
    config = configparser.ConfigParser()
    config_path = get_config_path()
    if os.path.exists(config_path):
        config.read(config_path)
    
    subtext_color = "#999999" if dark else "#666666"
    entry_bg = "#2d2d2d" if dark else "#ffffff"
    entry_fg = "#ffffff" if dark else "#000000"
    border_color = "#3e3e42" if dark else "#d0d0d0"
    
    # Configure styles for cleaner look
    settings_window.option_add("*Font", "Segoe UI 10")
    
    # === Main content frame ===
    main_frame = tk.Frame(settings_window, bg=bg_color)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
    
    # === Hotkey Section ===
    tk.Label(main_frame, text="Hotkey", bg=bg_color, fg=fg_color, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
    
    current_hotkey = get_configured_hotkey()
    hotkey_entry = tk.Entry(main_frame, bg=entry_bg, fg=entry_fg, font=("Segoe UI", 10),
                            relief=tk.SOLID, borderwidth=1)
    hotkey_entry.insert(0, current_hotkey)
    hotkey_entry.pack(fill=tk.X, pady=(0, 4))
    
    tk.Label(main_frame, text="e.g., ctrl+alt+f, shift+alt+d, ctrl+shift+t", 
             bg=bg_color, fg=subtext_color, font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 15))
    
    # === Add New Tool Section ===
    tk.Label(main_frame, text="Add New Tool", bg=bg_color, fg=fg_color, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
    
    # Tool entry fields (compact layout)
    fields = [
        ("Tool Name", "tool_name_entry"),
        ("URL/Path/Command", "tool_target_entry"),
        ("Description (optional)", "tool_desc_entry"),
        ("Category (optional)", "tool_cat_entry")
    ]
    
    entry_vars = {}
    for label, var_name in fields:
        tk.Label(main_frame, text=label, bg=bg_color, fg=fg_color, font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 3))
        entry = tk.Entry(main_frame, bg=entry_bg, fg=entry_fg, font=("Segoe UI", 10),
                        relief=tk.SOLID, borderwidth=1)
        entry.pack(fill=tk.X, pady=(0, 8))
        entry_vars[var_name] = entry
    
    tool_name_entry = entry_vars["tool_name_entry"]
    tool_target_entry = entry_vars["tool_target_entry"]
    tool_desc_entry = entry_vars["tool_desc_entry"]
    tool_cat_entry = entry_vars["tool_cat_entry"]
    
    # === Button Frame ===
    button_frame = tk.Frame(settings_window, bg=bg_color)
    button_frame.pack(pady=(15, 10), fill=tk.X, padx=20)
    
    def save_settings():
        """Save hotkey and new tool to config."""
        new_hotkey = hotkey_entry.get().strip()
        
        # Validate and update hotkey if changed
        if new_hotkey and new_hotkey != CURRENT_HOTKEY:
            try:
                update_hotkey(new_hotkey)
                if 'Settings' not in config:
                    config['Settings'] = {}
                config['Settings']['hotkey'] = new_hotkey
                print(f"Hotkey updated to: {new_hotkey}")
            except Exception as e:
                print(f"Error setting hotkey: {e}")
        
        # Add new tool if fields are filled
        tool_name = tool_name_entry.get().strip()
        tool_target = tool_target_entry.get().strip()
        
        if tool_name and tool_target:
            # Sanitize section name (remove special characters)
            safe_name = "".join(c for c in tool_name if c.isalnum() or c in (' ', '_', '-')).strip()
            if not safe_name:
                safe_name = "Tool"
            
            # Ensure unique section name
            counter = 1
            unique_name = safe_name
            while unique_name in config:
                unique_name = f"{safe_name}{counter}"
                counter += 1
            
            config[unique_name] = {}
            config[unique_name]['label'] = tool_name
            config[unique_name]['url' if tool_target.lower().startswith(('http://', 'https://', 'www.')) else 'path'] = tool_target
            
            if tool_desc_entry.get().strip():
                config[unique_name]['description'] = tool_desc_entry.get().strip()
            
            if tool_cat_entry.get().strip():
                config[unique_name]['category'] = tool_cat_entry.get().strip()
            
            print(f"Tool added: {tool_name}")
        
        # Save config
        if save_config(config):
            settings_window.destroy()
            # Refresh parent popup
            if parent_window and parent_window.winfo_exists():
                parent_window.destroy()
            show_popup()
    
    save_btn = tk.Button(button_frame, text="Save", command=save_settings,
                        bg="#0e639c" if dark else "#007acc", fg="#ffffff",
                        font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=20, pady=6,
                        cursor="hand2")
    save_btn.pack(side=tk.LEFT, padx=(0, 8))
    save_btn.configure(activebackground="#1177bb" if dark else "#0059b8")
    save_btn.configure(activeforeground="#ffffff")
    
    cancel_btn = tk.Button(button_frame, text="Cancel", command=settings_window.destroy,
                          bg="#3e3e42" if dark else "#e0e0e0", fg=fg_color,
                          font=("Segoe UI", 10), relief=tk.FLAT, padx=20, pady=6,
                          cursor="hand2")
    cancel_btn.pack(side=tk.LEFT)
    cancel_btn.configure(activebackground="#555555" if dark else "#d0d0d0")
    cancel_btn.configure(activeforeground=fg_color)

# === Tray Icon ===
def open_config():
    config_path = get_config_path()
    try:
        subprocess.Popen(["notepad.exe", config_path])
    except Exception as e:
        print(f"Error opening config: {e}")

def exit_app(icon, item):
    icon.stop()
    root.quit()
    sys.exit()

def create_tray_icon():
    image = Image.open(resource_path(ICON_FILE))
    menu = (
        item("Launch", lambda i, m: launch_popup()),
        item("Open Config", open_config),
        item("Exit", exit_app)
    )
    icon = pystray.Icon("ToolLauncher", image, "ToolLauncher", menu)
    threading.Thread(target=icon.run, daemon=True).start()

# === Hotkey Listener ===
def get_configured_hotkey():
    """Load the hotkey from config file."""
    config = configparser.ConfigParser()
    config_path = get_config_path()
    if os.path.exists(config_path):
        config.read(config_path)
        if 'Settings' in config:
            hotkey = config['Settings'].get('hotkey', DEFAULT_HOTKEY)
            if hotkey.strip():  # Ensure it's not empty
                return hotkey
    return DEFAULT_HOTKEY

def update_hotkey(new_hotkey):
    global CURRENT_HOTKEY
    # Remove old hotkey if it exists and is different
    if CURRENT_HOTKEY and CURRENT_HOTKEY != new_hotkey:
        try:
            keyboard.remove_hotkey(CURRENT_HOTKEY)
        except Exception as e:
            print(f"Note: Could not remove previous hotkey {CURRENT_HOTKEY}: {e}")
    
    # Set new hotkey
    try:
        CURRENT_HOTKEY = new_hotkey
        keyboard.add_hotkey(CURRENT_HOTKEY, launch_popup)
        print(f"ToolLauncher hotkey set to: {CURRENT_HOTKEY}")
    except Exception as e:
        print(f"Error registering hotkey {new_hotkey}: {e}")
        # Fallback to default if there's an issue
        if new_hotkey != DEFAULT_HOTKEY:
            print(f"Falling back to default hotkey: {DEFAULT_HOTKEY}")
            CURRENT_HOTKEY = DEFAULT_HOTKEY
            keyboard.add_hotkey(CURRENT_HOTKEY, launch_popup)

def start_hotkey_listener():
    """Initialize and register the hotkey from config."""
    initial_hotkey = get_configured_hotkey()
    update_hotkey(initial_hotkey)

# === Main ===
root = tk.Tk()
root.withdraw()

if __name__ == "__main__":
    # Ensure config file exists and create if necessary
    ensure_config_exists()
    # Load and set hotkey BEFORE creating tray icon
    start_hotkey_listener()
    create_tray_icon()
    root.mainloop()
