# ESP32 Controller — Serial GUI

A modern desktop application for controlling the built-in LED of an ESP32 board over Serial (UART) communication, with a real-time serial monitor.

Built with **Python**, **CustomTkinter**, and **PySerial**.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-informational)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)

---

## 📸 Screenshot

> _Add a screenshot of the running application here._
>
> ```
> ![ESP32 Controller Screenshot](docs/screenshot.png)
> ```

---

## ✨ Features

- 🔌 **Automatic COM port detection** with refresh button
- ⚙️ **Selectable baud rate** (9600 → 230400)
- 🟢 **LED ON / OFF control** with visual state indicator
- 📟 **Real-time Serial Monitor** with color-coded messages:
  - 🔵 Blue — commands sent
  - 🟢 Green — messages received
  - 🟡 Amber — system events
  - 🔴 Red — errors
- 🕒 **Timestamped log lines** with auto-scroll
- 🎨 **Modern, clean UI** (rounded cards, dark terminal, responsive layout)
- 🛡️ **Robust error handling** — no crashes on unplug or busy port
- 🧵 **Thread-safe serial I/O** — GUI never freezes
- 📖 **Built-in documentation** accessible from the app
- 📦 **Single-file `.exe` build** with PyInstaller
- 🧾 **Installable with Inno Setup** (Windows installer)

---

## 📋 Requirements

- **Python** 3.10 or newer (3.11–3.12 recommended)
- **Windows 10/11** (Linux/macOS should also work)
- An **ESP32 development board** connected via USB
- USB-to-Serial driver (CH340 or CP210x, depending on your board)

### Python packages

| Package | Purpose |
| --- | --- |
| `customtkinter` | Modern themed Tkinter widgets |
| `pyserial` | Serial (COM) port communication |
| `pyinstaller` | _(Optional)_ Build standalone `.exe` |

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/ESP32_GUI_UART.git
cd ESP32_GUI_UART
```

### 2. Install dependencies

```bash
pip install customtkinter pyserial
```

### 3. (Optional) Install the packaging tools

```bash
pip install pyinstaller
```

---

## ▶️ Usage

### Run from source

```bash
python esp32_gui.py
```

### Steps

1. Plug in your ESP32 via USB.
2. Click **↻ Refresh Ports** and select the COM port.
3. Select the **baud rate** (default `115200`).
4. Click **Connect**.
5. Use the **TURN LED ON** / **TURN LED OFF** buttons.
6. Watch live messages in the **Serial Monitor**.

Click **ⓘ Documentation** in the header to open the built-in help dialog.

---

## 🔧 ESP32 Firmware

Upload the following sketch to your ESP32 using the Arduino IDE.  
Required board package: **esp32 by Espressif Systems** (Boards Manager).

```cpp
#include <Arduino.h>

#define LED_PIN 2          // Built-in LED (see notes below)
#define BAUD_RATE 115200

String buffer = "";

void setup() {
  Serial.begin(BAUD_RATE);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  delay(500);
  Serial.println("ESP32 ready. Send ON or OFF.");
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (buffer.length() > 0) {
        handleCommand(buffer);
        buffer = "";
      }
    } else {
      buffer += c;
    }
  }
}

void handleCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();

  if (cmd == "ON") {
    digitalWrite(LED_PIN, HIGH);
    Serial.println("LED is ON");
  }
  else if (cmd == "OFF") {
    digitalWrite(LED_PIN, LOW);
    Serial.println("LED is OFF");
  }
  else if (cmd == "STATUS") {
    Serial.print("LED state: ");
    Serial.println(digitalRead(LED_PIN) ? "ON" : "OFF");
  }
  else {
    Serial.print("Unknown command: ");
    Serial.println(cmd);
  }
}
```

### Built-in LED pin reference

| Board | LED Pin | Note |
| --- | --- | --- |
| ESP32 DevKit (WROOM-32) | `2` | Most common |
| ESP32-WROVER | `2` | — |
| ESP32-S3 | `48` or `38` | Board-dependent |
| ESP32-C3 | `8` | **Active LOW** (invert logic) |

### Supported commands

| Command | Action |
| --- | --- |
| `ON` | Turns the LED on |
| `OFF` | Turns the LED off |
| `STATUS` | Returns the current LED state |

Commands must end with a newline (`\n`).

---

## 📦 Building a Windows `.exe`

Run from the project folder:

```bash
python -m PyInstaller --onefile --windowed --name "ESP32_Controller" ^
  --collect-all customtkinter ^
  esp32_gui.py
```

The executable will be at `dist/ESP32_Controller.exe`.

### Creating a Windows installer (optional)

1. Install [Inno Setup](https://jrsoftware.org/isdl.php).
2. Open **Inno Setup Compiler** → **File → New…** → follow the wizard.
3. Add the `dist/` folder as your application files.
4. Compile → produces a single `setup.exe`.

---

## 🛠️ Troubleshooting

| Problem | Fix |
| --- | --- |
| **No COM ports found** | Install the CH340 or CP210x USB driver, then click **Refresh Ports**. |
| **Port is busy / cannot open** | Close the Arduino IDE Serial Monitor or any other program using the port. |
| **Garbled / unreadable text** | The baud rate must match `Serial.begin()` in the ESP32 firmware. |
| **LED behaves opposite to buttons** | Your board uses an active-LOW LED — invert the logic in the firmware. |
| **ESP32 resets on connect** | Normal — the DTR line toggles when the port opens. |
| **`ModuleNotFoundError: customtkinter`** | Run `pip install customtkinter`. |
| **`.exe` shows blank window** | Rebuild with `--collect-all customtkinter`. |
| **Permission denied on Linux** | Add your user to `dialout`: `sudo usermod -aG dialout $USER`, then log out/in. |

---

## 📁 Project Structure

```
ESP32_GUI_UART/
├── esp32_gui.py           # Main application (GUI + serial logic)
├── esp32_led_uart.ino     # ESP32 firmware
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── LICENSE                # MIT License
└── docs/
    └── screenshot.png     # (Optional) app screenshot
```

---

## 📄 `requirements.txt`

Create this file at the root of your repo:

```
customtkinter>=5.2.0
pyserial>=3.5
```

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

1. Fork the project
2. Create your feature branch: `git checkout -b feature/new-feature`
3. Commit your changes: `git commit -m 'Add new feature'`
4. Push to the branch: `git push origin feature/new-feature`
5. Open a Pull Request

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**AHMED F. ALNAHHAL**

- 🌐 Freelancer: [www.freelancer.com/u/anahhal](https://www.freelancer.com/u/anahhal)
- 💼 Embedded systems · IoT · Desktop tools

---

## ⭐ Acknowledgements

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — modern Tkinter widgets
- [PySerial](https://github.com/pyserial/pyserial) — serial communication
- [Espressif](https://www.espressif.com/) — ESP32 platform
