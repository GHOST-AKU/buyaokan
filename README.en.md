# Input Device Tester

[中文](README.md)

A lightweight, local-first Windows utility for checking whether your keyboard, mouse, touchpad, and other HID devices are actually being detected — and whether their input events work in real time.

![Windows](https://img.shields.io/badge/platform-Windows-0078D4)
![Python](https://img.shields.io/badge/Python-3.x-3776AB)
![License](https://img.shields.io/badge/license-MIT-green)
![Network](https://img.shields.io/badge/network-none-lightgrey)

## What it can test

- **Keyboard** — visual key feedback and detected-key counting.
- **Mouse** — movement, left/right/middle clicks, double-clicks, and wheel events.
- **Touchpad** — checks the mouse-style events that Windows exposes for touchpad movement, taps, clicks, and scrolling.
- **Connected input devices** — lists keyboards, mice, touchpads, and other HID devices reported by Windows, including device status information.
- **Local-only diagnostics** — the source code contains no network upload logic.

Useful when you are checking a new laptop, troubleshooting a suspicious key or touchpad, verifying a repair, or simply trying to answer: **“Is Windows actually seeing this input device?”**

## Quick start

### Use the prebuilt executable

Download:

`release/InputDeviceTester.exe`

Then run it directly. Python is not required.

> The executable is currently unsigned. Windows Defender / SmartScreen may show a warning. Verify the download source before running it.

### Run from source

Requirements:

- Windows
- Python 3
- No third-party Python runtime dependencies

Run:

```bat
run_input_device_tester.bat
```

or:

```powershell
python .\input_device_tester.py
```

## Build the EXE

Install PyInstaller:

```powershell
python -m pip install pyinstaller
```

Then run:

```bat
build_exe.bat
```

The executable will be generated at:

```text
release\InputDeviceTester.exe
```

## Privacy

Input Device Tester reads input-device information reported by Windows and displays interaction events inside the app. The source code does not include any network upload functionality.

## Notes

- Windows only.
- Touchpads are commonly exposed through mouse-style events, so this tool is intended as a practical functional check rather than a raw precision-touchpad protocol analyzer.
- Device names and status information depend on what Windows and the installed drivers report.

## License

MIT License. See [LICENSE](LICENSE).

---

If this tiny tool saved you from wondering whether a keyboard, mouse, or touchpad was broken, consider giving the repository a ⭐.
