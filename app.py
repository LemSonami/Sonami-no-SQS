from __future__ import annotations
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from main_controller import AppController
from ui_views import configure_styles

_bg_process = None

def main() -> None:
    global _bg_process

    exe_path = Path(__file__).resolve().parent / "BASpark.exe"
    if exe_path.exists():
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        try:
            _bg_process = subprocess.Popen(
                [str(exe_path)],
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception:
            pass

    root = tk.Tk()
    root.title("Sonami×智测系统 V0.1.0")
    root.geometry("1000x680")

    icon_path = Path(__file__).resolve().parent / "assets" / "ICO.ico"
    if icon_path.exists():
        root.iconbitmap(str(icon_path))
    root.minsize(900, 600)

    _exit_called = False

    def _on_exit():
        nonlocal _exit_called
        if _exit_called:
            return
        _exit_called = True
        if _bg_process and _bg_process.poll() is None:
            _bg_process.terminate()
            try:
                _bg_process.wait(timeout=3)
            except Exception:
                _bg_process.kill()
        try:
            root.destroy()
        except tk.TclError:
            pass

    root.protocol("WM_DELETE_WINDOW", _on_exit)

    from data_manager import SettingsManager
    settings_mgr = SettingsManager()
    settings = settings_mgr.load_settings()
    configure_styles(root, settings)

    try:
        controller = AppController(root)
    except Exception as exc:
        messagebox.showerror("启动失败", f"系统初始化失败TAT：{exc}")
        _on_exit()
        return

    controller.show_login()
    root.mainloop()
    _on_exit()

if __name__ == "__main__":
    main()