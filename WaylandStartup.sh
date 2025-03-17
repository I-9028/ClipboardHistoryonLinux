#!/bin/sh

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
VENV_DIR=$SCRIPT_DIR/"ClipboardVenv"
VENV_PYTHON="$VENV_DIR/bin/python3"
SERVICE_NAME="ClipboardHistory.service"
USER_SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_FILE="$USER_SERVICE_DIR/$SERVICE_NAME"
GROUP="input"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment not found at $VENV_DIR"
    echo "Please run the installation script first."
    exit 1
fi

# Check if user is in group "input"
if id -nGz "$USER" | grep -qzxF "$GROUP"
then
    echo User "$USER" belongs to group "$GROUP"
else
    echo User "$USER" does not belong to group "$GROUP"
    echo "Adding ""$USER"" to group ""$GROUP"""
    echo "Please do so by running"
    echo "sudo usermod -aG ""$GROUP"" ""$USER"""
    echo "Please reboot for this to take effect. Logging out does not work."
fi

# Create the user service directory if it doesn't exist
mkdir -p "$USER_SERVICE_DIR"

# Create the systemd service file
cat > "$SERVICE_FILE" <<EOL
[Unit]
Description=Clipboard History Hotkey Listener (Wayland)
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
ExecStart=${VENV_PYTHON} ${SCRIPT_DIR}/HotkeyHandler/HotkeyHandler_Wayland.py
Restart=on-failure
RestartSec=10
WorkingDirectory=${SCRIPT_DIR}
Environment=WAYLAND_DISPLAY=%t/wayland-0
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=%t/bus
Environment=XDG_RUNTIME_DIR=%t
Environment=PYTHONPATH=${SCRIPT_DIR}
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical-session.target
EOL

# Reload systemd daemon
systemctl --user daemon-reload

# Enable and start the service
systemctl --user enable "$SERVICE_NAME"
systemctl --user start "$SERVICE_NAME"

echo "ClipboardHistory installed as a user service."
echo "Check status with: systemctl --user status $SERVICE_NAME"
