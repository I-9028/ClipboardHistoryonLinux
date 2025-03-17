import sys
import os
import shutil
import subprocess
import threading

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

from clipboardStorage import load_history_from_file, save_history_to_file


HISTORY_FILE = os.path.expanduser("~/.config/clipboard_history.json")


class ClipboardHistoryApp(Gtk.Window):
    def __init__(self, start_hidden=False):
        Gtk.init(None)
        super().__init__(title="Clipboard History Viewer")
        self.set_border_width(10)
        self.set_default_size(600, 400)

        # Window state flags
        self.is_configuring = False
        self.is_visible = not start_hidden
        self.programmatic_copy = False
        self.clipboard_lock = threading.Lock()

        # Main vertical box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        # Create a scrolled window for the TreeView
        scroll_window = Gtk.ScrolledWindow()
        scroll_window.set_vexpand(True)
        vbox.pack_start(scroll_window, True, True, 0)

        # Create ListStore and TreeView
        self.clipboard_store = Gtk.ListStore(str, str)  # Preview, Full Content
        self.tree_view = Gtk.TreeView(model=self.clipboard_store)

        # Add columns
        preview_column = Gtk.TreeViewColumn("Preview")
        preview_cell = Gtk.CellRendererText()
        preview_column.pack_start(preview_cell, True)
        preview_column.add_attribute(preview_cell, "text", 0)
        self.tree_view.append_column(preview_column)

        full_column = Gtk.TreeViewColumn("Full Content")
        full_cell = Gtk.CellRendererText()
        full_column.pack_start(full_cell, True)
        full_column.add_attribute(full_cell, "text", 1)
        self.tree_view.append_column(full_column)

        # Enable selection
        self.tree_view.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
        self.tree_view.connect("row-activated", self.on_row_activated)
        scroll_window.add(self.tree_view)

        # Buttons
        button_box = Gtk.Box(spacing=6)
        clear_button = Gtk.Button(label="Clear Clipboard")
        clear_button.connect("clicked", self.on_clear_clicked)
        copy_button = Gtk.Button(label="Copy Selected")
        copy_button.connect("clicked", self.on_copy_clicked)
        button_box.pack_start(clear_button, True, True, 0)
        button_box.pack_start(copy_button, True, True, 0)
        vbox.pack_start(button_box, False, False, 0)

        # Initialize clipboard history and last content
        self.clipboard_history = load_history_from_file()
        self.update_clipboard_display()
        self.last_content = ""

        # Connect signals for window management
        self.connect("destroy", self.on_destroy)
        self.connect("delete-event", self.on_delete_event)
        self.connect("configure-event", self.on_configure_event)
        self.connect("focus-in-event", self.on_focus_event)
        self.connect("focus-out-event", self.on_focus_event)

        # Start periodic clipboard checking
        GLib.timeout_add(1000, self.check_clipboard_changes)

        # Handle window state
        if not start_hidden:
            self.show_all()

        # Create a Unix domain socket for IPC
        self.setup_ipc()

    def on_configure_event(self, widget, event):
        """Handle window resize and move events."""
        self.is_configuring = True
        GLib.timeout_add(300, self.reset_configuring)
        return False  # Allow the event to propagate

    def on_focus_event(self, widget, event):
        """Handle window focus events."""
        self.is_configuring = True
        GLib.timeout_add(200, self.reset_configuring)
        return False  # Allow the event to propagate

    def reset_configuring(self):
        """Reset the configuration flag after a delay."""
        self.is_configuring = False
        return False  # Don't repeat the timeout

    def setup_ipc(self):
        import socket
        import threading
        self.socket_path = "/tmp/clipboard_history.sock"
        if os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except OSError as e:
                print(f"Error removing socket file: {e}")
                return
        try:
            self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.server.bind(self.socket_path)
            self.server.listen(1)
            threading.Thread(target=self.handle_ipc, daemon=True).start()
        except Exception as e:
            print(f"Error setting up IPC: {e}")

    def handle_ipc(self):
        while True:
            try:
                conn, _ = self.server.accept()
                data = conn.recv(1024).decode()
                if data == "toggle":
                    GLib.idle_add(self.toggle_visibility)
                conn.close()
            except Exception as e:
                print(f"IPC error: {e}")
                # Small delay to avoid tight loop in case of repeated errors
                import time
                time.sleep(0.1)

    def toggle_visibility(self):
        try:
            if self.is_visible:
                self.hide()
                self.is_visible = False
            else:
                self.show_all()
                self.is_visible = True
                self.present()  # Bring window to front
        except Exception as e:
            print(f"Error toggling visibility: {e}")
        return False  # Don't repeat

    def get_clipboard_type(self):
        if self.is_configuring:
            return None

        try:
            result = subprocess.run(
                ["wl-paste", "--list-types"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            targets = result.stdout.strip().split('\n')
            if result.returncode != 0 or not result.stdout.strip():
                return None
            # Only check for text types now
            text_types = ['text/plain', 'UTF8_STRING', 'TEXT', 'STRING']
            for target in targets:
                if target.strip() in text_types:
                    return 'text/plain'
            return None
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error getting clipboard type: {e}")
            return None

    def get_clipboard_content(self):
        if self.is_configuring:
            return None, None

        content_type = self.get_clipboard_type()
        if not content_type:
            return None, None

        try:
            if content_type == 'text/plain':
                result = subprocess.run(
                    ["wl-paste", "--no-newline"],
                    stdout=subprocess.PIPE,
                    text=True,
                    check=True
                )
                return result.stdout.strip(), 'text'
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error getting clipboard content: {e}")
            return None, None
        return None, None

    def check_clipboard_changes(self):
        try:
            # Skip clipboard checks only if we're in the middle of certain operations
            if self.programmatic_copy or self.is_configuring:
                return True

            with self.clipboard_lock:
                content, content_type = self.get_clipboard_content()
                if content and content != self.last_content:
                    self.last_content = content
                    if content_type == 'text' and \
                            (not self.clipboard_history or
                             content != self.clipboard_history[-1][0]):
                        self.clipboard_history.append((content, content_type))
                        GLib.idle_add(self.update_clipboard_display)
                        # Save history when a new entry is added
                        save_history_to_file(self.clipboard_history)
        except Exception as e:
            print(f"Error checking clipboard: {e}")
        return True  # Continue the timeout

    def on_clear_clicked(self, widget):
        try:
            with self.clipboard_lock:
                subprocess.run(["wl-copy", "--clear"], check=True)
                self.clipboard_history.clear()
                self.last_content = ""
                self.update_clipboard_display()
                open(HISTORY_FILE, "w").close()
        except Exception as e:
            print(f"Error clearing clipboard: {e}")

    def on_copy_clicked(self, widget):
        try:
            if self.programmatic_copy or self.is_configuring:
                return

            selection = self.tree_view.get_selection()
            model, tree_iter = selection.get_selected()
            if tree_iter:
                content = model.get_value(tree_iter, 1)
                self.programmatic_copy = True
                with self.clipboard_lock:
                    subprocess.run(["wl-copy"], input=content, text=True)
                # Reset the flag after a delay
                GLib.timeout_add(500, self.reset_programmatic_copy)
        except Exception as e:
            print(f"Error copying selection: {e}")
            self.programmatic_copy = False

    def on_row_activated(self, treeview, path, column):
        try:
            if self.programmatic_copy or self.is_configuring:
                return

            model = treeview.get_model()
            tree_iter = model.get_iter(path)
            content = model.get_value(tree_iter, 1)
            self.programmatic_copy = True
            with self.clipboard_lock:
                subprocess.run(["wl-copy"], input=content, text=True)
            # Reset the flag after a delay
            GLib.timeout_add(500, self.reset_programmatic_copy)
        except Exception as e:
            print(f"Error activating row: {e}")
            self.programmatic_copy = False

    def reset_programmatic_copy(self):
        self.programmatic_copy = False
        return False  # Don't repeat the timeout

    def update_clipboard_display(self):
        try:
            self.clipboard_store.clear()
            for content, content_type in self.clipboard_history:
                if content_type == 'text':
                    preview = (content[:50] + '...') if len(content) > 50 else content
                    preview = preview.replace('\n', ' ')
                    self.clipboard_store.append([preview, content])
        except Exception as e:
            print(f"Error updating display: {e}")
        return False  # Don't repeat if called via idle_add

    def on_delete_event(self, widget, event):
        try:
            # Save history when window is closed
            with self.clipboard_lock:
                save_history_to_file(self.clipboard_history)
        except Exception as e:
            print(f"Error saving history on delete: {e}")
        return False  # Allow the destroy signal to be emitted

    def on_destroy(self, widget):
        try:
            # Final cleanup
            with self.clipboard_lock:
                save_history_to_file(self.clipboard_history)
            # Clean up socket
            if hasattr(self, 'server'):
                self.server.close()
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)
        except Exception as e:
            print(f"Error during cleanup: {e}")
        Gtk.main_quit()


def checkRequiredComponents():
    print("WAYLAND_DISPLAY:", os.environ.get('WAYLAND_DISPLAY'))
    try:
        _, _ = Gtk.init_check(None)
    except Exception as e:
        print("Gtk.init_check() failed:", e)
        return False
    if not (shutil.which("wl-paste") and shutil.which("wl-copy")):
        print("wl-clipboard tools (wl-paste and wl-copy) are required but not installed.")
        return False
    return True


def main():
    if not checkRequiredComponents():
        return
    start_hidden = "--hidden" in sys.argv
    win = ClipboardHistoryApp(start_hidden=start_hidden)
    Gtk.main()


if __name__ == "__main__":
    main()
