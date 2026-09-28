# Input Device Tester

[English](README.en.md)

一个轻量、完全本地运行的 Windows 输入设备自检工具。用它快速确认：**键盘、鼠标、触摸板和其他 HID 设备到底有没有被 Windows 正确识别，以及输入事件是否真的正常。**

![Windows](https://img.shields.io/badge/platform-Windows-0078D4)
![Python](https://img.shields.io/badge/Python-3.x-3776AB)
![License](https://img.shields.io/badge/license-MIT-green)
![Network](https://img.shields.io/badge/network-none-lightgrey)

## 它能检查什么

- **键盘**：按键实时高亮，并统计已经检测到的按键。
- **鼠标**：移动、左键、右键、中键、双击和滚轮事件。
- **触摸板**：检查 Windows 暴露出来的移动、轻触/点击和滚动等鼠标式事件。
- **系统输入设备**：读取 Windows 报告的键盘、鼠标、触摸板及其他 HID 设备，并显示设备状态。
- **纯本地诊断**：源码不包含网络上传逻辑。

它很适合这些场景：

- 新电脑到手，快速验键盘、鼠标和触摸板；
- 怀疑某个按键失灵，但不确定是硬件还是系统问题；
- 换键盘、修电脑之后做功能复查；
- 想快速确认：**“Windows 到底有没有识别到这个输入设备？”**

## 直接使用

下载：

`release/InputDeviceTester.exe`

双击即可运行，不需要安装 Python。

> 当前 EXE 未做代码签名，因此 Windows Defender / SmartScreen 可能弹出提示。请先确认下载来源，再决定是否运行。

## 从源码运行

要求：

- Windows
- Python 3
- 运行时仅使用 Python 标准库

运行：

```bat
run_input_device_tester.bat
```

也可以直接运行：

```powershell
python .\input_device_tester.py
```

## 构建 EXE

先安装 PyInstaller：

```powershell
python -m pip install pyinstaller
```

然后运行：

```bat
build_exe.bat
```

生成文件位于：

```text
release\InputDeviceTester.exe
```

## 隐私说明

Input Device Tester 只读取 Windows 报告的输入设备信息，并在程序窗口里显示交互事件。源码中不包含网络上传功能。

## 注意事项

- 仅支持 Windows。
- 触摸板通常会被 Windows 映射为鼠标式事件，因此这里更偏向“功能是否正常”的实用检测，而不是底层 Precision Touchpad 协议分析。
- 设备名称与状态取决于 Windows 和驱动程序实际报告的内容。

## 许可证

MIT License，详见 [LICENSE](LICENSE)。

---

如果这个小工具帮你少折腾了一会儿键盘、鼠标或触摸板，欢迎顺手点个 ⭐。
