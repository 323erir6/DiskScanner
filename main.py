import argparse
import ctypes
import math
import os
import queue
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from tkinter import Canvas, filedialog, messagebox

try:
    import customtkinter as ctk
except ImportError as exc:
    raise SystemExit(
        "Missing required library: customtkinter\n"
        "Install it manually with:\n"
        "pip install -r requirements.txt"
    ) from exc


APP_TITLE = "File Scanner"
MIN_SLICE_DEGREES = 1.2
MAX_VISIBLE_ITEMS = 28
INACCESSIBLE_COLOR = "#7A7F8C"

LANGUAGES = {
    "Українська": {
        "other": "Інше",
        "back": "← Назад",
        "choose": "Обрати",
        "scan": "Сканувати",
        "language": "Мова",
        "theme": "Тема",
        "content": "Вміст поточної папки",
        "hover_details": "Наведіть курсор на сектор, щоб побачити деталі.",
        "scan_background": "Сканування виконується у фоні.",
        "read_top": "Зчитую верхній рівень папки.",
        "prepare": "Підготовка сканування...",
        "scanning": "Сканування...",
        "ready": "Готово",
        "error": "Помилка",
        "current_folder": "поточна папка",
        "no_data": "Немає даних",
        "counting": "Рахую",
        "items_total": "{count} елементів, разом {size}{suffix}",
        "updating": " (оновлюється...)",
        "folder": "Папка",
        "file": "Файл",
        "group": "Група",
        "share": "Частка",
        "click_folder": "Клік відкриє цю папку.",
        "file_no_scan": "Файл не сканується далі.",
        "other_info": "Це сума дрібних елементів.",
        "other_click": "Сектор 'Інше' об'єднує маленькі елементи. Відкрийте їх зі списку.",
        "denied": "Доступ заборонено",
        "denied_details": "Доступ заборонено. Сектор позначений сірим.",
        "admin_question": "Для цієї папки можуть знадобитися права адміністратора. Перезапустити програму від адміністратора?",
        "admin_title": "Права адміністратора",
        "bad_path": "Такий шлях не існує.",
        "open_error": "Не вдалося відкрити папку: {error}",
        "shown": "Показано 80 з {count} елементів",
        "gray": "Сіра",
        "black": "Чорна",
        "neon": "Неон",
    },
    "Русский": {
        "other": "Другое",
        "back": "← Назад",
        "choose": "Выбрать",
        "scan": "Сканировать",
        "language": "Язык",
        "theme": "Тема",
        "content": "Содержимое текущей папки",
        "hover_details": "Наведите курсор на сектор, чтобы увидеть детали.",
        "scan_background": "Сканирование выполняется в фоне.",
        "read_top": "Читаю верхний уровень папки.",
        "prepare": "Подготовка сканирования...",
        "scanning": "Сканирование...",
        "ready": "Готово",
        "error": "Ошибка",
        "current_folder": "текущая папка",
        "no_data": "Нет данных",
        "counting": "Считаю",
        "items_total": "{count} элементов, всего {size}{suffix}",
        "updating": " (обновляется...)",
        "folder": "Папка",
        "file": "Файл",
        "group": "Группа",
        "share": "Доля",
        "click_folder": "Клик откроет эту папку.",
        "file_no_scan": "Файл дальше не сканируется.",
        "other_info": "Это сумма мелких элементов.",
        "other_click": "Сектор 'Другое' объединяет маленькие элементы. Откройте их из списка.",
        "denied": "Доступ запрещен",
        "denied_details": "Доступ запрещен. Сектор отмечен серым.",
        "admin_question": "Для этой папки могут понадобиться права администратора. Перезапустить программу от администратора?",
        "admin_title": "Права администратора",
        "bad_path": "Такой путь не существует.",
        "open_error": "Не удалось открыть папку: {error}",
        "shown": "Показано 80 из {count} элементов",
        "gray": "Серая",
        "black": "Черная",
        "neon": "Неон",
    },
    "English": {
        "other": "Other",
        "back": "← Back",
        "choose": "Choose",
        "scan": "Scan",
        "language": "Language",
        "theme": "Theme",
        "content": "Current folder contents",
        "hover_details": "Hover a slice to see details.",
        "scan_background": "Scanning runs in the background.",
        "read_top": "Reading the top folder level.",
        "prepare": "Preparing scan...",
        "scanning": "Scanning...",
        "ready": "Done",
        "error": "Error",
        "current_folder": "current folder",
        "no_data": "No data",
        "counting": "Counting",
        "items_total": "{count} items, total {size}{suffix}",
        "updating": " (updating...)",
        "folder": "Folder",
        "file": "File",
        "group": "Group",
        "share": "Share",
        "click_folder": "Click opens this folder.",
        "file_no_scan": "Files are not scanned deeper.",
        "other_info": "This is the sum of small items.",
        "other_click": "The 'Other' slice groups small items. Open them from the list.",
        "denied": "Access denied",
        "denied_details": "Access denied. The slice is marked gray.",
        "admin_question": "This folder may require administrator rights. Restart the app as administrator?",
        "admin_title": "Administrator rights",
        "bad_path": "This path does not exist.",
        "open_error": "Could not open folder: {error}",
        "shown": "Showing 80 of {count} items",
        "gray": "Gray",
        "black": "Black",
        "neon": "Neon",
    },
}

THEMES = {
    "gray": {
        "mode": "dark",
        "window": "#20232A",
        "panel": "#282C34",
        "chart": "#1E222B",
        "text": "#F2F5FA",
        "muted": "#AAB2C0",
        "line": "#3A4150",
        "button": "#4B5563",
        "button_hover": "#5E6A7A",
        "entry": "#171A21",
        "center": "#20232A",
        "accent": "#8FB5FF",
        "colors": ["#7AA2F7", "#9ECE6A", "#E0AF68", "#F7768E", "#BB9AF7", "#7DCFFF"],
    },
    "black": {
        "mode": "dark",
        "window": "#050505",
        "panel": "#101010",
        "chart": "#070707",
        "text": "#F8FAFC",
        "muted": "#9CA3AF",
        "line": "#262626",
        "button": "#1F2937",
        "button_hover": "#374151",
        "entry": "#0B0B0B",
        "center": "#050505",
        "accent": "#FFFFFF",
        "colors": ["#2563EB", "#16A34A", "#EA580C", "#DC2626", "#9333EA", "#0891B2"],
    },
    "neon": {
        "mode": "dark",
        "window": "#080A16",
        "panel": "#101427",
        "chart": "#070918",
        "text": "#F7FBFF",
        "muted": "#96A3C7",
        "line": "#26304F",
        "button": "#4C1D95",
        "button_hover": "#6D28D9",
        "entry": "#0B1024",
        "center": "#080A16",
        "accent": "#22D3EE",
        "colors": ["#00E5FF", "#FF2D95", "#A3FF12", "#FFB800", "#8B5CF6", "#00FFA3"],
    },
}


@dataclass
class DiskItem:
    name: str
    path: Path
    size: int
    is_dir: bool
    error: str | None = None
    inaccessible: bool = False


@dataclass
class PieSlice:
    item: DiskItem
    start: float
    extent: float
    color: str
    value: float


def human_size(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def is_drive_root(path: Path) -> bool:
    resolved = path.resolve()
    return resolved.parent == resolved


def is_admin() -> bool:
    if os.name != "nt":
        return os.geteuid() == 0
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except OSError:
        return False


def is_protected_path(path: Path) -> bool:
    if os.name != "nt":
        return False
    protected_roots = [
        os.environ.get("WINDIR"),
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
        os.environ.get("ProgramData"),
    ]
    try:
        target = path.resolve()
        return any(root and target.is_relative_to(Path(root).resolve()) for root in protected_roots)
    except OSError:
        return False


def relaunch_as_admin(path: Path) -> bool:
    if os.name != "nt":
        return False
    script = Path(__file__).resolve()
    params = f'"{script}" --path "{path}"'
    result = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    return result > 32


class FileScannerApp(ctk.CTk):
    def __init__(self, start_path: Path | None = None) -> None:
        super().__init__()

        self.language = "English"
        self.theme_key = "gray"
        self.theme = THEMES[self.theme_key]
        ctk.set_appearance_mode(self.theme["mode"])
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry("1240x800")
        self.minsize(980, 640)

        self.current_path = start_path or Path(os.environ.get("SystemDrive", "C:") + "\\")
        if not self.current_path.exists():
            self.current_path = Path.cwd().anchor and Path(Path.cwd().anchor) or Path.cwd()

        self.scan_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.scan_token = 0
        self.scanning = False
        self.loading_text = ""
        self.loading_phase = 0

        self.items: list[DiskItem] = []
        self.slices: list[PieSlice] = []
        self.hovered_index: int | None = None
        self.selected_index: int | None = None
        self.hover_progress: dict[int, float] = {}

        self._build_ui()
        self.apply_theme()
        self.apply_language()
        self.after(120, self._poll_scan_queue)
        self.after(40, self._animate)
        self.scan_path(self.current_path, ask_admin=True)

    def t(self, key: str, **kwargs) -> str:
        text = LANGUAGES[self.language][key]
        return text.format(**kwargs) if kwargs else text

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.top_bar = ctk.CTkFrame(self, corner_radius=0)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_columnconfigure(2, weight=1)

        self.back_button = ctk.CTkButton(self.top_bar, width=96, command=self.go_back)
        self.back_button.grid(row=0, column=0, padx=(16, 8), pady=(14, 8))

        self.choose_button = ctk.CTkButton(self.top_bar, width=96, command=self.choose_folder)
        self.choose_button.grid(row=0, column=1, padx=8, pady=(14, 8))

        self.path_entry = ctk.CTkEntry(self.top_bar, font=ctk.CTkFont(size=15))
        self.path_entry.grid(row=0, column=2, sticky="ew", padx=8, pady=(14, 8))
        self.path_entry.bind("<Return>", lambda _event: self.scan_from_entry())

        self.scan_button = ctk.CTkButton(self.top_bar, width=104, command=self.scan_from_entry)
        self.scan_button.grid(row=0, column=3, padx=8, pady=(14, 8))

        self.status_label = ctk.CTkLabel(self.top_bar, text="", width=130, anchor="e")
        self.status_label.grid(row=0, column=4, padx=(8, 16), pady=(14, 8))

        self.language_label = ctk.CTkLabel(self.top_bar, text="")
        self.language_label.grid(row=1, column=0, padx=(16, 8), pady=(0, 12))

        self.language_menu = ctk.CTkOptionMenu(
            self.top_bar,
            values=list(LANGUAGES.keys()),
            command=self.change_language,
            width=130,
        )
        self.language_menu.grid(row=1, column=1, padx=8, pady=(0, 12))
        self.language_menu.set(self.language)

        self.theme_label = ctk.CTkLabel(self.top_bar, text="")
        self.theme_label.grid(row=1, column=2, sticky="e", padx=(8, 4), pady=(0, 12))

        self.theme_menu = ctk.CTkOptionMenu(
            self.top_bar,
            values=[self.t("gray"), self.t("black"), self.t("neon")],
            command=self.change_theme,
            width=120,
        )
        self.theme_menu.grid(row=1, column=3, sticky="w", padx=8, pady=(0, 12))

        self.loading_bar = ctk.CTkProgressBar(self.top_bar, mode="indeterminate", height=5)
        self.loading_bar.grid(row=2, column=0, columnspan=5, sticky="ew", padx=16, pady=(0, 10))
        self.loading_bar.grid_remove()

        self.content = ctk.CTkFrame(self, corner_radius=0)
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=3)
        self.content.grid_columnconfigure(1, weight=2)
        self.content.grid_rowconfigure(0, weight=1)

        self.chart_frame = ctk.CTkFrame(self.content, corner_radius=0)
        self.chart_frame.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        self.chart_frame.grid_columnconfigure(0, weight=1)
        self.chart_frame.grid_rowconfigure(0, weight=1)

        self.chart = Canvas(self.chart_frame, highlightthickness=0, bd=0)
        self.chart.grid(row=0, column=0, sticky="nsew")
        self.chart.bind("<Configure>", lambda _event: self.draw_chart())
        self.chart.bind("<Motion>", self.on_chart_motion)
        self.chart.bind("<Leave>", self.on_chart_leave)
        self.chart.bind("<Button-1>", self.on_chart_click)

        self.side_panel = ctk.CTkFrame(self.content, corner_radius=0)
        self.side_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        self.side_panel.grid_columnconfigure(0, weight=1)
        self.side_panel.grid_rowconfigure(2, weight=1)

        self.title_label = ctk.CTkLabel(
            self.side_panel,
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 4))

        self.summary_label = ctk.CTkLabel(self.side_panel, text="", anchor="w")
        self.summary_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        self.item_list = ctk.CTkScrollableFrame(self.side_panel, corner_radius=0)
        self.item_list.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.item_list.grid_columnconfigure(0, weight=1)

        self.details_label = ctk.CTkLabel(
            self.side_panel,
            anchor="w",
            justify="left",
            wraplength=380,
        )
        self.details_label.grid(row=3, column=0, sticky="ew", padx=16, pady=(8, 16))

    def apply_language(self) -> None:
        self.back_button.configure(text=self.t("back"))
        self.choose_button.configure(text=self.t("choose"))
        self.scan_button.configure(text=self.t("scan"))
        self.language_label.configure(text=self.t("language"))
        self.theme_label.configure(text=self.t("theme"))
        self.title_label.configure(text=self.t("content"))
        if not self.items:
            self.summary_label.configure(text=self.t("read_top") if self.scanning else "")
        self.details_label.configure(text=self.t("hover_details"))
        self.theme_menu.configure(values=[self.t("gray"), self.t("black"), self.t("neon")])
        self.theme_menu.set(self.theme_display_name())
        self.render_item_list()
        self.draw_chart()

    def apply_theme(self) -> None:
        self.theme = THEMES[self.theme_key]
        self.configure(fg_color=self.theme["window"])
        self.top_bar.configure(fg_color=self.theme["panel"])
        self.content.configure(fg_color=self.theme["window"])
        self.chart_frame.configure(fg_color=self.theme["chart"])
        self.side_panel.configure(fg_color=self.theme["panel"])
        self.item_list.configure(fg_color=self.theme["panel"])
        self.chart.configure(bg=self.theme["chart"])

        button_options = {
            "fg_color": self.theme["button"],
            "hover_color": self.theme["button_hover"],
            "text_color": self.theme["text"],
        }
        for button in (self.back_button, self.choose_button, self.scan_button):
            button.configure(**button_options)

        self.path_entry.configure(
            fg_color=self.theme["entry"],
            border_color=self.theme["line"],
            text_color=self.theme["text"],
        )
        self.loading_bar.configure(progress_color=self.theme["accent"])
        for label in (
            self.status_label,
            self.language_label,
            self.theme_label,
            self.title_label,
            self.summary_label,
            self.details_label,
        ):
            label.configure(text_color=self.theme["text"])
        self.render_item_list()
        self.draw_chart()

    def change_language(self, language: str) -> None:
        self.language = language
        self.apply_language()
        self.update_summary(finished=not self.scanning)

    def theme_display_name(self) -> str:
        return {
            "gray": self.t("gray"),
            "black": self.t("black"),
            "neon": self.t("neon"),
        }[self.theme_key]

    def change_theme(self, display_name: str) -> None:
        lookup = {
            self.t("gray"): "gray",
            self.t("black"): "black",
            self.t("neon"): "neon",
        }
        self.theme_key = lookup.get(display_name, "gray")
        self.apply_theme()

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory(initialdir=str(self.current_path))
        if selected:
            self.scan_path(Path(selected), ask_admin=True)

    def scan_from_entry(self) -> None:
        path = Path(self.path_entry.get().strip('" '))
        if not path.exists():
            messagebox.showerror(APP_TITLE, self.t("bad_path"))
            return
        if path.is_file():
            path = path.parent
        self.scan_path(path, ask_admin=True)

    def go_back(self) -> None:
        parent = self.current_path.parent
        if parent != self.current_path:
            self.scan_path(parent, ask_admin=False)

    def should_request_admin(self, path: Path, force: bool = False) -> bool:
        if is_admin():
            return False
        if force or is_protected_path(path):
            return messagebox.askyesno(self.t("admin_title"), self.t("admin_question"))
        return False

    def request_admin_for_path(self, path: Path, force: bool = False) -> bool:
        if not self.should_request_admin(path, force=force):
            return False
        if relaunch_as_admin(path):
            self.destroy()
            return True
        return False

    def scan_path(self, path: Path, ask_admin: bool = False) -> None:
        if ask_admin and self.request_admin_for_path(path):
            return

        self.scan_token += 1
        token = self.scan_token
        self.current_path = path
        self.items = []
        self.slices = []
        self.hover_progress = {}
        self.hovered_index = None
        self.selected_index = None
        self.scanning = True
        self.loading_text = self.t("prepare")

        self.path_entry.delete(0, "end")
        self.path_entry.insert(0, str(path))
        self.status_label.configure(text=self.t("scanning"))
        self.summary_label.configure(text=self.t("read_top"))
        self.details_label.configure(text=self.t("scan_background"))
        self.back_button.configure(state="disabled" if is_drive_root(path) else "normal")
        self.loading_bar.grid()
        self.loading_bar.start()
        self._clear_item_list()
        self.draw_chart()

        thread = threading.Thread(target=self._scan_worker, args=(path, token), daemon=True)
        thread.start()

    def _scan_worker(self, path: Path, token: int) -> None:
        items: list[DiskItem] = []
        try:
            children = sorted(path.iterdir(), key=lambda child: (not child.is_dir(), child.name.lower()))
        except PermissionError as exc:
            self.scan_queue.put(("error", (token, self.t("open_error", error=exc))))
            return
        except OSError as exc:
            self.scan_queue.put(("error", (token, self.t("open_error", error=exc))))
            return

        total_children = len(children)
        self.scan_queue.put(("progress", (token, 0, total_children)))

        for index, child in enumerate(children, start=1):
            if token != self.scan_token:
                return

            self.scan_queue.put(("active", (token, index, total_children, child.name)))
            item = self._measure_item(child, token)
            items.append(item)

            if index == total_children or index % 2 == 0:
                self.scan_queue.put(("progress", (token, index, total_children)))
                self.scan_queue.put(("partial", (token, list(items))))

        self.scan_queue.put(("done", (token, items)))

    def _measure_item(self, path: Path, token: int) -> DiskItem:
        try:
            is_dir = path.is_dir()
        except PermissionError as exc:
            return DiskItem(path.name, path, 0, True, str(exc), inaccessible=True)
        except OSError as exc:
            return DiskItem(path.name, path, 0, False, str(exc), inaccessible=True)

        if not is_dir:
            try:
                return DiskItem(path.name, path, path.stat().st_size, False)
            except PermissionError as exc:
                return DiskItem(path.name, path, 0, False, str(exc), inaccessible=True)
            except OSError as exc:
                return DiskItem(path.name, path, 0, False, str(exc), inaccessible=True)

        total = 0
        error: str | None = None
        inaccessible = False

        def on_walk_error(exc: OSError) -> None:
            nonlocal error, inaccessible
            error = str(exc)
            if isinstance(exc, PermissionError):
                inaccessible = True

        for root, dir_names, file_names in os.walk(path, topdown=True, onerror=on_walk_error):
            if token != self.scan_token:
                break

            filtered_dirs = []
            for dir_name in dir_names:
                dir_path = Path(root) / dir_name
                try:
                    if not dir_path.is_symlink():
                        filtered_dirs.append(dir_name)
                except PermissionError as exc:
                    error = str(exc)
                    inaccessible = True
                except OSError as exc:
                    error = str(exc)
            dir_names[:] = filtered_dirs

            for file_name in file_names:
                file_path = Path(root) / file_name
                try:
                    if not file_path.is_symlink():
                        total += file_path.stat().st_size
                except PermissionError as exc:
                    error = str(exc)
                    inaccessible = True
                except OSError as exc:
                    error = str(exc)

        return DiskItem(path.name, path, total, True, error, inaccessible)

    def _poll_scan_queue(self) -> None:
        try:
            while True:
                event, payload = self.scan_queue.get_nowait()
                if event == "progress":
                    token, current, total = payload
                    if token == self.scan_token:
                        self.status_label.configure(text=f"{current}/{total}")
                elif event == "active":
                    token, current, total, name = payload
                    if token == self.scan_token:
                        self.loading_text = f"{self.t('counting')}: {name}"
                        self.status_label.configure(text=f"{current}/{total}")
                elif event == "partial":
                    token, items = payload
                    if token == self.scan_token:
                        self._set_items(items, finished=False)
                elif event == "done":
                    token, items = payload
                    if token == self.scan_token:
                        self.scanning = False
                        self.loading_text = ""
                        self._set_items(items, finished=True)
                        self.status_label.configure(text=self.t("ready"))
                        self.loading_bar.stop()
                        self.loading_bar.grid_remove()
                elif event == "error":
                    token, message = payload
                    if token == self.scan_token:
                        self.scanning = False
                        self.loading_text = ""
                        self.status_label.configure(text=self.t("error"))
                        self.loading_bar.stop()
                        self.loading_bar.grid_remove()
                        messagebox.showerror(APP_TITLE, message)
        except queue.Empty:
            pass

        self.after(120, self._poll_scan_queue)

    def _set_items(self, items: list[DiskItem], finished: bool) -> None:
        self.items = sorted(items, key=lambda item: (item.inaccessible, item.size), reverse=True)
        self.slices = self._build_slices(self.items)
        self.draw_chart()
        self.render_item_list()
        self.update_summary(finished)

    def update_summary(self, finished: bool) -> None:
        total_size = sum(item.size for item in self.items)
        suffix = "" if finished else self.t("updating")
        self.summary_label.configure(
            text=self.t("items_total", count=len(self.items), size=human_size(total_size), suffix=suffix)
        )

    def _slice_value(self, item: DiskItem, real_total: int) -> float:
        if item.size > 0:
            return float(item.size)
        if item.inaccessible:
            return max(real_total * 0.035, 1.0)
        return 1.0

    def _build_slices(self, items: list[DiskItem]) -> list[PieSlice]:
        visible = items[:MAX_VISIBLE_ITEMS]
        hidden = items[MAX_VISIBLE_ITEMS:]
        other_label = self.t("other")

        if hidden:
            visible.append(
                DiskItem(
                    name=other_label,
                    path=self.current_path,
                    size=sum(item.size for item in hidden),
                    is_dir=False,
                    inaccessible=any(item.inaccessible for item in hidden),
                )
            )

        real_total = sum(max(item.size, 0) for item in visible)
        values = [self._slice_value(item, real_total) for item in visible]
        total = sum(values)
        if total <= 0:
            return []

        slices: list[PieSlice] = []
        start = 90.0
        colors = self.theme["colors"]
        for index, (item, value) in enumerate(zip(visible, values)):
            extent = max((value / total) * 360.0, MIN_SLICE_DEGREES)
            if start - extent < -270:
                extent = start + 270
            if extent <= 0:
                break
            color = INACCESSIBLE_COLOR if item.inaccessible else colors[index % len(colors)]
            slices.append(PieSlice(item, start, -extent, color, value))
            start -= extent
        return slices

    def draw_chart(self) -> None:
        self.chart.delete("all")
        width = self.chart.winfo_width()
        height = self.chart.winfo_height()
        if width <= 2 or height <= 2:
            return

        if not self.slices:
            self.chart.create_text(
                width / 2,
                height / 2 - 14,
                text=self.t("no_data") if not self.scanning else self.t("scanning"),
                fill=self.theme["text"],
                font=("Segoe UI", 20, "bold"),
            )
            if self.scanning and self.loading_text:
                self.chart.create_text(
                    width / 2,
                    height / 2 + 18,
                    text=self._loading_caption(46),
                    fill=self.theme["muted"],
                    font=("Segoe UI", 12),
                )
            return

        margin = 38
        size = min(width, height) - margin * 2
        x0 = (width - size) / 2
        y0 = (height - size) / 2
        x1 = x0 + size
        y1 = y0 + size

        for index, slice_data in enumerate(self.slices):
            progress = self.hover_progress.get(index, 0.0)
            offset = 10 * progress
            outline = self.theme["chart"]
            outline_width = 2
            if progress > 0:
                outline = self.theme["accent"]
                outline_width = 2 + int(2 * progress)
            elif index == self.selected_index:
                offset = 6
                outline = self.theme["text"]
                outline_width = 3

            dx, dy = self._slice_offset(slice_data, offset)
            self.chart.create_arc(
                x0 + dx,
                y0 + dy,
                x1 + dx,
                y1 + dy,
                start=slice_data.start,
                extent=slice_data.extent,
                fill=slice_data.color,
                outline=outline,
                width=outline_width,
                style="pieslice",
            )

        total_size = sum(item.size for item in self.items)
        center = min(size * 0.36, 210)
        cx = width / 2
        cy = height / 2
        pulse = 1 + (math.sin(self.loading_phase / 7) * 0.02 if self.scanning else 0)
        center_size = center * pulse
        self.chart.create_oval(
            cx - center_size / 2,
            cy - center_size / 2,
            cx + center_size / 2,
            cy + center_size / 2,
            fill=self.theme["center"],
            outline=self.theme["line"],
            width=2,
        )
        self.chart.create_text(
            cx,
            cy - 12,
            text=human_size(total_size),
            fill=self.theme["text"],
            font=("Segoe UI", 22, "bold"),
        )
        self.chart.create_text(
            cx,
            cy + 20,
            text=self._loading_caption(34) if self.scanning else self.t("current_folder"),
            fill=self.theme["muted"],
            font=("Segoe UI", 11),
        )

    def _loading_caption(self, max_length: int) -> str:
        dots = "." * ((self.loading_phase // 8) % 4)
        return self._short_text(f"{self.loading_text}{dots}", max_length)

    def _short_text(self, text: str, max_length: int) -> str:
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    def _slice_offset(self, slice_data: PieSlice, distance: float) -> tuple[float, float]:
        if distance == 0:
            return 0.0, 0.0
        middle = math.radians(slice_data.start + slice_data.extent / 2)
        return math.cos(middle) * distance, -math.sin(middle) * distance

    def _animate(self) -> None:
        changed = False
        self.loading_phase += 1
        for index in range(len(self.slices)):
            target = 1.0 if index == self.hovered_index else 0.0
            current = self.hover_progress.get(index, 0.0)
            next_value = current + (target - current) * 0.28
            if abs(next_value - current) > 0.01:
                self.hover_progress[index] = next_value
                changed = True
            elif target == 0.0 and index in self.hover_progress:
                self.hover_progress.pop(index, None)
                changed = True
        if changed or self.scanning:
            self.draw_chart()
        self.after(40, self._animate)

    def on_chart_motion(self, event) -> None:
        index = self._slice_at(event.x, event.y)
        if index != self.hovered_index:
            self.hovered_index = index
            self.update_details(index)

    def on_chart_leave(self, _event) -> None:
        self.hovered_index = None
        self.update_details(None)

    def on_chart_click(self, event) -> None:
        index = self._slice_at(event.x, event.y)
        if index is None or index >= len(self.slices):
            return

        item = self.slices[index].item
        self.selected_index = index
        self.draw_chart()

        if item.name == self.t("other"):
            self.details_label.configure(text=self.t("other_click"))
            return

        if item.inaccessible:
            if self.request_admin_for_path(item.path, force=True):
                return
            self.details_label.configure(text=f"{item.name}\n{self.t('denied_details')}")
            return

        if item.is_dir:
            self.scan_path(item.path, ask_admin=True)
        else:
            self.details_label.configure(
                text=f"{item.name}\n{self.t('file')}: {human_size(item.size)}\n{self.t('file_no_scan')}"
            )

    def _slice_at(self, x: int, y: int) -> int | None:
        width = self.chart.winfo_width()
        height = self.chart.winfo_height()
        margin = 38
        size = min(width, height) - margin * 2
        if size <= 0:
            return None

        cx = width / 2
        cy = height / 2
        dx = x - cx
        dy = y - cy
        radius = math.sqrt(dx * dx + dy * dy)
        if radius > size / 2 or radius < (size * 0.36) / 2:
            return None

        angle = math.degrees(math.atan2(-dy, dx))
        if angle < 0:
            angle += 360

        for index, slice_data in enumerate(self.slices):
            start = slice_data.start % 360
            end = (slice_data.start + slice_data.extent) % 360
            if self._angle_in_clockwise_range(angle, start, end):
                return index
        return None

    def _angle_in_clockwise_range(self, angle: float, start: float, end: float) -> bool:
        if start >= end:
            return end <= angle <= start
        return angle <= start or angle >= end

    def update_details(self, index: int | None) -> None:
        if index is None or index >= len(self.slices):
            self.details_label.configure(text=self.t("hover_details"))
            return

        item = self.slices[index].item
        total = sum(slice_data.value for slice_data in self.slices)
        percent = (self.slices[index].value / total * 100) if total else 0
        kind = self.t("folder") if item.is_dir else self.t("file")
        action = self.t("click_folder") if item.is_dir else self.t("file_no_scan")
        if item.name == self.t("other"):
            kind = self.t("group")
            action = self.t("other_info")
        if item.inaccessible:
            action = f"{self.t('denied_details')} {self.t('admin_question')}"

        self.details_label.configure(
            text=(
                f"{item.name}\n"
                f"{kind}: {human_size(item.size)}\n"
                f"{self.t('share')}: {percent:.1f}%\n"
                f"{action}"
            )
        )

    def render_item_list(self) -> None:
        if not hasattr(self, "item_list"):
            return
        self._clear_item_list()

        for row, item in enumerate(self.items[:80]):
            mark = "!" if item.inaccessible else ("DIR" if item.is_dir else "FILE")
            text = f"{mark}  {item.name}"
            item_button = ctk.CTkButton(
                self.item_list,
                text=text,
                anchor="w",
                fg_color="transparent",
                hover_color=self.theme["button_hover"],
                text_color=INACCESSIBLE_COLOR if item.inaccessible else self.theme["text"],
                command=lambda selected=item: self.open_item_from_list(selected),
            )
            item_button.grid(row=row, column=0, sticky="ew", padx=6, pady=(4, 0))

            size_text = self.t("denied") if item.inaccessible and item.size == 0 else human_size(item.size)
            size_label = ctk.CTkLabel(
                self.item_list,
                text=size_text,
                text_color=INACCESSIBLE_COLOR if item.inaccessible else self.theme["muted"],
                anchor="e",
            )
            size_label.grid(row=row, column=1, sticky="e", padx=(8, 10), pady=(4, 0))

        if len(self.items) > 80:
            more_label = ctk.CTkLabel(
                self.item_list,
                text=self.t("shown", count=len(self.items)),
                text_color=self.theme["muted"],
            )
            more_label.grid(row=81, column=0, columnspan=2, pady=12)

    def open_item_from_list(self, item: DiskItem) -> None:
        if item.inaccessible:
            self.request_admin_for_path(item.path, force=True)
        elif item.is_dir:
            self.scan_path(item.path, ask_admin=True)
        else:
            self.details_label.configure(text=f"{item.name}\n{self.t('file')}: {human_size(item.size)}")

    def _clear_item_list(self) -> None:
        for widget in self.item_list.winfo_children():
            widget.destroy()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=str, default="")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    start = Path(args.path) if args.path else None
    app = FileScannerApp(start)
    app.mainloop()
