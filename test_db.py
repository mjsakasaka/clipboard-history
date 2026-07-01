"""阶段 1 验证脚本：测试 database.py 和 config.py。

使用内存数据库（:memory:），不影响正式数据。
"""

import sys
import os

# 确保 src 在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import Database
from src.config import Config


def test_create_tables():
    """验证建表。"""
    db = Database(":memory:")
    cursor = db.conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [r["name"] for r in cursor.fetchall()]
    assert "clipboard_items" in tables, "clipboard_items 表缺失"
    assert "settings" in tables, "settings 表缺失"
    db.close()
    print("  [PASS] test_create_tables")


def test_add_text():
    """验证添加文字记录。"""
    db = Database(":memory:")
    item_id = db.add_item("text", "Hello World", None)
    assert item_id == 1
    assert db.get_count() == 1
    db.close()
    print("  [PASS] test_add_text")


def test_add_image():
    """验证添加图片记录。"""
    db = Database(":memory:")
    item_id = db.add_item("image", None, "data/images/test.png")
    items = db.get_items()
    assert items[0]["content_type"] == "image"
    assert items[0]["image_path"] == "data/images/test.png"
    db.close()
    print("  [PASS] test_add_image")


def test_get_items_order():
    """验证排序：置顶优先 + 时间降序。"""
    db = Database(":memory:")
    db.add_item("text", "item 1", None)
    db.add_item("text", "item 2", None)
    db.add_item("text", "item 3", None)
    db.toggle_pin(3)  # 置顶第 3 条

    items = db.get_items()
    assert items[0]["id"] == 3, "置顶项应排第一"
    assert items[1]["id"] == 2, "最新未置顶排第二"
    assert items[2]["id"] == 1, "最旧排最后"
    db.close()
    print("  [PASS] test_get_items_order")


def test_search():
    """验证搜索过滤。"""
    db = Database(":memory:")
    db.add_item("text", "苹果很好吃", None)
    db.add_item("text", "香蕉也不错", None)
    db.add_item("image", None, "test.png")  # 图片不应被搜到

    results = db.get_items(search="苹果")
    assert len(results) == 1
    assert "苹果" in results[0]["text_content"]
    db.close()
    print("  [PASS] test_search")


def test_toggle_pin():
    """验证置顶状态切换。"""
    db = Database(":memory:")
    item_id = db.add_item("text", "test", None)

    db.toggle_pin(item_id)
    items = db.get_items()
    assert items[0]["pinned"] == 1

    db.toggle_pin(item_id)
    items = db.get_items()
    assert items[0]["pinned"] == 0
    db.close()
    print("  [PASS] test_toggle_pin")


def test_delete_item():
    """验证删除并返回 image_path。"""
    db = Database(":memory:")
    db.add_item("text", "text item", None)
    img_id = db.add_item("image", None, "data/images/to_delete.png")

    # 删除文字记录
    path = db.delete_item(1)
    assert path is None
    assert db.get_count() == 1

    # 删除图片记录
    path = db.delete_item(img_id)
    assert path == "data/images/to_delete.png"
    assert db.get_count() == 0
    db.close()
    print("  [PASS] test_delete_item")


def test_get_expired_ids():
    """验证过期查询。"""
    db = Database(":memory:")
    # 手动插入一条"过去"的记录
    cursor = db.conn.cursor()
    cursor.execute(
        "INSERT INTO clipboard_items (content_type, text_content, created_at) "
        "VALUES ('text', 'old item', datetime('now', 'localtime', '-5 days'))"
    )
    db.conn.commit()

    expired = db.get_expired_ids(retention_days=3)
    assert len(expired) == 1, "5天前的记录应被标记为过期（保留3天）"

    expired = db.get_expired_ids(retention_days=7)
    assert len(expired) == 0, "5天前的记录在保留7天时不应过期"
    db.close()
    print("  [PASS] test_get_expired_ids")


def test_delete_oldest_unpinned():
    """验证超量清理：返回最旧未置顶的多余记录。"""
    db = Database(":memory:")
    db.add_item("text", "item 1", None)
    db.add_item("text", "item 2", None)
    db.add_item("text", "item 3", None)
    db.toggle_pin(3)  # 置顶第 3 条

    # 保持 2 条，应删除 1 条最旧未置顶（id=1）
    to_delete = db.delete_oldest_unpinned(keep_count=2)
    assert len(to_delete) == 1
    assert to_delete[0][0] == 1  # id=1 是最旧未置顶

    # 保持 100 条，不应删除
    to_delete = db.delete_oldest_unpinned(keep_count=100)
    assert len(to_delete) == 0
    db.close()
    print("  [PASS] test_delete_oldest_unpinned")


def test_batch_delete():
    """验证批量删除。"""
    db = Database(":memory:")
    db.add_item("text", "a", None)
    db.add_item("text", "b", None)
    db.add_item("text", "c", None)

    db.delete_by_ids([1, 3])
    assert db.get_count() == 1
    items = db.get_items()
    assert items[0]["id"] == 2
    db.close()
    print("  [PASS] test_batch_delete")


# ------------------------------------------------------------------
# config.py 测试
# ------------------------------------------------------------------


def test_config_defaults():
    """验证默认配置写入。"""
    db = Database(":memory:")
    cfg = Config(db)

    assert cfg.get("retention_days") == "3"
    assert cfg.get("max_items") == "500"
    assert cfg.get_int("max_items") == 500
    assert cfg.get_bool("hotkey_enabled") is True
    assert cfg.get("nonexistent") == ""  # 不存在的 key
    db.close()
    print("  [PASS] test_config_defaults")


def test_config_set_and_persist():
    """验证配置读写和持久化。"""
    db = Database(":memory:")
    cfg = Config(db)

    cfg.set("retention_days", "5")
    cfg.set("max_items", "100")
    cfg.set("hotkey_enabled", "false")

    assert cfg.get("retention_days") == "5"
    assert cfg.get_int("max_items") == 100
    assert cfg.get_bool("hotkey_enabled") is False
    db.close()
    print("  [PASS] test_config_set_and_persist")


def test_config_reset():
    """验证重置为默认值。"""
    db = Database(":memory:")
    cfg = Config(db)

    cfg.set("retention_days", "99")
    cfg.reset_defaults()
    assert cfg.get("retention_days") == "3"
    db.close()
    print("  [PASS] test_config_reset")


# ------------------------------------------------------------------
# 主入口
# ------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Stage 1 Test: Data Layer ===\n")

    tests = [
        ("建表", test_create_tables),
        ("添加文字", test_add_text),
        ("添加图片", test_add_image),
        ("排序规则", test_get_items_order),
        ("搜索过滤", test_search),
        ("置顶切换", test_toggle_pin),
        ("删除记录", test_delete_item),
        ("过期查询", test_get_expired_ids),
        ("超量清理", test_delete_oldest_unpinned),
        ("批量删除", test_batch_delete),
        ("配置默认值", test_config_defaults),
        ("配置读写", test_config_set_and_persist),
        ("配置重置", test_config_reset),
    ]

    passed = 0
    failed = 0

    for name, fn in tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"  [FAIL] {name}: {e}")

    print(f"\n{'='*40}")
    print(f"Passed: {passed}/{len(tests)}  |  Failed: {failed}")
    print(f"{'='*40}")

    if failed > 0:
        sys.exit(1)
