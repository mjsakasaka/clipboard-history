"""阶段 3 验证脚本：测试系统托盘和程序入口。

验证各组件的创建、信号连接、监控启停和清理逻辑。
实际托盘图标可见性需手动确认。
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
import win32clipboard

from src.database import Database
from src.config import Config
from src.clipboard_monitor import ClipboardMonitor
from src.ui.tray_icon import TrayIcon


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def set_clipboard_text(text: str) -> None:
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
    win32clipboard.CloseClipboard()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    passed = 0
    failed = 0

    # --------------------------------------------------
    # 测试 1: 各组件正常创建
    # --------------------------------------------------
    print("[TEST 1] Create all components...")
    try:
        db_path = os.path.join(PROJECT_ROOT, "data", "clipboard.db")
        db = Database(db_path)
        cfg = Config(db)

        image_dir = os.path.join(PROJECT_ROOT, "data", "images")
        monitor = ClipboardMonitor(db, image_dir=image_dir)

        icon_path = os.path.join(PROJECT_ROOT, "assets", "icon.png")
        tray = TrayIcon(icon_path=icon_path)
        print("  [PASS] All components created")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Component creation failed: {e}")
        failed += 1
        db.close()
        sys.exit(1)

    # --------------------------------------------------
    # 测试 2: 托盘图标加载成功
    # --------------------------------------------------
    print("[TEST 2] Tray icon loaded...")
    if tray.icon().isNull():
        print("  [FAIL] Icon is null (fallback also failed)")
        failed += 1
    else:
        print("  [PASS] Icon loaded")
        passed += 1

    # --------------------------------------------------
    # 测试 3: 托盘右键菜单项齐全
    # --------------------------------------------------
    print("[TEST 3] Tray menu actions...")
    menu = tray.contextMenu()
    actions = [a.text() for a in menu.actions() if a.text()]
    required = ["Open History Panel", "Settings", "Pause Monitoring", "Quit"]
    missing = [r for r in required if r not in actions]
    if missing:
        print(f"  [FAIL] Missing actions: {missing}")
        failed += 1
    else:
        print(f"  [PASS] All {len(required)} menu actions present")
        passed += 1

    # --------------------------------------------------
    # 测试 4: 监控正常启停
    # --------------------------------------------------
    print("[TEST 4] Monitor start/stop...")
    monitor.start()
    time.sleep(0.3)
    if not monitor.isRunning():
        print("  [FAIL] Monitor not running")
        failed += 1
    else:
        print("  [PASS] Monitor started")

        monitor.stop_monitoring()
        monitor.wait(2000)
        if monitor.isRunning():
            print("  [FAIL] Monitor failed to stop")
            failed += 1
        else:
            print("  [PASS] Monitor stopped")
            passed += 1

    # --------------------------------------------------
    # 测试 5: 暂停/恢复
    # --------------------------------------------------
    print("[TEST 5] Monitor pause/resume...")

    # 清空剪贴板，启动监控
    set_clipboard_text("")
    time.sleep(0.3)

    monitor.start()
    time.sleep(0.6)
    monitor.pause_monitoring()
    time.sleep(0.3)

    assert monitor.is_paused, "Monitor should be paused"

    count_before = db.get_count()
    set_clipboard_text("Paused text")
    time.sleep(0.8)

    if db.get_count() == count_before:
        print("  [PASS] Pause working")
        passed += 1
    else:
        print("  [FAIL] Content recorded while paused")
        failed += 1

    # 恢复
    monitor.resume_monitoring()
    set_clipboard_text("Resumed text")
    time.sleep(0.8)

    if db.get_count() > count_before:
        print("  [PASS] Resume working")
        passed += 1
    else:
        print("  [FAIL] Content not recorded after resume")
        failed += 1

    monitor.stop_monitoring()
    monitor.wait(2000)

    # --------------------------------------------------
    # 测试 6: 设置持久化
    # --------------------------------------------------
    print("[TEST 6] Settings persist...")
    cfg.set("retention_days", "1")
    cfg2 = Config(db)
    if cfg2.get("retention_days") == "1":
        print("  [PASS] Settings persisted")
        passed += 1
    else:
        print("  [FAIL] Settings not persisted")
        failed += 1
    cfg.set("retention_days", "3")  # 恢复默认

    # --------------------------------------------------
    # 清理
    # --------------------------------------------------
    # 删除测试期间写入的数据
    for item in db.get_items():
        db.delete_item(item["id"])
    db.close()

    print(f"\n{'='*40}")
    print(f"Passed: {passed}/{passed + failed}  |  Failed: {failed}")
    print(f"{'='*40}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
