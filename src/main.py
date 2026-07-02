"""Clipboard History — 程序入口。

初始化数据库、配置、剪贴板监控和系统托盘，
管理主窗口生命周期。
"""

import sys
import os


def _get_project_root() -> str:
    """获取项目根目录。

    PyInstaller 打包后资源解压到 sys._MEIPASS，
    数据文件（数据库、图片）存放在 .exe 同级目录。
    """
    if getattr(sys, "frozen", False):
        # 打包后：资源在 _MEIPASS，数据在 exe 同级
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_data_dir() -> str:
    """获取运行时数据目录（数据库、图片存储）。

    打包后在 .exe 同级创建 data/ 文件夹。
    """
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "data")
    return os.path.join(_get_project_root(), "data")


PROJECT_ROOT = _get_project_root()
DATA_DIR = _get_data_dir()

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtWidgets import QApplication

from src.database import Database
from src.config import Config
from src.cleanup import CleanupManager
from src.clipboard_monitor import ClipboardMonitor
from src.ui.tray_icon import TrayIcon
from src.ui.main_window import MainWindow
from src.ui.settings_dialog import SettingsDialog
from src.utils.hotkey import HotkeyManager


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Clipboard History")
    app.setQuitOnLastWindowClosed(False)  # 关闭窗口不退出，托盘常驻

    # ---- 初始化数据层 ----
    db_path = os.path.join(DATA_DIR, "clipboard.db")
    db = Database(db_path)
    cfg = Config(db)

    # ---- 初始化主窗口 ----
    icon_path = os.path.join(PROJECT_ROOT, "assets", "icon.png")
    window = MainWindow(db, icon_path=icon_path)

    # ---- 初始化剪贴板监控 ----
    image_dir = os.path.join(DATA_DIR, "images")
    monitor = ClipboardMonitor(db, image_dir=image_dir)

    # 新剪贴板内容 → 主窗口实时刷新
    monitor.new_item.connect(lambda _: window.refresh_list())

    # ---- 初始化系统托盘 ----
    tray = TrayIcon(icon_path=icon_path)

    # ---- 初始化全局热键 ----
    hotkey_mgr = HotkeyManager()

    def register_hotkey():
        if cfg.get_bool("hotkey_enabled"):
            hotkey_mgr.register(cfg.get("hotkey_combo"))

    # ---- 托盘菜单 → 动作 ----

    def show_window():
        window.show()
        window.raise_()
        window.activateWindow()

    tray.show_window_requested.connect(show_window)
    hotkey_mgr.activated.connect(show_window)

    def open_settings():
        dlg = SettingsDialog(cfg, parent=window)
        if dlg.exec() == SettingsDialog.DialogCode.Accepted:
            register_hotkey()  # 设置变更后重新注册热键

    tray.settings_requested.connect(open_settings)
    window.settings_requested.connect(open_settings)

    # 暂停 / 恢复监控
    def toggle_pause(checked: bool):
        if checked:
            monitor.pause_monitoring()
        else:
            monitor.resume_monitoring()

    tray.pause_action.toggled.connect(toggle_pause)

    # 退出
    def quit_app():
        cleanup_mgr.stop()
        hotkey_mgr.unregister()
        monitor.stop_monitoring()
        monitor.wait(2000)
        db.close()
        tray.hide()
        app.quit()

    tray.quit_requested.connect(quit_app)

    # ---- 清理任务 ----
    cleanup_mgr = CleanupManager(db, cfg)
    cleanup_mgr.cleaned.connect(lambda: window.refresh_list())
    cleanup_mgr.run()  # 启动时立即执行一次

    # ---- 启动 ----
    tray.show()
    monitor.start()
    register_hotkey()  # 根据设置注册全局热键

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
