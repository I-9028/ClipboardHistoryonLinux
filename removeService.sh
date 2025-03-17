#!/bin/sh

systemctl --user stop ClipboardHistory.service 
systemctl --user disable ClipboardHistory.service 

# Remove Configuration Files
rm ~/.config/systemd/user/ClipboardHistory.service

status=$(systemctl --user status ClipboardHistory.service 2>&1)

if echo "$status" | grep -q "Unit ClipboardHistory.service could not be found."; then
    echo "Service Removed Successfully, including config files. Run startup script to restart the service."
else
    echo "Failed to remove service or service is still present."
fi
