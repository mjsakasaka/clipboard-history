"""阶段 7 验证脚本：测试清理管理器和托盘状态。

验证过期清理、超量清理、图片文件删除、托盘暂停状态切换。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication

from src.database import Database
from src.config import Config
from src.cleanup import CleanupManager
from src.ui.tray_icon import TrayIcon


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    app = QApplication(sys.argv)

    passed = 0
    failed = 0

    db = Database(":memory:")
    cfg = Config(db)

    # --------------------------------------------------
    # 测试 1: CleanupManager 创建
    # --------------------------------------------------
    print("[TEST 1] Create CleanupManager...")
    try:
        mgr = CleanupManager(db, cfg)
        print("  [PASS] CleanupManager created")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1
        db.close()
        sys.exit(1)

    # --------------------------------------------------
    # 测试 2: 过期记录被清理
    # --------------------------------------------------
    print("[TEST 2] Expired items cleaned...")
    try:
        # 插入一条 5 天前的记录
        cursor = db.conn.cursor()
        cursor.execute(
            "INSERT INTO clipboard_items (content_type, text_content, created_at) "
            "VALUES ('text', 'old', datetime('now', 'localtime', '-5 days'))"
        )
        # 插入一条 1 小时前的记录
        cursor.execute(
            "INSERT INTO clipboard_items (content_type, text_content, created_at) "
            "VALUES ('text', 'recent', datetime('now', 'localtime', '-1 hour'))"
        )
        db.conn.commit()

        # 保留天数设为 3 → 5 天前的应被删，1 小时前的保留
        cfg.set("retention_days", "3")
        mgr.run()

        items = db.get_items()
        ids = [it["id"] for it in items]
        # recent 保留，old 删除
        recent = [it for it in items if it["text_content"] == "recent"]
        old = [it for it in items if it["text_content"] == "old"]

        if len(recent) == 1 and len(old) == 0:
            print("  [PASS] Expired item removed, recent kept")
            passed += 1
        else:
            print(f"  [FAIL] recent={len(recent)}, old={len(old)}")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1

    # 清理
    cfg.set("retention_days", "3")
    for item in db.get_items():
        db.delete_item(item["id"])

    # --------------------------------------------------
    # 测试 3: 超量记录被清理
    # --------------------------------------------------
    print("[TEST 3] Overflow items cleaned...")
    try:
        inserted_ids = []
        for i in range(5):
            item_id = db.add_item("text", f"item {i+1}", None)
            inserted_ids.append(item_id)

        cfg.set("max_items", "3")
        mgr.run()

        if db.get_count() == 3:
            # 最旧的 2 条应被删，最新的 3 条保留
            items = db.get_items()
            ids = [it["id"] for it in items]
            oldest = inserted_ids[:2]  # 最旧的 2 个 ID
            newest = inserted_ids[2:]  # 最新的 3 个 ID
            if all(oid not in ids for oid in oldest) and all(nid in ids for nid in newest):
                print("  [PASS] Oldest unpinned removed, kept 3 newest")
                passed += 1
            else:
                print(f"  [FAIL] Remaining ids: {ids}, expected newest: {newest}")
                failed += 1
        else:
            print(f"  [FAIL] Expected 3, got {db.get_count()}")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1

    # 清理
    cfg.set("max_items", "500")
    for item in db.get_items():
        db.delete_item(item["id"])

    # --------------------------------------------------
    # 测试 4: 置顶记录不被清理
    # --------------------------------------------------
    print("[TEST 4] Pinned items protected...")
    try:
        pinned_id = db.add_item("text", "pinned item", None)
        normal_id = db.add_item("text", "normal old", None)
        db.toggle_pin(pinned_id)  # 置顶第一条

        cfg.set("max_items", "1")
        mgr.run()

        items = db.get_items()
        # 置顶的保留，普通的被删
        if db.get_count() == 1 and items[0]["pinned"] == 1:
            print("  [PASS] Pinned item preserved")
            passed += 1
        else:
            print(f"  [FAIL] Count={db.get_count()}, pinned={items[0]['pinned'] if items else 'N/A'}")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1

    # 清理
    cfg.set("max_items", "500")
    for item in db.get_items():
        db.delete_item(item["id"])

    # --------------------------------------------------
    # 测试 5: 图片文件随记录删除
    # --------------------------------------------------
    print("[TEST 5] Image file deleted with record...")
    try:
        # 创建临时图片文件
        test_img_path = os.path.join(PROJECT_ROOT, "data", "images", "_test_cleanup.png")
        os.makedirs(os.path.dirname(test_img_path), exist_ok=True)
        with open(test_img_path, "w") as f:
            f.write("fake image data")

        db.add_item("image", None, test_img_path)
        cursor = db.conn.cursor()
        cursor.execute(
            "UPDATE clipboard_items SET created_at = datetime('now', 'localtime', '-10 days') "
            "WHERE image_path = ?", (test_img_path,)
        )
        db.conn.commit()

        cfg.set("retention_days", "1")
        mgr.run()

        if not os.path.exists(test_img_path) and db.get_count() == 0:
            print("  [PASS] Image file removed with expired record")
            passed += 1
        else:
            print(f"  [FAIL] File exists={os.path.exists(test_img_path)}, count={db.get_count()}")
            failed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1

    cfg.set("retention_days", "3")

    # --------------------------------------------------
    # 测试 6: 托盘暂停状态切换文本
    # --------------------------------------------------
    print("[TEST 6] Tray pause/resume text toggle...")
    try:
        icon_path = os.path.join(PROJECT_ROOT, "assets", "icon.png")
        tray = TrayIcon(icon_path=icon_path)

        # 初始：未暂停
        assert tray.pause_action.text() == "Pause Monitoring"

        # 模拟点击暂停
        tray.pause_action.setChecked(True)
        # toggled 信号触发 → 文本和提示已更新
        assert "Resume" in tray.pause_action.text()
        assert "Paused" in tray.toolTip()
        print("  [PASS] Pause state: text and tooltip updated")
        passed += 1

        # 恢复
        tray.pause_action.setChecked(False)
        assert tray.pause_action.text() == "Pause Monitoring"
        assert "Paused" not in tray.toolTip()
        print("  [PASS] Resume state: text and tooltip restored")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1

    # --------------------------------------------------
    # 清理
    # --------------------------------------------------
    mgr.stop()
    db.close()

    print(f"\n{'='*40}")
    print(f"Passed: {passed}/{passed + failed}  |  Failed: {failed}")
    print(f"{'='*40}")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
