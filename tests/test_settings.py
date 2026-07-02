"""阶段 6 验证脚本：测试设置对话框和全局热键。

验证设置读写、热键解析和注册/注销。
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from src.database import Database
from src.config import Config
from src.ui.settings_dialog import SettingsDialog
from src.utils.hotkey import HotkeyManager


def main():
    app = QApplication(sys.argv)

    passed = 0
    failed = 0

    db = Database(":memory:")
    cfg = Config(db)

    # --------------------------------------------------
    # 测试 1: 设置对话框加载默认值
    # --------------------------------------------------
    print("[TEST 1] SettingsDialog loads defaults...")
    try:
        dlg = SettingsDialog(cfg)
        if (dlg.retention_combo.currentText() == "3"
                and dlg.max_items_spin.value() == 500
                and dlg.hotkey_check.isChecked() is True
                and dlg.autostart_check.isChecked() is True):
            print("  [PASS] All defaults loaded correctly")
            passed += 1
        else:
            print(f"  [FAIL] Values: retention={dlg.retention_combo.currentText()}, "
                  f"max={dlg.max_items_spin.value()}, "
                  f"hotkey={dlg.hotkey_check.isChecked()}, "
                  f"autostart={dlg.autostart_check.isChecked()}")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1

    # --------------------------------------------------
    # 测试 2: 设置对话框保存
    # --------------------------------------------------
    print("[TEST 2] SettingsDialog save...")
    try:
        dlg = SettingsDialog(cfg)
        dlg.retention_combo.setCurrentText("5")
        dlg.max_items_spin.setValue(1000)
        dlg.hotkey_check.setChecked(False)
        dlg.autostart_check.setChecked(False)
        dlg._on_save()

        if (cfg.get("retention_days") == "5"
                and cfg.get_int("max_items") == 1000
                and cfg.get_bool("hotkey_enabled") is False
                and cfg.get_bool("auto_start") is False):
            print("  [PASS] Settings saved correctly")
            passed += 1
        else:
            print("  [FAIL] Settings not saved")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1

    # 恢复默认
    cfg.reset_defaults()

    # --------------------------------------------------
    # 测试 3: 快捷键编辑
    # --------------------------------------------------
    print("[TEST 3] Key sequence edit...")
    try:
        dlg = SettingsDialog(cfg)
        from PySide6.QtGui import QKeySequence
        dlg.hotkey_edit.setKeySequence(QKeySequence("Ctrl+Alt+X"))
        dlg._on_save()
        saved = cfg.get("hotkey_combo")
        if "Ctrl" in saved and "Alt" in saved and "X" in saved:
            print(f"  [PASS] Hotkey saved: '{saved}'")
            passed += 1
        else:
            print(f"  [FAIL] Unexpected combo: '{saved}'")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1

    cfg.reset_defaults()

    # --------------------------------------------------
    # 测试 4: HotkeyManager 解析组合键
    # --------------------------------------------------
    print("[TEST 4] HotkeyManager parse combo...")
    try:
        parsed = HotkeyManager._parse_combo("Ctrl+Shift+V")
        if parsed == ["Ctrl", "Shift", "V"]:
            print("  [PASS] Combo parsed correctly")
            passed += 1
        else:
            print(f"  [FAIL] Got: {parsed}")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1

    # --------------------------------------------------
    # 测试 5: pynput 键名转换
    # --------------------------------------------------
    print("[TEST 5] Pynput key name conversion...")
    try:
        ctrl_name = HotkeyManager._to_pynput_name("Ctrl")
        shift_name = HotkeyManager._to_pynput_name("Shift")
        v_name = HotkeyManager._to_pynput_name("V")
        # Ctrl → <ctrl>, Shift → <shift>, V → v
        if ctrl_name == "<ctrl>" and shift_name == "<shift>" and v_name == "v":
            print(f"  [PASS] Names: {ctrl_name}, {shift_name}, {v_name}")
            passed += 1
        else:
            print(f"  [FAIL] Got: {ctrl_name}, {shift_name}, {v_name}")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1

    # --------------------------------------------------
    # 测试 6: HotkeyManager 注册和注销
    # --------------------------------------------------
    print("[TEST 6] HotkeyManager register/unregister...")
    try:
        mgr = HotkeyManager()
        activated = []

        def on_activated():
            activated.append(True)

        mgr.activated.connect(on_activated)

        # 注册热键
        mgr.register("Ctrl+Shift+V")
        time.sleep(0.5)
        if mgr._listener is not None and mgr._thread is not None:
            print("  [PASS] Hotkey registered (listener running)")
            passed += 1
        else:
            print("  [FAIL] Listener not running")
            failed += 1

        # 注销
        mgr.unregister()
        time.sleep(0.5)
        if mgr._listener is None:
            print("  [PASS] Hotkey unregistered")
            passed += 1
        else:
            print("  [FAIL] Listener still active")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1

    # --------------------------------------------------
    # 测试 7: 无效快捷键不崩溃
    # --------------------------------------------------
    print("[TEST 7] Invalid hotkey combo...")
    try:
        mgr = HotkeyManager()
        mgr.register("")  # 空字符串
        # 应打印警告但不崩溃
        print("  [PASS] Invalid combo handled gracefully")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1

    # --------------------------------------------------
    # 测试 8: 快捷键开关联动
    # --------------------------------------------------
    print("[TEST 8] Hotkey checkbox ↔ edit enabled...")
    try:
        dlg = SettingsDialog(cfg)
        # 初始：勾选 → 编辑框可用
        if dlg.hotkey_edit.isEnabled() is True:
            print("  [PASS] Edit enabled when checkbox checked")
            passed += 1
        else:
            print("  [FAIL] Edit should be enabled")
            failed += 1

        dlg.hotkey_check.setChecked(False)
        if dlg.hotkey_edit.isEnabled() is False:
            print("  [PASS] Edit disabled when checkbox unchecked")
            passed += 1
        else:
            print("  [FAIL] Edit should be disabled")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 2  # Two checks failed

    # --------------------------------------------------
    # 清理
    # --------------------------------------------------
    db.close()

    print(f"\n{'='*40}")
    print(f"Passed: {passed}/{passed + failed}  |  Failed: {failed}")
    print(f"{'='*40}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
