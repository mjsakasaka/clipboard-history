"""阶段 2 验证脚本：测试剪贴板监控。

通过程序化写入剪贴板来模拟用户复制操作，
验证 ClipboardMonitor 的检测、去重、暂停/恢复功能。
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

import win32clipboard
from src.database import Database
from src.clipboard_monitor import ClipboardMonitor


def set_clipboard_text(text: str) -> None:
    """将文字写入 Windows 剪贴板。"""
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
    win32clipboard.CloseClipboard()


def wait_monitor(ms: int = 800) -> None:
    """等待监控线程检测到剪贴板变化。"""
    time.sleep(ms / 1000)


def main():
    app = QApplication(sys.argv)

    db = Database(":memory:")
    monitor = ClipboardMonitor(db, image_dir="data/images")

    received_items = []
    # DirectConnection: 槽函数在监控线程内执行，无需事件循环
    monitor.new_item.connect(
        lambda item: received_items.append(item), Qt.DirectConnection
    )

    # 启动前清空剪贴板，避免残留内容干扰
    set_clipboard_text("")
    wait_monitor(100)

    monitor.start()
    wait_monitor(600)  # 等待第一次轮询

    # 清空监控启动后意外记录的内容，重置到已知基线
    received_items.clear()
    for item in db.get_items():
        db.delete_item(item["id"])

    passed = 0
    failed = 0

    # --------------------------------------------------
    # 测试 1: 检测文字复制
    # --------------------------------------------------
    print("[TEST 1] Copy text...")
    set_clipboard_text("Hello World")
    wait_monitor()

    if received_items and received_items[-1]["text_content"] == "Hello World":
        print("  [PASS] Text detected")
        passed += 1
    else:
        print("  [FAIL] Text not detected")
        failed += 1

    # --------------------------------------------------
    # 测试 2: 连续复制相同内容（去重）
    # --------------------------------------------------
    print("[TEST 2] Copy same text again (dedup)...")
    count_before = len(received_items)
    set_clipboard_text("Hello World")
    wait_monitor()

    if len(received_items) == count_before:
        print("  [PASS] Duplicate filtered")
        passed += 1
    else:
        print("  [FAIL] Duplicate was not filtered")
        failed += 1

    # --------------------------------------------------
    # 测试 3: 不同文字
    # --------------------------------------------------
    print("[TEST 3] Copy different text...")
    count_before = len(received_items)
    set_clipboard_text("Different content")
    wait_monitor()

    if len(received_items) == count_before + 1:
        print("  [PASS] New text recorded")
        passed += 1
    else:
        print("  [FAIL] New text not recorded")
        failed += 1

    # --------------------------------------------------
    # 测试 4: 数据库记录
    # --------------------------------------------------
    print("[TEST 4] Check database...")
    count = db.get_count()
    items = db.get_items()
    if count == 2:
        print(f"  [PASS] DB has 2 items")
        passed += 1
    else:
        print(f"  [FAIL] Expected 2 items, got {count}")
        failed += 1

    # 验证排序：最新在前
    if items[0]["text_content"] == "Different content":
        print("  [PASS] Order is correct (newest first)")
        passed += 1
    else:
        print("  [FAIL] Order wrong")
        failed += 1

    # --------------------------------------------------
    # 测试 5: 暂停监控
    # --------------------------------------------------
    print("[TEST 5] Pause monitoring...")
    monitor.pause_monitoring()
    assert monitor.is_paused
    set_clipboard_text("Should be ignored")
    wait_monitor()

    db_count_paused = db.get_count()
    if db_count_paused == 2:
        print("  [PASS] Paused — content ignored")
        passed += 1
    else:
        print(f"  [FAIL] Paused but content was recorded (count={db_count_paused})")
        failed += 1

    # --------------------------------------------------
    # 测试 6: 恢复监控
    # --------------------------------------------------
    print("[TEST 6] Resume monitoring...")
    monitor.resume_monitoring()
    assert not monitor.is_paused
    set_clipboard_text("After resume")
    wait_monitor()

    db_count_resumed = db.get_count()
    if db_count_resumed == 3:
        print("  [PASS] Resumed — new content recorded")
        passed += 1
    else:
        print(f"  [FAIL] Resumed but content not recorded (count={db_count_resumed})")
        failed += 1

    # --------------------------------------------------
    # 测试 7: 空内容不记录
    # --------------------------------------------------
    print("[TEST 7] Empty/whitespace content...")
    count_before = db.get_count()
    # 写入空白剪贴板
    set_clipboard_text("   ")
    wait_monitor()

    if db.get_count() == count_before:
        print("  [PASS] Whitespace-only content ignored")
        passed += 1
    else:
        print("  [FAIL] Whitespace was recorded")
        failed += 1

    # --------------------------------------------------
    # 清理
    # --------------------------------------------------
    monitor.stop_monitoring()
    monitor.wait()
    db.close()

    total_checks = passed + failed
    print(f"\n{'='*40}")
    print(f"Passed: {passed}/{total_checks}  |  Failed: {failed}")
    print(f"{'='*40}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
