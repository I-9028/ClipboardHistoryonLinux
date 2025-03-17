#!/bin/sh

# Get Python version
PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
PYTHON_VER=$(echo "$PYTHON_VERSION" | cut -d "." -f 1,2)

# Other Variables
GROUP="input"
# Paths
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
VENV_DIR="$SCRIPT_DIR/ClipboardVenv"

# Install system dependencies
echo "Installing required system packages..."
sudo apt update && sudo apt install -y wl-clipboard python3-gi gir1.2-gtk-3.0 python3-evdev \
    python"$PYTHON_VER"-venv python"$PYTHON_VER"-dev gcc linux-headers-"$(uname -r)"

# Create virtual environment
echo "Setting up Python virtual environment..."
if [ -d "$VENV_DIR" ]; then
    echo "Existing virtual environment found. Recreate? (y/n): "
    read -r RECREATE
    [ "$RECREATE" = "y" ] || [ "$RECREATE" = "Y" ] && rm -rf "$VENV_DIR"
fi

# Create venv if it doesn't exist
[ ! -d "$VENV_DIR" ] && python3 -m venv "$VENV_DIR"

# Activate venv and install packages
if [ -f "$VENV_DIR/bin/activate" ]; then
    . "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install evdev
else
    echo "Error: Virtual environment activation failed!"
    exit 1
fi
echo

# Check for WaylandStartup.sh script
if [ -f "$SCRIPT_DIR/WaylandStartup.sh" ]; then
    echo "Please run the WaylandStartup script to set up the systemd script."
else
    echo "WaylandStartup.sh not found in $SCRIPT_DIR"
    exit 1
fi