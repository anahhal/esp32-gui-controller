"""
ESP32 Controller — Modern Serial GUI
Framework : CustomTkinter
Requires  : customtkinter, pyserial
Author    : AHMED F. ALNAHHAL
"""

import queue
import threading
import time
import webbrowser
from datetime import datetime

import customtkinter as ctk
import serial
import serial.tools.list_ports


# ============================================================
#  Theme
# ============================================================
COLOR_BG          = "#F5F7FA"
COLOR_CARD        = "#FFFFFF"
COLOR_CARD_BORDER = "#E2E8F0"
COLOR_PRIMARY     = "#2563EB"
COLOR_PRIMARY_HOV = "#1D4ED8"
COLOR_SUCCESS     = "#10B981"
COLOR_SUCCESS_HOV = "#059669"
COLOR_DANGER      = "#EF4444"
COLOR_DANGER_HOV  = "#DC2626"
COLOR_TEXT        = "#1E293B"
COLOR_MUTED       = "#64748B"
COLOR_DISABLED    = "#94A3B8"
COLOR_TERMINAL_BG = "#0F172A"
COLOR_TERM_TEXT   = "#E2E8F0"
COLOR_TERM_SENT   = "#60A5FA"
COLOR_TERM_RECV   = "#34D399"
COLOR_TERM_SYS    = "#FBBF24"
COLOR_TERM_ERR    = "#F87171"
COLOR_TERM_TIME   = "#64748B"

# ============================================================
#  Credits
# ============================================================
AUTHOR_NAME = "AHMED F. ALNAHHAL"
AUTHOR_URL  = "https://www.freelancer.com/u/anahhal"
APP_VERSION = "v1.0.0"

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class ESP32ControllerApp(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title("ESP32 Controller")
        self.geometry("900x900")
        self.minsize(820, 760)
        self.configure(fg_color=COLOR_BG)

        # state
        self.serial_port = None
        self.reader_thread = None
        self.running = False
        self.msg_queue = queue.Queue()
        self.led_state = False
        self._closing = False

        # layout: header, middle row, serial monitor (expands), footer
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_middle_row()
        self._build_serial_card()
        self._build_footer()

        self.refresh_ports(silent=True)
        self.after(80, self._process_queue)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # =========================================================
    #  UI BUILDERS
    # =========================================================
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 6))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="ESP32 Controller",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=COLOR_TEXT,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header, text="Serial Communication & LED Control",
            font=ctk.CTkFont(size=13),
            text_color=COLOR_MUTED,
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        # About button (top-right)
        ctk.CTkButton(
            header, text="ⓘ  Documentation", command=self._show_about,
            width=150, height=34, corner_radius=8,
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOV,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=1, rowspan=2, sticky="e")

    def _build_middle_row(self):
        middle = ctk.CTkFrame(self, fg_color="transparent")
        middle.grid(row=1, column=0, sticky="ew", padx=20, pady=8)
        middle.grid_columnconfigure(0, weight=1, uniform="mid")
        middle.grid_columnconfigure(1, weight=1, uniform="mid")

        self._build_connection_card(middle, col=0)
        self._build_led_card(middle, col=1)

    def _make_card(self, parent, title):
        card = ctk.CTkFrame(
            parent, fg_color=COLOR_CARD, corner_radius=14,
            border_width=1, border_color=COLOR_CARD_BORDER,
        )
        ctk.CTkLabel(
            card, text=title.upper(),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_MUTED,
        ).pack(anchor="w", padx=18, pady=(14, 6))
        return card

    # ---------- Connection card ----------
    def _build_connection_card(self, parent, col):
        card = self._make_card(parent, "Connection")
        card.grid(row=0, column=col, sticky="nsew",
                  padx=(0, 8) if col == 0 else (8, 0))

        status_row = ctk.CTkFrame(card, fg_color="transparent")
        status_row.pack(fill="x", padx=18, pady=(0, 8))

        ctk.CTkLabel(
            status_row, text="Status:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXT,
        ).pack(side="left")

        self.status_dot = ctk.CTkLabel(
            status_row, text="●",
            font=ctk.CTkFont(size=16),
            text_color=COLOR_DISABLED,
        )
        self.status_dot.pack(side="left", padx=(6, 4))

        self.status_label = ctk.CTkLabel(
            status_row, text="Disconnected",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_MUTED,
        )
        self.status_label.pack(side="left")

        fields = ctk.CTkFrame(card, fg_color="transparent")
        fields.pack(fill="x", padx=18)
        fields.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            fields, text="COM Port",
            font=ctk.CTkFont(size=12), text_color=COLOR_TEXT,
        ).grid(row=0, column=0, sticky="w", pady=4)

        self.port_combo = ctk.CTkComboBox(
            fields, values=[""], state="readonly", height=32, corner_radius=8,
            border_color=COLOR_CARD_BORDER,
            button_color=COLOR_PRIMARY, button_hover_color=COLOR_PRIMARY_HOV,
            dropdown_fg_color=COLOR_CARD, font=ctk.CTkFont(size=12),
        )
        self.port_combo.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=4)

        ctk.CTkLabel(
            fields, text="Baud Rate",
            font=ctk.CTkFont(size=12), text_color=COLOR_TEXT,
        ).grid(row=1, column=0, sticky="w", pady=4)

        self.baud_combo = ctk.CTkComboBox(
            fields,
            values=["9600", "19200", "38400", "57600", "115200", "230400"],
            state="readonly", height=32, corner_radius=8,
            border_color=COLOR_CARD_BORDER,
            button_color=COLOR_PRIMARY, button_hover_color=COLOR_PRIMARY_HOV,
            dropdown_fg_color=COLOR_CARD, font=ctk.CTkFont(size=12),
        )
        self.baud_combo.set("115200")
        self.baud_combo.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=4)

        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(fill="x", padx=18, pady=(14, 16))

        self.refresh_btn = ctk.CTkButton(
            btns, text="↻  Refresh Ports", command=self.refresh_ports,
            height=34, corner_radius=8,
            fg_color="#E2E8F0", hover_color="#CBD5E1", text_color=COLOR_TEXT,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.refresh_btn.pack(fill="x", pady=(0, 6))

        self.connect_btn = ctk.CTkButton(
            btns, text="Connect", command=self.connect_serial,
            height=34, corner_radius=8,
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOV,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.connect_btn.pack(fill="x", pady=6)

        self.disconnect_btn = ctk.CTkButton(
            btns, text="Disconnect", command=self.disconnect_serial,
            height=34, corner_radius=8,
            fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOV,
            font=ctk.CTkFont(size=12, weight="bold"),
            state="disabled",
        )
        self.disconnect_btn.pack(fill="x", pady=(6, 0))

    # ---------- LED card ----------
    def _build_led_card(self, parent, col):
        card = self._make_card(parent, "LED Control")
        card.grid(row=0, column=col, sticky="nsew",
                  padx=(0, 8) if col == 0 else (8, 0))

        state_row = ctk.CTkFrame(card, fg_color="transparent")
        state_row.pack(fill="x", padx=18, pady=(4, 14))

        self.led_dot = ctk.CTkLabel(
            state_row, text="●",
            font=ctk.CTkFont(size=28), text_color=COLOR_DISABLED,
        )
        self.led_dot.pack(side="left", padx=(0, 8))

        self.led_status = ctk.CTkLabel(
            state_row, text="LED: OFF",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLOR_MUTED,
        )
        self.led_status.pack(side="left")

        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(fill="x", padx=18, pady=(0, 16))

        self.on_btn = ctk.CTkButton(
            btns, text="●  TURN LED ON", command=self.led_on,
            height=48, corner_radius=10,
            fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOV,
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled",
        )
        self.on_btn.pack(fill="x", pady=(0, 8))

        self.off_btn = ctk.CTkButton(
            btns, text="●  TURN LED OFF", command=self.led_off,
            height=48, corner_radius=10,
            fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOV,
            font=ctk.CTkFont(size=14, weight="bold"),
            state="disabled",
        )
        self.off_btn.pack(fill="x", pady=(8, 0))

    # ---------- Serial monitor card ----------
    def _build_serial_card(self):
        card = self._make_card(self, "Serial Monitor")
        card.grid(row=2, column=0, sticky="nsew", padx=20, pady=(8, 8))

        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(0, 6))

        ctk.CTkButton(
            head, text="Clear Log", command=self.clear_log,
            width=90, height=28, corner_radius=8,
            fg_color="#E2E8F0", hover_color="#CBD5E1", text_color=COLOR_TEXT,
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="right")

        self.log_text = ctk.CTkTextbox(
            card, corner_radius=10,
            fg_color=COLOR_TERMINAL_BG, text_color=COLOR_TERM_TEXT,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word", border_width=0,
        )
        self.log_text.pack(fill="both", expand=True, padx=18, pady=(0, 16))
        self.log_text.configure(state="disabled")

        inner = getattr(self.log_text, "_textbox", self.log_text)
        inner.tag_config("sent", foreground=COLOR_TERM_SENT)
        inner.tag_config("recv", foreground=COLOR_TERM_RECV)
        inner.tag_config("sys",  foreground=COLOR_TERM_SYS)
        inner.tag_config("err",  foreground=COLOR_TERM_ERR)
        inner.tag_config("time", foreground=COLOR_TERM_TIME)

    # =========================================================
    #  FOOTER  (always-visible credits)
    # =========================================================
    def _build_footer(self):
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))
        footer.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            footer,
            text=f"Developed by {AUTHOR_NAME}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_TEXT,
        ).grid(row=0, column=0, sticky="w")

        link = ctk.CTkLabel(
            footer, text="www.freelancer.com/u/anahhal",
            font=ctk.CTkFont(size=11, underline=True),
            text_color=COLOR_PRIMARY, cursor="hand2",
        )
        link.grid(row=0, column=1, sticky="w", padx=(10, 0))
        link.bind("<Button-1>", lambda e: webbrowser.open(AUTHOR_URL))

        ctk.CTkLabel(
            footer, text=APP_VERSION,
            font=ctk.CTkFont(size=11),
            text_color=COLOR_MUTED,
        ).grid(row=0, column=2, sticky="e")

    # =========================================================
    #  DOCUMENTATION DIALOG
    # =========================================================
    def _show_about(self):
        win = ctk.CTkToplevel(self)
        win.title("Documentation — ESP32 Controller")
        win.geometry("620x680")
        win.transient(self)
        win.grab_set()
        win.configure(fg_color=COLOR_BG)

        ctk.CTkLabel(
            win, text="Documentation",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLOR_TEXT,
        ).pack(anchor="w", padx=24, pady=(20, 0))

        ctk.CTkLabel(
            win, text=f"ESP32 Controller  ·  {APP_VERSION}",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_MUTED,
        ).pack(anchor="w", padx=24, pady=(2, 12))

        body = ctk.CTkScrollableFrame(
            win, fg_color=COLOR_CARD, corner_radius=12,
            border_width=1, border_color=COLOR_CARD_BORDER,
        )
        body.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        def h(text):
            ctk.CTkLabel(
                body, text=text,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLOR_PRIMARY,
            ).pack(anchor="w", padx=16, pady=(16, 4))

        def p(text):
            ctk.CTkLabel(
                body, text=text, justify="left", wraplength=520,
                font=ctk.CTkFont(size=12), text_color=COLOR_TEXT,
            ).pack(anchor="w", padx=16, pady=(0, 2))

        h("Overview")
        p("A desktop application to control the built-in LED of an ESP32 "
          "board over a Serial (UART) connection and view live messages "
          "sent back from the microcontroller.")

        h("Getting Started")
        p("1.  Connect the ESP32 to your PC using a USB cable.")
        p("2.  Click 'Refresh Ports' and select the COM port of your ESP32.")
        p("3.  Choose the baud rate (default is 115200).")
        p("4.  Click 'Connect'.")
        p("5.  Use the LED buttons to turn the built-in LED on or off.")
        p("6.  Watch incoming messages in the Serial Monitor below.")

        h("Supported Commands")
        p("ON         →  Turns the built-in LED on.")
        p("OFF        →  Turns the built-in LED off.")
        p("STATUS     →  Requests the current LED state from the ESP32.")
        p("Each command must be terminated with a newline (\\n).")

        h("Serial Monitor — Color Legend")
        p("Blue    →  Commands sent to the ESP32")
        p("Green   →  Messages received from the ESP32")
        p("Amber   →  System / connection events")
        p("Red     →  Errors and warnings")
        p("Every line is timestamped (HH:MM:SS).")

        h("Troubleshooting")
        p("•  Port not listed?   Install the CH340 or CP210x USB driver, "
          "then click Refresh Ports.")
        p("•  Port busy?   Close the Arduino IDE Serial Monitor or any "
          "other program using the port.")
        p("•  Garbled text?   The baud rate must match Serial.begin() in "
          "your ESP32 firmware.")
        p("•  ESP32 resets on connect?   This is normal — the DTR signal "
          "toggles when the port opens.")

        h("About the Author")
        p(f"Developed by {AUTHOR_NAME}.")
        p("Freelance services in embedded systems, IoT, and desktop tools.")

        link = ctk.CTkLabel(
            body, text=AUTHOR_URL,
            font=ctk.CTkFont(size=12, underline=True),
            text_color=COLOR_PRIMARY, cursor="hand2",
        )
        link.pack(anchor="w", padx=16, pady=(4, 16))
        link.bind("<Button-1>", lambda e: webbrowser.open(AUTHOR_URL))

        ctk.CTkButton(
            win, text="Close", command=win.destroy,
            width=120, height=36, corner_radius=8,
            fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOV,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(pady=(0, 18))

        # center on parent window
        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - win.winfo_width())  // 2
        y = self.winfo_y() + (self.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    # =========================================================
    #  PORT / SERIAL
    # =========================================================
    def refresh_ports(self, silent=False):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo.configure(values=ports if ports else [""])

        if ports:
            current = self.port_combo.get()
            if current not in ports:
                self.port_combo.set(ports[0])
            if not silent:
                self._log("sys", f"Found {len(ports)} port(s): {', '.join(ports)}")
        else:
            self.port_combo.set("")
            if not silent:
                self._log("err", "No serial ports found. Plug in your ESP32 and click Refresh.")

    def connect_serial(self):
        if self.serial_port and self.serial_port.is_open:
            return

        port = self.port_combo.get().strip()
        baud = self.baud_combo.get().strip()

        if not port:
            self._log("err", "No COM port selected. Click Refresh and pick a port.")
            return

        try:
            self.serial_port = serial.Serial(port, int(baud), timeout=0.1)
        except Exception as e:
            self._log("err", f"Connection failed: {e}")
            self.serial_port = None
            return

        time.sleep(1.8)

        self.running = True
        self.reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.reader_thread.start()

        self._set_connected_ui(True, port, baud)
        self._log("sys", f"Connected to {port} @ {baud} baud")

    def disconnect_serial(self):
        if self.serial_port:
            self.running = False
            time.sleep(0.2)
            try:
                if self.serial_port.is_open:
                    self.serial_port.close()
            except Exception:
                pass
            self.serial_port = None

        self._set_connected_ui(False)
        self._log("sys", "Disconnected.")

    def _reader_loop(self):
        while self.running:
            try:
                if (self.serial_port and self.serial_port.is_open
                        and self.serial_port.in_waiting):
                    line = self.serial_port.readline().decode(errors="ignore").strip()
                    if line:
                        self.msg_queue.put(("recv", line))
                else:
                    time.sleep(0.05)
            except Exception as e:
                self.msg_queue.put(("err", f"Serial read error: {e}"))
                self.msg_queue.put(("__disconnect__", None))
                break

    def send_command(self, cmd):
        if not (self.serial_port and self.serial_port.is_open):
            self._log("err", "Not connected. Connect to the ESP32 first.")
            return False
        try:
            self.serial_port.write((cmd + "\n").encode())
            self._log("sent", cmd)
            return True
        except Exception as e:
            self._log("err", f"Send failed: {e}")
            return False

    # =========================================================
    #  BUTTON HANDLERS
    # =========================================================
    def led_on(self):
        if self.send_command("ON"):
            self.led_state = True
            self._update_led_visual()

    def led_off(self):
        if self.send_command("OFF"):
            self.led_state = False
            self._update_led_visual()

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    # =========================================================
    #  UI STATE
    # =========================================================
    def _set_connected_ui(self, connected, port=None, baud=None):
        if connected:
            self.status_dot.configure(text_color=COLOR_SUCCESS)
            self.status_label.configure(
                text=f"Connected · {port}",
                text_color=COLOR_SUCCESS,
            )
            self.connect_btn.configure(state="disabled")
            self.disconnect_btn.configure(state="normal")
            self.refresh_btn.configure(state="disabled")
            self.port_combo.configure(state="disabled")
            self.baud_combo.configure(state="disabled")
            self.on_btn.configure(state="normal")
            self.off_btn.configure(state="normal")
        else:
            self.status_dot.configure(text_color=COLOR_DISABLED)
            self.status_label.configure(text="Disconnected", text_color=COLOR_MUTED)
            self.connect_btn.configure(state="normal")
            self.disconnect_btn.configure(state="disabled")
            self.refresh_btn.configure(state="normal")
            self.port_combo.configure(state="readonly")
            self.baud_combo.configure(state="readonly")
            self.on_btn.configure(state="disabled")
            self.off_btn.configure(state="disabled")
            self.led_state = False
            self._update_led_visual()

    def _update_led_visual(self):
        if self.led_state:
            self.led_dot.configure(text_color=COLOR_SUCCESS)
            self.led_status.configure(text="LED: ON", text_color=COLOR_SUCCESS)
        else:
            self.led_dot.configure(text_color=COLOR_DISABLED)
            self.led_status.configure(text="LED: OFF", text_color=COLOR_MUTED)

    # =========================================================
    #  THREAD-SAFE LOG
    # =========================================================
    def _log(self, kind, message):
        self.msg_queue.put((kind, message))

    def _append_log(self, kind, message):
        ts = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "sent": "→ Sent: ",
            "recv": "← Received: ",
            "sys":  "● System: ",
            "err":  "⚠ Error: ",
        }.get(kind, "")

        self.log_text.configure(state="normal")
        inner = getattr(self.log_text, "_textbox", self.log_text)
        inner.insert("end", f"[{ts}] ", "time")
        inner.insert("end", prefix + message + "\n", kind)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _process_queue(self):
        if self._closing:
            return
        try:
            while True:
                kind, message = self.msg_queue.get_nowait()
                if kind == "__disconnect__":
                    self._handle_forced_disconnect()
                else:
                    self._append_log(kind, message)
        except queue.Empty:
            pass
        finally:
            self.after(80, self._process_queue)

    def _handle_forced_disconnect(self):
        was_running = self.running
        if self.serial_port:
            try:
                self.serial_port.close()
            except Exception:
                pass
            self.serial_port = None
        self.running = False
        self._set_connected_ui(False)
        if was_running:
            self._append_log("err", "ESP32 disconnected unexpectedly.")

    # =========================================================
    #  CLOSE
    # =========================================================
    def _on_close(self):
        self._closing = True
        self.running = False
        try:
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.close()
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    app = ESP32ControllerApp()
    app.mainloop()
