#一个 Bug 是 Bug ，一堆 Bug 是 Debug ；能跑起来的叫 Feature ，跑不起来的叫 Debug ，跑起来了但不知所云的叫玄学，而你的 Debugger 妈妈能把“不知为何能跑”改成“不知为何跑不起来”的，如果你乱动，那么本来能跑的也跑不起来了，这叫 Release ，你盯着日志它不复现，你一去倒水它就崩，这叫 Heisenbug ，稳定复现，像玻尔模型一样老实的叫 Bohrbug ，你不看代码它有问题，一看代码它又好像正常的叫 Schrödinbug ，像混沌分形的，你修一个角，它炸一片的叫 Mandelbug~
#早期 Harvard Mark II 计算机里发现过一只飞蛾，被贴在本子上写着 “First actual case of bug being found”
#Debugger 就是去除 Bug 的东西——只不过去除方式是先制造一个更确定的 Bug ~awa


#这是一个扁平化深色软键盘，点击即发送字符到当前焦点窗口。仅支持 Windows（依赖 user32.dll）。不是输入法，不联网，不做词库，只是模拟键盘。


import ctypes
import customtkinter as ctk
import sys
import os


def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.abspath("."), relative)


#尝试导入keyboard库，用于全局热键隐藏/显示
try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False

user32 = ctypes.windll.user32

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

VK_BACK = 0x08
VK_TAB = 0x09
VK_RETURN = 0x0D
VK_SPACE = 0x20
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12

#扁平深色配色
BG = "#1a1a1a"
KEY_BG = "#2d2d2d"
KEY_HOVER = "#3d3d3d"
KEY_TEXT = "#e0e0e0"
SPECIAL_BG = "#252525"
SPECIAL_HOVER = "#353535"
ACTIVE_BG = "#0a84ff"


def send_char(ch):
    #发送一个Unicode字符到当前焦点窗口。
    user32.keybd_event(0, ord(ch), KEYEVENTF_UNICODE, 0)
    user32.keybd_event(0, ord(ch), KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0)


def send_vk(vk):
    #发送一个虚拟键码（功能键）。
    user32.keybd_event(vk, 0, 0, 0)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def set_no_activate(window):
    #让窗口不抢焦点，同时强制在任务栏显示图标。
    GWL_EXSTYLE = -20
    WS_EX_NOACTIVATE = 0x08000000
    WS_EX_APPWINDOW = 0x00040000
    WS_EX_TOOLWINDOW = 0x00000080
    SW_SHOW = 5
    try:
        hwnd = user32.FindWindowW(None, window.title())
        if not hwnd:
            return
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        #清掉TOOLWINDOW，加上APPWINDOW
        style = (style & ~WS_EX_TOOLWINDOW) | WS_EX_NOACTIVATE | WS_EX_APPWINDOW
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        #重新显示一次，让新样式生效
        user32.ShowWindow(hwnd, SW_SHOW)
    except Exception:
        pass


class KeyboardApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Keyboard")
        self.overrideredirect(True)

        self.title("Keyboard")
        try:
            self.iconbitmap(resource_path("keyboard_icon.ico"))
        except Exception:
            pass

        #固定初始位置在右上角
        screen_h = self.winfo_screenheight()
        self.geometry(f"880x340+0+{screen_h - 340}")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        #初始透明度
        self.attributes("-alpha", 0.95)

        ctk.set_appearance_mode("dark")

        self.shift_on = False
        self.caps_on = False
        self.buttons = {}          #所有按钮kind/value->button
        self.letter_buttons = {}   #字母键小写字母->button
        self.is_hidden = False     #当前是否处于隐藏状态

        #顶部控制栏：透明度+置顶+隐藏提示
        control_bar = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        control_bar.pack(fill="x", padx=8, pady=(8, 0))

        ctk.CTkLabel(
            control_bar, text="Opacity",
            font=("Segoe UI", 11),
            text_color=KEY_TEXT
        ).pack(side="left", padx=(5, 8))

        self.opacity_var = ctk.DoubleVar(value=0.95)
        ctk.CTkSlider(
            control_bar, from_=0.3, to=1.0,
            variable=self.opacity_var,
            command=self._on_opacity_change,
            width=160, height=18,
            button_color=ACTIVE_BG,
            progress_color=ACTIVE_BG
        ).pack(side="left", padx=(0, 10))

        self.opacity_label = ctk.CTkLabel(
            control_bar, text="95%",
            font=("Segoe UI", 10),
            text_color=KEY_TEXT, width=40
        )
        self.opacity_label.pack(side="left", padx=(0, 15))

        #置顶开关
        self.topmost_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(
            control_bar, text="Always on Top",
            variable=self.topmost_var,
            command=self._toggle_topmost,
            font=("Segoe UI", 11),
            text_color=KEY_TEXT,
            progress_color=ACTIVE_BG,
            button_color=KEY_TEXT,
            button_hover_color=KEY_TEXT,
            width=140
        ).pack(side="left", padx=(0, 15))

        #隐藏：优先用全局热键，没有keyboard库就用按钮
        if HAS_KEYBOARD:
            ctk.CTkLabel(
                control_bar, text="Ctrl+Alt+H to hide",
                font=("Segoe UI", 16),
                text_color="#888888"
            ).pack(side="right", padx=10)
        else:
            ctk.CTkButton(
                control_bar, text="Hide",
                font=("Segoe UI", 11),
                width=70, height=24,
                fg_color=SPECIAL_BG, hover_color=SPECIAL_HOVER,
                command=self._hide
            ).pack(side="right", padx=5)

        #主键盘区
        container = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        container.pack(fill="both", expand=True, padx=8, pady=8)

        for c in range(15):
            container.grid_columnconfigure(c, weight=1, uniform="key")
        for r in range(5):
            container.grid_rowconfigure(r, weight=1, uniform="row")

        self._build_rows(container)

        #延时应用no-activate，等窗口真正创建出来
        self.after(150, lambda: set_no_activate(self))

        #延时注册全局热键
        if HAS_KEYBOARD:
            self.after(200, self._register_hotkey)

    def _register_hotkey(self):
        #注册全局热键Ctrl+Alt+H，用来显示/隐藏键盘
        #用self.after(0, ...)确保切回主线程，避免tkinter线程安全问题
        try:
            keyboard.add_hotkey('ctrl+alt+h', lambda: self.after(0, self._toggle_visibility))
        except Exception:
            pass

    def _toggle_visibility(self):
        #显示/隐藏键盘
        if self.is_hidden:
            self.deiconify()
            self.is_hidden = False
            #重新应用no-activate样式（deiconify后可能失效）
            self.after(50, lambda: set_no_activate(self))
        else:
            self.withdraw()
            self.is_hidden = True

    def _toggle_topmost(self):
        #切换窗口置顶状态
        try:
            self.attributes("-topmost", self.topmost_var.get())
        except Exception:
            pass

    def _hide(self):
        #备用方案：最小化到任务栏
        self.iconify()

    def _on_opacity_change(self, value):
        #透明度变化时实时更新
        try:
            v = float(value)
            self.attributes("-alpha", v)
            self.opacity_label.configure(text=f"{int(v * 100)}%")
        except Exception:
            pass

    def _build_rows(self, parent):
        #每行显示文字, 动作类型, 动作值, 列跨度
        rows = [
            [
                ("`", "char", "`", 1), ("1", "char", "1", 1),
                ("2", "char", "2", 1), ("3", "char", "3", 1),
                ("4", "char", "4", 1), ("5", "char", "5", 1),
                ("6", "char", "6", 1), ("7", "char", "7", 1),
                ("8", "char", "8", 1), ("9", "char", "9", 1),
                ("0", "char", "0", 1), ("-", "char", "-", 1),
                ("=", "char", "=", 1), ("⌫", "vk", VK_BACK, 2),
            ],
            [
                ("Tab", "vk", VK_TAB, 2),
                ("Q", "char", "q", 1), ("W", "char", "w", 1),
                ("E", "char", "e", 1), ("R", "char", "r", 1),
                ("T", "char", "t", 1), ("Y", "char", "y", 1),
                ("U", "char", "u", 1), ("I", "char", "i", 1),
                ("O", "char", "o", 1), ("P", "char", "p", 1),
                ("[", "char", "[", 1), ("]", "char", "]", 1),
                ("\\", "char", "\\", 1),
            ],
            [
                ("Caps", "caps", None, 2),
                ("A", "char", "a", 1), ("S", "char", "s", 1),
                ("D", "char", "d", 1), ("F", "char", "f", 1),
                ("G", "char", "g", 1), ("H", "char", "h", 1),
                ("J", "char", "j", 1), ("K", "char", "k", 1),
                ("L", "char", "l", 1), (";", "char", ";", 1),
                ("'", "char", "'", 1), ("Enter", "vk", VK_RETURN, 3),
            ],
            [
                ("Shift", "shift", None, 3),
                ("Z", "char", "z", 1), ("X", "char", "x", 1),
                ("C", "char", "c", 1), ("V", "char", "v", 1),
                ("B", "char", "b", 1), ("N", "char", "n", 1),
                ("M", "char", "m", 1), (",", "char", ",", 1),
                (".", "char", ".", 1), ("/", "char", "/", 1),
                ("Shift", "shift", None, 3),
            ],
            [
                ("Ctrl", "vk", VK_CONTROL, 3),
                ("Alt", "vk", VK_MENU, 3),
                ("Space", "vk", VK_SPACE, 5),
                ("Alt", "vk", VK_MENU, 2),
                ("Ctrl", "vk", VK_CONTROL, 2),
            ],
        ]

        for r, row in enumerate(rows):
            col = 0
            for label, kind, value, span in row:
                btn = self._make_button(parent, label, kind, value)
                btn.grid(row=r, column=col, columnspan=span,
                         sticky="nsew", padx=2, pady=2)
                col += span

    def _make_button(self, parent, label, kind, value):
        is_special = kind in ("vk", "shift", "caps")
        bg = SPECIAL_BG if is_special else KEY_BG
        hover = SPECIAL_HOVER if is_special else KEY_HOVER

        btn = ctk.CTkButton(
            parent,
            text=label,
            font=("Segoe UI", 12),
            fg_color=bg,
            hover_color=hover,
            text_color=KEY_TEXT,
            corner_radius=6,
            border_width=0,
            command=lambda k=kind, v=value: self._on_press(k, v),
        )

        #记录按钮，供Shift/Caps状态刷新用
        if kind == "char":
            self.buttons[value] = btn
            if value.isalpha() and len(value) == 1:
                self.letter_buttons[value] = btn
        elif kind in ("shift", "caps"):
            self.buttons[kind] = btn

        return btn

    def _on_press(self, kind, value):
        if kind == "char":
            ch = value
            if self.shift_on or self.caps_on:
                if ch.isalpha():
                    #字母Shift和Caps是异或关系
                    if self.shift_on ^ self.caps_on:
                        ch = ch.upper()
                elif self.shift_on:
                    #符号只有Shift才变
                    ch = self._shift_symbol(ch)
            send_char(ch)

        elif kind == "vk":
            send_vk(value)

        elif kind == "shift":
            self.shift_on = not self.shift_on
            self._refresh_shift()

        elif kind == "caps":
            self.caps_on = not self.caps_on
            self._refresh_caps()

    def _shift_symbol(self, ch):
        mapping = {
            "`": "~", "1": "!", "2": "@", "3": "#", "4": "$",
            "5": "%", "6": "^", "7": "&", "8": "*", "9": "(",
            "0": ")", "-": "_", "=": "+", "[": "{", "]": "}",
            "\\": "|", ";": ":", "'": '"', ",": "<", ".": ">",
            "/": "?",
        }
        return mapping.get(ch, ch)

    def _refresh_shift(self):
        #Shift键高亮
        shift_btn = self.buttons.get("shift")
        if shift_btn:
            shift_btn.configure(fg_color=ACTIVE_BG if self.shift_on else SPECIAL_BG)

        #字母显示大小写
        upper = self.shift_on ^ self.caps_on
        for letter, btn in self.letter_buttons.items():
            btn.configure(text=letter.upper() if upper else letter.lower())

    def _refresh_caps(self):
        caps_btn = self.buttons.get("caps")
        if caps_btn:
            caps_btn.configure(fg_color=ACTIVE_BG if self.caps_on else SPECIAL_BG)
        self._refresh_shift()


if __name__ == "__main__":
    app = KeyboardApp()
    app.mainloop()