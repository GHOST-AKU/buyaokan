import ctypes
import json
import subprocess
import sys
import time
import tkinter as tk
from tkinter import ttk


KEYBOARD_LAYOUT = [
    ["Esc", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"],
    ["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "BackSpace"],
    ["Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "\\"],
    ["Caps_Lock", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "Return"],
    ["Shift_L", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "Shift_R"],
    ["Control_L", "Win", "Alt_L", "space", "Alt_R", "Menu", "Control_R", "Left", "Up", "Down", "Right"],
]


POWERSHELL_DEVICE_SCRIPT = r"""
$ErrorActionPreference = 'SilentlyContinue'

function Emit-Devices($ClassName, $Category) {
    Get-PnpDevice -Class $ClassName | ForEach-Object {
        [PSCustomObject]@{
            category = $Category
            name = $_.FriendlyName
            status = $_.Status
            class = $_.Class
            instanceId = $_.InstanceId
            problemCode = $_.ProblemCode
        }
    }
}

$devices = @()
$devices += Emit-Devices 'Keyboard' 'keyboard'
$devices += Emit-Devices 'Mouse' 'mouse'
$devices += Emit-Devices 'HIDClass' 'hid'
$devices += Get-CimInstance Win32_PointingDevice | ForEach-Object {
    [PSCustomObject]@{
        category = 'pointing'
        name = $_.Name
        status = if ($_.Status) { $_.Status } else { 'Unknown' }
        class = $_.PNPClass
        instanceId = $_.PNPDeviceID
        problemCode = ''
    }
}

$devices | ConvertTo-Json -Depth 3 -Compress
"""


def run_powershell(script):
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        script,
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=15,
        check=False,
    )
    stdout = completed.stdout.strip()
    if completed.returncode != 0 or not stdout:
        return None, completed.stderr.strip() or "PowerShell command failed."
    return stdout, None


def get_system_metrics():
    user32 = ctypes.windll.user32
    metrics = {
        "mouse_present": bool(user32.GetSystemMetrics(19)),
        "mouse_buttons": int(user32.GetSystemMetrics(43)),
        "swap_buttons": bool(user32.GetSystemMetrics(23)),
        "touch_capable": bool(user32.GetSystemMetrics(95)),
        "max_touch_points": int(user32.GetSystemMetrics(95)),
    }
    return metrics


def load_devices():
    stdout, error = run_powershell(POWERSHELL_DEVICE_SCRIPT)
    if error:
        return [], error

    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        return [], "无法解析系统设备列表。"

    if isinstance(parsed, dict):
        parsed = [parsed]

    devices = []
    for item in parsed:
        name = (item.get("name") or "").strip()
        if not name:
            continue
        devices.append(
            {
                "category": item.get("category") or "unknown",
                "name": name,
                "status": item.get("status") or "Unknown",
                "class": item.get("class") or "",
                "instance_id": item.get("instanceId") or "",
                "problem_code": item.get("problemCode") or "",
            }
        )
    return devices, None


def classify_devices(devices):
    summary = {
        "keyboards": [],
        "mice": [],
        "touchpads": [],
        "other_hid": [],
    }

    touchpad_keywords = (
        "touch pad",
        "touchpad",
        "precision touchpad",
        "synaptics",
        "elan",
        "i2c hid device",
        "asus precision",
    )
    mouse_keywords = ("mouse", "trackball", "pointing")

    for device in devices:
        lowered = device["name"].lower()
        category = device["category"]
        if category == "keyboard":
            summary["keyboards"].append(device)
        elif any(keyword in lowered for keyword in touchpad_keywords):
            summary["touchpads"].append(device)
        elif category in {"mouse", "pointing"} or any(keyword in lowered for keyword in mouse_keywords):
            summary["mice"].append(device)
        else:
            summary["other_hid"].append(device)

    return summary


class InputDeviceTesterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("笔记本输入设备检测工具")
        self.root.geometry("1180x760")
        self.root.minsize(920, 560)

        self.devices = []
        self.key_widgets = {}
        self.key_seen = set()
        self.active_keys = set()
        self.event_log_lines = []
        self.motion_events = 0
        self.left_clicks = 0
        self.right_clicks = 0
        self.middle_clicks = 0
        self.double_clicks = 0
        self.scroll_up = 0
        self.scroll_down = 0
        self.last_motion_time = 0.0

        self.status_var = tk.StringVar(value="正在准备检测环境...")
        self.device_summary_var = tk.StringVar(value="正在读取系统设备信息...")
        self.keyboard_stats_var = tk.StringVar(value="已检测按键：0")
        self.mouse_stats_var = tk.StringVar(value="移动 0 次 | 左键 0 | 右键 0 | 中键 0 | 双击 0 | 滚轮上 0 | 滚轮下 0")
        self.touchpad_hint_var = tk.StringVar(
            value="触摸板通常会映射成鼠标移动、点击和滚轮事件；如果两指滚动或轻触没有反应，就值得继续排查。"
        )

        self.build_ui()
        self.refresh_devices()

    def build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        outer = ttk.Frame(self.root)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        self.scroll_canvas = tk.Canvas(outer, highlightthickness=0, bg=self.root.cget("bg"))
        self.scroll_canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=self.scroll_canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.scroll_canvas.configure(yscrollcommand=scrollbar.set)

        content = ttk.Frame(self.scroll_canvas, padding=(0, 0, 0, 0))
        self.scroll_window = self.scroll_canvas.create_window((0, 0), window=content, anchor="nw")

        content.bind("<Configure>", self.on_content_configure)
        self.scroll_canvas.bind("<Configure>", self.on_canvas_configure)
        self.root.bind_all("<MouseWheel>", self.on_app_mousewheel, add=True)

        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(1, weight=1)

        header = ttk.Frame(content, padding=(16, 12))
        header.grid(row=0, column=0, columnspan=2, sticky="nsew")
        header.columnconfigure(0, weight=1)

        title = ttk.Label(header, text="输入设备自检", font=("Microsoft YaHei UI", 20, "bold"))
        title.grid(row=0, column=0, sticky="w")

        status = ttk.Label(header, textvariable=self.status_var, foreground="#0a5c36")
        status.grid(row=1, column=0, sticky="w", pady=(4, 0))

        refresh_btn = ttk.Button(header, text="刷新设备列表", command=self.refresh_devices)
        refresh_btn.grid(row=0, column=1, rowspan=2, sticky="e")

        left_panel = ttk.Frame(content, padding=(16, 0, 10, 16))
        left_panel.grid(row=1, column=0, sticky="nsew")
        left_panel.rowconfigure(2, weight=1)
        left_panel.columnconfigure(0, weight=1)

        info_card = ttk.LabelFrame(left_panel, text="系统识别结果", padding=12)
        info_card.grid(row=0, column=0, sticky="nsew")
        info_card.columnconfigure(0, weight=1)

        ttk.Label(info_card, textvariable=self.device_summary_var, wraplength=620, justify="left").grid(
            row=0, column=0, sticky="w"
        )

        columns = ("category", "name", "status")
        self.device_tree = ttk.Treeview(info_card, columns=columns, show="headings", height=8)
        self.device_tree.heading("category", text="类别")
        self.device_tree.heading("name", text="设备")
        self.device_tree.heading("status", text="状态")
        self.device_tree.column("category", width=90, anchor="center")
        self.device_tree.column("name", width=420)
        self.device_tree.column("status", width=90, anchor="center")
        self.device_tree.grid(row=1, column=0, sticky="nsew", pady=(12, 0))

        keyboard_card = ttk.LabelFrame(left_panel, text="键盘测试", padding=12)
        keyboard_card.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        keyboard_card.columnconfigure(0, weight=1)

        ttk.Label(
            keyboard_card,
            text="按下键盘上的键，按过的键会变成绿色，正在按住的键会显示为橙色。",
            wraplength=620,
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(keyboard_card, textvariable=self.keyboard_stats_var).grid(row=1, column=0, sticky="w", pady=(6, 8))

        key_frame = ttk.Frame(keyboard_card)
        key_frame.grid(row=2, column=0, sticky="nsew")
        self.build_keyboard_grid(key_frame)

        mouse_card = ttk.LabelFrame(left_panel, text="鼠标 / 触摸板交互测试", padding=12)
        mouse_card.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
        mouse_card.rowconfigure(2, weight=1)
        mouse_card.columnconfigure(0, weight=1)

        ttk.Label(
            mouse_card,
            text="在下方区域移动鼠标或触摸板，测试点击、双击、滚轮和两指滚动。",
            wraplength=620,
            justify="left",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(mouse_card, textvariable=self.mouse_stats_var).grid(row=1, column=0, sticky="w", pady=(6, 8))

        self.test_canvas = tk.Canvas(mouse_card, bg="#f7f7f8", highlightthickness=1, highlightbackground="#c7c7cc")
        self.test_canvas.grid(row=2, column=0, sticky="nsew")
        self.test_canvas.create_text(
            320,
            120,
            text="在这里移动 / 点击 / 滚动\n触摸板轻触、按压和两指滚动通常也会触发这里的事件",
            fill="#3f3f46",
            font=("Microsoft YaHei UI", 13),
            justify="center",
        )
        self.bind_mouse_events()

        right_panel = ttk.Frame(content, padding=(10, 0, 16, 16))
        right_panel.grid(row=1, column=1, sticky="nsew")
        right_panel.rowconfigure(1, weight=1)
        right_panel.columnconfigure(0, weight=1)

        touch_card = ttk.LabelFrame(right_panel, text="触摸板检查提示", padding=12)
        touch_card.grid(row=0, column=0, sticky="nsew")
        touch_card.columnconfigure(0, weight=1)

        touch_text = (
            "1. 单指移动光标，看画面中的移动计数是否增加。\n"
            "2. 单指轻触 / 按压左下角，看左键计数是否增加。\n"
            "3. 两指滚动页面，看滚轮上/下计数是否变化。\n"
            "4. 如果系统里识别不到触摸板，或这里完全没有响应，通常是驱动、排线或硬件本体异常。"
        )
        ttk.Label(touch_card, text=touch_text, wraplength=360, justify="left").grid(row=0, column=0, sticky="w")
        ttk.Label(touch_card, textvariable=self.touchpad_hint_var, wraplength=360, justify="left").grid(
            row=1, column=0, sticky="w", pady=(10, 0)
        )

        log_card = ttk.LabelFrame(right_panel, text="实时事件日志", padding=12)
        log_card.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        log_card.rowconfigure(0, weight=1)
        log_card.columnconfigure(0, weight=1)

        self.log_text = tk.Text(log_card, height=20, wrap="word", state="disabled", bg="#fcfcfd")
        self.log_text.grid(row=0, column=0, sticky="nsew")

        hint = ttk.Label(
            right_panel,
            text="如果某些按键、点击或滚轮反复不触发，基本可以判断那个输入通道有问题。",
            wraplength=360,
            justify="left",
            foreground="#7c2d12",
        )
        hint.grid(row=2, column=0, sticky="w", pady=(12, 0))

        self.root.bind_all("<KeyPress>", self.on_key_press, add=True)
        self.root.bind_all("<KeyRelease>", self.on_key_release, add=True)

    def on_content_configure(self, event):
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.scroll_canvas.itemconfigure(self.scroll_window, width=event.width)

    def on_app_mousewheel(self, event):
        if event.widget == self.test_canvas:
            return
        delta = int(-event.delta / 120) if event.delta else 0
        if delta:
            self.scroll_canvas.yview_scroll(delta, "units")

    def build_keyboard_grid(self, parent):
        for row_index, row in enumerate(KEYBOARD_LAYOUT):
            current_col = 0
            for key_name in row:
                width = self.key_width(key_name)
                label = tk.Label(
                    parent,
                    text=key_name,
                    relief="solid",
                    bd=1,
                    bg="#eceef2",
                    padx=8,
                    pady=5,
                    font=("Microsoft YaHei UI", 10),
                )
                label.grid(row=row_index, column=current_col, padx=3, pady=3, sticky="nsew", columnspan=width)
                self.key_widgets[key_name] = label
                current_col += width

        for index in range(24):
            parent.columnconfigure(index, weight=1)

    @staticmethod
    def key_width(key_name):
        if key_name in {"BackSpace", "Caps_Lock", "Return", "Shift_L", "Shift_R"}:
            return 2
        if key_name == "space":
            return 5
        return 1

    def bind_mouse_events(self):
        self.test_canvas.bind("<Motion>", self.on_mouse_motion)
        self.test_canvas.bind("<Button-1>", self.on_left_click)
        self.test_canvas.bind("<Button-2>", self.on_middle_click)
        self.test_canvas.bind("<Button-3>", self.on_right_click)
        self.test_canvas.bind("<Double-Button-1>", self.on_double_click)
        self.test_canvas.bind("<MouseWheel>", self.on_mouse_wheel)

    def refresh_devices(self):
        self.status_var.set("正在读取系统识别到的输入设备...")
        self.root.update_idletasks()

        self.devices, error = load_devices()
        metrics = get_system_metrics()

        for row in self.device_tree.get_children():
            self.device_tree.delete(row)

        if error:
            self.device_summary_var.set(f"读取设备失败：{error}")
            self.status_var.set("设备读取失败，但交互测试仍然可以使用。")
            return

        summary = classify_devices(self.devices)
        for category_name, items in (
            ("键盘", summary["keyboards"]),
            ("鼠标", summary["mice"]),
            ("触摸板", summary["touchpads"]),
            ("其他 HID", summary["other_hid"]),
        ):
            for item in items:
                self.device_tree.insert("", "end", values=(category_name, item["name"], item["status"]))

        ok_touchpad_count = sum(1 for item in summary["touchpads"] if item["status"].lower() == "ok")
        summary_text = (
            f"系统识别到键盘 {len(summary['keyboards'])} 个，鼠标/指点设备 {len(summary['mice'])} 个，"
            f"疑似触摸板 {len(summary['touchpads'])} 个。"
            f" 当前鼠标按钮数：{metrics['mouse_buttons']}，系统报告触控能力："
            f"{'是' if metrics['touch_capable'] else '否'}。"
        )
        if summary["touchpads"]:
            summary_text += f" 其中状态正常的触摸板候选设备有 {ok_touchpad_count} 个。"
            self.touchpad_hint_var.set("系统已经识别到疑似触摸板设备，请重点看轻触、按压和两指滚动是否稳定。")
        else:
            self.touchpad_hint_var.set(
                "系统设备列表里没有明显的触摸板条目。如果你的笔记本本来有触摸板，这本身就比较可疑。"
            )

        abnormal = [item for item in self.devices if str(item["status"]).lower() not in {"ok", "unknown"}]
        if abnormal:
            names = "；".join(item["name"] for item in abnormal[:3])
            summary_text += f" 发现状态异常设备：{names}"
            self.status_var.set("已读取设备列表，存在需要留意的异常状态。")
        else:
            self.status_var.set("设备列表读取完成，可以开始交互测试。")

        self.device_summary_var.set(summary_text)
        self.append_log("系统设备列表已刷新。")

    def normalize_keysym(self, event):
        keysym = event.keysym
        if keysym in {"Super_L", "Super_R"}:
            return "Win"
        return keysym

    def on_key_press(self, event):
        key_name = self.normalize_keysym(event)
        self.key_seen.add(key_name)
        self.active_keys.add(key_name)
        self.update_key_widget(key_name)
        self.keyboard_stats_var.set(f"已检测按键：{len(self.key_seen)}")
        self.append_log(f"键盘：按下 {key_name}")

    def on_key_release(self, event):
        key_name = self.normalize_keysym(event)
        if key_name in self.active_keys:
            self.active_keys.remove(key_name)
        self.update_key_widget(key_name)
        self.append_log(f"键盘：释放 {key_name}")

    def update_key_widget(self, key_name):
        widget = self.key_widgets.get(key_name)
        if not widget:
            return
        if key_name in self.active_keys:
            widget.configure(bg="#ffd59e")
        elif key_name in self.key_seen:
            widget.configure(bg="#cce9d6")
        else:
            widget.configure(bg="#eceef2")

    def on_mouse_motion(self, event):
        now = time.time()
        if now - self.last_motion_time < 0.02:
            return
        self.last_motion_time = now
        self.motion_events += 1
        self.update_mouse_stats()
        self.append_log(f"指针：移动到 ({event.x}, {event.y})", dedupe_prefix="指针：移动到")
        self.draw_pointer(event.x, event.y)

    def on_left_click(self, event):
        self.left_clicks += 1
        self.update_mouse_stats()
        self.append_log(f"鼠标：左键单击 ({event.x}, {event.y})")
        self.flash_marker(event.x, event.y, "#22c55e")

    def on_right_click(self, event):
        self.right_clicks += 1
        self.update_mouse_stats()
        self.append_log(f"鼠标：右键单击 ({event.x}, {event.y})")
        self.flash_marker(event.x, event.y, "#ef4444")

    def on_middle_click(self, event):
        self.middle_clicks += 1
        self.update_mouse_stats()
        self.append_log(f"鼠标：中键单击 ({event.x}, {event.y})")
        self.flash_marker(event.x, event.y, "#3b82f6")

    def on_double_click(self, event):
        self.double_clicks += 1
        self.update_mouse_stats()
        self.append_log(f"鼠标：左键双击 ({event.x}, {event.y})")
        self.flash_marker(event.x, event.y, "#f59e0b")

    def on_mouse_wheel(self, event):
        if event.delta > 0:
            self.scroll_up += 1
            direction = "上"
        else:
            self.scroll_down += 1
            direction = "下"
        self.update_mouse_stats()
        self.append_log(f"滚轮：向{direction}滚动，delta={event.delta}")

    def update_mouse_stats(self):
        self.mouse_stats_var.set(
            "移动 {0} 次 | 左键 {1} | 右键 {2} | 中键 {3} | 双击 {4} | 滚轮上 {5} | 滚轮下 {6}".format(
                self.motion_events,
                self.left_clicks,
                self.right_clicks,
                self.middle_clicks,
                self.double_clicks,
                self.scroll_up,
                self.scroll_down,
            )
        )

    def draw_pointer(self, x, y):
        self.test_canvas.delete("pointer")
        self.test_canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill="#0f766e", outline="", tags="pointer")

    def flash_marker(self, x, y, color):
        marker = self.test_canvas.create_oval(x - 12, y - 12, x + 12, y + 12, outline=color, width=3)
        self.root.after(280, lambda: self.test_canvas.delete(marker))

    def append_log(self, message, dedupe_prefix=None):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        if dedupe_prefix and self.event_log_lines:
            last_line = self.event_log_lines[-1]
            if dedupe_prefix in last_line:
                self.event_log_lines.pop()
        self.event_log_lines.append(line)
        self.event_log_lines = self.event_log_lines[-120:]

        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "\n".join(self.event_log_lines))
        self.log_text.see("end")
        self.log_text.configure(state="disabled")


def main():
    if sys.platform != "win32":
        raise SystemExit("这个工具当前只支持 Windows。")

    root = tk.Tk()
    ttk.Style().theme_use("vista")
    app = InputDeviceTesterApp(root)
    app.append_log("程序已启动，可以开始检测。")
    root.mainloop()


if __name__ == "__main__":
    main()
