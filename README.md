**ToolLauncher**

ToolLauncher is a lightweight Windows utility that lets you launch your favorite tools and dashboards with a single hotkey. It reads from a simple config file and dynamically builds a GUI with buttons that open URLs in your default browser.

**Features**

- Hotkey-triggered launcher (default: Ctrl+Alt+F)  
- System tray icon with config access and exit  
- Config-driven tool list with labels, URLs, and descriptions  
- Dynamic window sizing based on number of tools  
- Clean, minimal interface with dark/light mode support  
- Automatic config creation on first run  
- Easy config editing via "Open Config" menu option  

**Installation**

1. Clone or download the repository  
2. Ensure Python 3 is installed  
3. Install dependencies:  
   - tkinter (included with Python)  
   - pystray  
   - pillow  
   - keyboard  
4. Place your icon file as `ToolLauncher_Logo.ico` in the same directory  

**Config File**

The config file is automatically created on first run if it doesn't exist. 

**Location:**
- **Compiled EXE:** Same directory as the executable
- **Development (Python script):** Same directory as ToolLauncher.py

**Auto-Creation:**
When you first run ToolLauncher, a default config file (`ToolLauncher.conf`) is automatically created with a sample tool (Notepad launcher). You can then customize it by using the "Open Config" option.

**Format**

ToolLauncher.conf uses INI format. Each section defines a tool with a URL or Path, optional label, description, and category. Tools are organized into columns by category.

Example:
```
[Settings]
hotkey = ctrl+alt+f

[Tool1]  
label = Azure Portal  
url = https://portal.azure.com  
description = Manage cloud resources and subscriptions  
category = Cloud

[GitHub]  
url = https://github.com  
description = Access repositories and version control  
category = Code

[Tool3]
path = C:\Windows\System32\calc.exe
description = Windows Calculator
category = Apps
```

**Usage**

1. Run `ToolLauncher.py` or the compiled EXE  
2. Press **Ctrl+Alt+F** (or your custom hotkey) to open the launcher  
3. Click any tool button to launch it  
4. **To edit the config:** Right-click the tray icon and select **"Open Config"** to open it in Notepad  
5. After editing the config, restart the application for changes to take effect

**Customization**

- **Change the hotkey:** Edit the `hotkey` setting in the Settings section of the config file, then right-click the tray icon and select "Open Config" to modify it  
- **Add or remove tools:** Right-click the tray icon, select "Open Config", edit the file, and restart the application  
- **Replace the icon:** Replace `ToolLauncher_Logo.ico` with your own icon file (must be in .ico format)  
- **Categories:** Tools are automatically organized into columns based on their `category` field

**Building an EXE**

To package as a standalone EXE using PyInstaller:
```
pyinstaller --icon=ToolLauncher_Logo.ico --onefile --windowed ToolLauncher.py
```

Place the generated EXE and `ToolLauncher_Logo.ico` in the same folder for the app to function correctly.  
