"""阶段 4 验证脚本：测试主窗口和卡片组件。

验证 MainWindow 创建、列表刷新、搜索、卡片渲染、复制到剪贴板。
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
import win32clipboard

from src.database import Database
from src.ui.main_window import MainWindow


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_clipboard_text() -> str:
    """读取当前剪贴板文字。"""
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
            data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
            return data
        win32clipboard.CloseClipboard()
    except Exception:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass
    return ""


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    passed = 0
    failed = 0

    # 使用临时数据库
    db = Database(":memory:")

    # --------------------------------------------------
    # 测试 1: 窗口创建
    # --------------------------------------------------
    print("[TEST 1] Create MainWindow...")
    try:
        window = MainWindow(db)
        print("  [PASS] MainWindow created")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] Create failed: {e}")
        failed += 1
        db.close()
        sys.exit(1)

    # --------------------------------------------------
    # 测试 2: 空列表刷新
    # --------------------------------------------------
    print("[TEST 2] Refresh empty list...")
    try:
        window.refresh_list()
        # 空状态：empty_label 被加入 card_layout，parent 变为 card_container
        if (window.empty_label.parent() is window.card_container
                and not window.empty_label.isHidden()):
            print("  [PASS] Empty state shown")
            passed += 1
        else:
            print("  [FAIL] Empty state not visible")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] Refresh failed: {e}")
        failed += 1

    # --------------------------------------------------
    # 测试 3: 有数据时列表刷新
    # --------------------------------------------------
    print("[TEST 3] Refresh with items...")
    try:
        db.add_item("text", "Hello World", None)
        db.add_item("text", "Another item", None)
        window.refresh_list()

        if not window.empty_label.isVisible() and len(window._cards) == 2:
            print(f"  [PASS] 2 cards rendered")
            passed += 1
        else:
            print(f"  [FAIL] Expected 2 cards, got {len(window._cards)}")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] Refresh failed: {e}")
        failed += 1

    # --------------------------------------------------
    # 测试 4: 卡片排序（置顶优先）
    # --------------------------------------------------
    print("[TEST 4] Pin order check...")
    try:
        db.toggle_pin(1)  # 置顶第一条
        window.refresh_list()
        if window._cards[0].item["id"] == 1 and window._cards[0].item["pinned"] == 1:
            print("  [PASS] Pinned item first")
            passed += 1
        else:
            print("  [FAIL] Pinned item not first")
            failed += 1
        db.toggle_pin(1)  # 恢复
    except Exception as e:
        print(f"  [FAIL] Pin sort failed: {e}")
        failed += 1

    # --------------------------------------------------
    # 测试 5: 搜索过滤
    # --------------------------------------------------
    print("[TEST 5] Search filter...")
    try:
        window.search_input.setText("Hello")
        window.refresh_list()
        if len(window._cards) == 1 and "Hello" in window._cards[0].item["text_content"]:
            print("  [PASS] Search filtered correctly")
            passed += 1
        else:
            print(f"  [FAIL] Expected 1 result, got {len(window._cards)}")
            failed += 1
        window.search_input.clear()
        window.refresh_list()
    except Exception as e:
        print(f"  [FAIL] Search failed: {e}")
        failed += 1

    # --------------------------------------------------
    # 测试 6: 点击卡片 → 复制文字到剪贴板
    # --------------------------------------------------
    print("[TEST 6] Copy to clipboard...")
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.CloseClipboard()

        # 模拟点击第一个卡片
        card = window._cards[0]
        card.clicked.emit(card.item)
        # Qt 信号是同步的（DirectConnection），所以剪贴板已写入
        time.sleep(0.1)

        clipboard_content = get_clipboard_text()
        # 清空搜索后第一个卡片是 "Another item"（最新），还是 "Hello World"？
        # 按时间降序，最后添加的 "Another item" 在前
        if "Another item" in clipboard_content or "Hello World" in clipboard_content:
            print(f"  [PASS] Text copied: '{clipboard_content[:30]}'")
            passed += 1
        else:
            print(f"  [FAIL] Clipboard has: '{clipboard_content[:30]}'")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] Copy failed: {e}")
        failed += 1

    # --------------------------------------------------
    # 测试 7: 删除卡片
    # --------------------------------------------------
    print("[TEST 7] Delete item...")
    try:
        count_before = db.get_count()
        # 直接删除数据库记录，跳过确认对话框
        db.delete_item(window._cards[0].item["id"])
        window.refresh_list()

        if db.get_count() == count_before - 1:
            print("  [PASS] Item deleted")
            passed += 1
        else:
            print(f"  [FAIL] Count mismatch: {db.get_count()} != {count_before - 1}")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] Delete failed: {e}")
        failed += 1

    # --------------------------------------------------
    # 清理
    # --------------------------------------------------
    window.close()
    db.close()

    print(f"\n{'='*40}")
    print(f"Passed: {passed}/{passed + failed}  |  Failed: {failed}")
    print(f"{'='*40}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
