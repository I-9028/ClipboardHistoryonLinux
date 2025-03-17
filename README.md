# Clipboard History: For Linux
## About the Project
I used to drive Linux daily for a few years and use both Windows 11 and Linux intermittently. Windows has an application, Powertoys, which features Clipboard History, which records items in history, 

There was no similar thing I knew for Linux, so I decided to write something on my own. 

**⚠️ IMPORTANT:** This project **only supports text content**. It does not store or process images, rich text, or files.

This would serve for a good side project, since I hadn't really worked on Linux Apps before.

All the Python files are PEP8 Compliant to the best of my abilities (except for E501 limit), and the shell scripts are POSIX compliant as well, for which I used the `shellcheck` tool.

### Built With
The UI in Python3 was handled by the `gi` module, `evdev` was used for Keyboard Events.

The PEP8 Compliance was checked using [AutoPEP8](https://packagecontrol.io/packages/AutoPEP8)  and POSIX Compliance for the shell scripts by using [Shellcheck](https://github.com/koalaman/shellcheck).

### File hierarchy:

    ├── HotkeyHandler
    │   ├── HotkeyHandler_Wayland.py
    │   └── keyconfig.json
    ├── LICENSE
    ├── README.md
    ├── WaylandCheck.sh
    ├── WaylandClipboard.py
    ├── WaylandStartup.sh
    ├── clipboardStorage.py
    └── removeService.sh

The Clipboard History persists between boots, and can be found at `/home/$USER/.config/clipboard_history.json`. You can change this in the `clipboardStorage.py` and `WaylandClipboard`file. 

If you wish to read the JSON directly, I would recommend using the `json.tool` tool in Python, you can do so as `python3 -m json.tool file.json`

## Getting Started
### Prerequisites
The application requires a **Wayland** display., and having `systemd`
as your **init** system.
Other pre-requisites are:
* `wl-clipboard`
* Python3
	* `venv`
	* `evdev`

The `WaylandCheck.sh` script checks for these pre-requisites and if not found, installs them.
### How to Install
1. Clone the repository using 
	`git clone https://github.com/I-9028/ClipboardHistoryonLinux.git`
	
	Enter into the repo folder by `cd ClipboardHistoryonLinux/`
	
3. Assign executable permissions to the "WaylandCheck.sh" script using

    `chmod +x WaylandCheck.sh`

4. It checks if you have all the required dependencies, and creates a Python Virtual Environment. Run it as follows:

    `sudo ./WaylandCheck.sh`
    
5. Then its the startup script for the application itself,

    `./WaylandStartup.sh`
    
	It starts the service and lets you know if you need to reboot. If it asks you to reboot, please **do so**. For some reason, logging out and re-logging in does not solve the issue.
For this script to work,  the user must be in the *input* group, wich is not very secure. I intend to look for a workaround.
 
4. Monitor the status of the service using

    `systemctl --user status ClipboardHistory.service`

### Uninstallation
If you simply wish to stop the service and remove the Configuration FIles generated, run the `removeService.sh` script as follows:

    ./removeService.sh`
    
This **does not** remove the Virtual Environment. To remove the Virtual Environment, run `sudo rm -rf ClipboardVenv/`

### Usage
By default, the key-bindings are set to `LeftAlt + V`, these can be changed by modifying the `HotkeyHandler/config.json` file. 

## FAQ
1.  I get an error message saying "user is not in sudoers file"

  

	[Follow the instructions here](https://stackoverflow.com/a/47807036), which are:

	`sudo root`

	`nano /etc/sudoers`

  

	In the line below

	`# User privilege specification`

	`root ALL=(ALL:ALL) ALL`

  

	Add

	`username ALL=(ALL:ALL) ALL`

2.  Even after a restart, the window does not show up?

  

	Check the output of the command `id "$USER" | grep input`. If you do not see any output, please manually run `sudo usermod -aG input $USER`. This manually adds you to the `input` user-group.

	Reboot.
## To Do
The following tasks are yet to be undertaken:
1. Look into developing a version that is compatible with X11, maybe by using [wl-clipboard-x11](https://github.com/brunelli/wl-clipboard-x11)
2. It repeatedly causes system to flicker, or mini-freeze, need to look into it.
3. Possibly work on a clone for MacOS.
4. Add Image Support
5. Look into better alternatives for capturing user input than adding user to group "input"