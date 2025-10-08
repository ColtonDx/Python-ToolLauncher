**ToolLauncher**

ToolLauncher is a lightweight Windows utility that lets you launch your favorite tools and dashboards with a single hotkey. It reads from a simple config file and dynamically builds a GUI with buttons that open URLs in your default browser.

**Features**

- Hotkey-triggered launcher (default: Ctrl+Shift+V)  
- System tray icon with config access and exit  
- Config-driven tool list with labels, URLs, and descriptions  
- Dynamic window sizing based on number of tools  
- Clean, minimal interface with subtext descriptions  

**Installation**

1. Clone or download the repository  
2. Ensure Python 3 is installed  
3. Install dependencies:  
   - tkinter (included with Python)  
   - pystray  
   - pillow  
   - keyboard  
4. Place your icon file as `ToolLauncher_Logo.ico` in the same directory  
5. Create a config file named `ToolLauncher.conf`  

**Config Format**

ToolLauncher.conf should use INI format. Each section defines a tool with a label, URL, and optional description.

Example:

[Tool1]  
label = Azure Portal  
url = https://portal.azure.com  
description = Manage cloud resources and subscriptions  

[Tool2]  
label = GitHub  
url = https://github.com  
description = Access repositories and version control  

**Usage**

- Run `ToolLauncher.py`  
- Press Ctrl+Shift+V to open the launcher  
- Click any "Launch" button to open the corresponding URL  
- Use the tray icon to open the config or exit the app  

**Customization**

- Change the hotkey by modifying the `HOTKEY` variable in the script  
- Add or remove tools by editing `ToolLauncher.conf`  
- Replace `ToolLauncher_Logo.ico` with your own icon  
