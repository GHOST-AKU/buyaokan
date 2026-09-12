# Input Device Tester

一个仅支持 Windows 的输入设备自检工具，用于查看系统识别到的键盘、鼠标、触摸板和其他 HID 设备，并实时测试按键、移动、点击、双击与滚轮事件。

## 直接使用

下载 `release/InputDeviceTester.exe` 后双击运行，不需要安装 Python。

如果 Windows Defender 对未签名程序发出提示，请自行核对下载来源及文件内容后再决定是否运行。

## 从源码运行

需要 Windows 和 Python 3。项目只使用 Python 标准库。

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

生成的程序位于 `release\InputDeviceTester.exe`，临时构建文件位于 `build\`。

## 隐私说明

程序在本机读取 Windows 报告的输入设备信息，并在窗口内显示交互事件；源码不包含网络上传功能。

## 许可证

本项目采用 [MIT License](LICENSE) 开源。
