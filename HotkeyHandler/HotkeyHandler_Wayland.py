import os
import json
import subprocess
import socket
from evdev import InputDevice, categorize, ecodes, list_devices
from select import select
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='/tmp/hotkey_handler.log'
)

FILE_NAME = 'WaylandClipboard.py'


class KeyConfig:
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'keyconfig.json')
        self.default_config = {
            'hotkey': {
                'modifiers': ['KEY_LEFTALT'],
                'key': 'KEY_V'
            }
        }
        self.load_config()
        logging.info(f"Loaded key config: {self.config}")

    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error loading config: {e}")
            self.config = self.default_config
            # self.save_config()


class HotkeyListener:
    def __init__(self):
        self.key_config = KeyConfig()
        self.devices = self.get_keyboard_devices()
        logging.info(f"Found keyboard devices: {[dev.name for dev in self.devices]}")
        self.pressed_keys = set()
        self.socket_path = "/tmp/clipboard_history.sock"

    def get_keyboard_devices(self):
        """ Get all keyboard input devices """
        devices = [InputDevice(path) for path in list_devices()]
        keyboard_devices = [dev for dev in devices if
                            ("keyboard" in dev.name.lower() or
                             dev.capabilities().get(ecodes.EV_KEY))]

        if not keyboard_devices:
            logging.error("No keyboard devices found!")
        return keyboard_devices

    def toggle_gui(self):
        """ Send toggle command to the running GUI process """
        logging.info("Attempting to toggle GUI")
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.connect(self.socket_path)
            sock.send(b"toggle")
            sock.close()
            logging.info("Successfully sent toggle command")
        except (ConnectionRefusedError, FileNotFoundError) as e:
            logging.error(f"Failed to connect to GUI process: {e}")
            self.launch_gui()

    def launch_gui(self):
        """ Launch the GUI script in hidden mode """
        try:
            script_dir = os.path.dirname(os.path.realpath(__file__))
            parent_dir = os.path.dirname(script_dir)
            gui_path = os.path.join(parent_dir, FILE_NAME)

            logging.info(f"Launching GUI from path: {gui_path}")

            # Get necessary environment variables
            env = os.environ.copy()

            # Use the full path to python from the virtual environment if available
            venv_dir = os.path.join(parent_dir, "ClipboardVenv")
            if os.path.exists(venv_dir):
                python_path = os.path.join(venv_dir, "bin", "python3")
            else:
                python_path = "python3"

            # Launch with subprocess and wait briefly to ensure it starts
            process = subprocess.Popen(
                [python_path, gui_path, '--hidden'],
                env=env,
                start_new_session=True  # This detaches the process
            )

            # Log the process ID for debugging
            logging.info(f"Started GUI process with PID: {process.pid}")

        except Exception as e:
            logging.error(f"Error launching GUI: {e}", exc_info=True)

    def listen(self):
        """ Listen for keypress events """
        try:
            modifier_keys = {ecodes.ecodes[key]
                             for key in self.key_config.config['hotkey']['modifiers']}
            main_key = ecodes.ecodes[self.key_config.config['hotkey']['key']]
            logging.info(f"Listening for modifier keys: {modifier_keys}\
                and main key: {main_key}")
        except KeyError as e:
            logging.error(f"Error setting up key codes: {e}")
            return

        while True:
            try:
                r, _, _ = select(self.devices, [], [])
                for dev in r:
                    try:
                        for event in dev.read():
                            if event.type == ecodes.EV_KEY:
                                key_event = categorize(event)
                                key_code = key_event.scancode
                                key_name = ecodes.KEY[key_event.scancode]

                                if key_event.keystate == key_event.key_down:
                                    self.pressed_keys.add(key_code)
                                    logging.debug(f"Key pressed: {key_name} ({key_code})")
                                elif key_event.keystate == key_event.key_up:
                                    self.pressed_keys.discard(key_code)
                                    logging.debug(f"Key released: {key_name} ({key_code})")

                                # Log current state of pressed keys
                                logging.debug(f"Currently pressed keys: {self.pressed_keys}")
                                logging.debug(f"Looking for modifiers: {modifier_keys}")
                                logging.debug(f"Looking for main key: {main_key}")

                                # Check if all modifier keys and the main key are pressed
                                if modifier_keys.issubset(self.pressed_keys)\
                                        and main_key in self.pressed_keys:
                                    logging.info("Hotkey combination detected!")
                                    self.toggle_gui()
                    except Exception as e:
                        logging.error(f"Error reading from device: {e}")
            except Exception as e:
                logging.error(f"Error in main event loop: {e}")


def main():
    logging.info("Starting clipboard history in background...")
    # Start the clipboard history application in hidden mode
    script_dir = os.path.dirname(os.path.realpath(__file__))
    parent_dir = os.path.dirname(script_dir)
    gui_path = os.path.join(parent_dir, FILE_NAME)
    subprocess.Popen(['python3', gui_path, '--hidden'])

    logging.info("Hotkey listener is running...")
    listener = HotkeyListener()
    listener.listen()


if __name__ == "__main__":
    main()
