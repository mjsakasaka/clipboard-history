"""SQLite 数据库操作模块。

提供剪贴板记录的增删查改，以及应用设置的读写。
"""

import os
import sqlite3


class Database:
    """剪贴板历史数据库管理类。"""

    def __init__(self, db_path: str = "data/clipboard.db"):
        """初始化数据库连接，自动创建表结构。

        Args:
            db_path: 数据库文件路径。目录不存在时自动创建。
        """
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")  # 提高并发读写性能
        self._init_tables()

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------

    def _init_tables(self) -> None:
        """创建数据库表（如不存在则创建）。"""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clipboard_items (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type TEXT    NOT NULL CHECK(content_type IN ('text', 'image')),
                text_content TEXT,
                image_path   TEXT,
                pinned       INTEGER DEFAULT 0 CHECK(pinned IN (0, 1)),
                created_at   TIMESTAMP DEFAULT (datetime('now', 'localtime'))
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at
                ON clipboard_items(created_at DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pinned
                ON clipboard_items(pinned)
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        self.conn.commit()

    # ------------------------------------------------------------------
    # 剪贴板记录 CRUD
    # ------------------------------------------------------------------

    def add_item(
        self,
        content_type: str,
        text_content: str | None = None,
        image_path: str | None = None,
    ) -> int:
        """新增一条剪贴板记录。

        Args:
            content_type: 'text' 或 'image'。
            text_content: 文字内容，图片时为 None。
            image_path: 图片文件路径，文字时为 None。

        Returns:
            新插入记录的自增 ID。
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO clipboard_items (content_type, text_content, image_path) "
            "VALUES (?, ?, ?)",
            (content_type, text_content, image_path),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_items(
        self,
        search: str = "",
        limit: int = 500,
        offset: int = 0,
    ) -> list[dict]:
        """查询剪贴板记录列表。

        - 置顶项优先，同组按时间降序。
        - 搜索时仅匹配文字类型记录。

        Args:
            search: 搜索关键词（空字符串表示不过滤）。
            limit: 每页条数。
            offset: 偏移量。

        Returns:
            记录字典列表，字段与表结构一致。
        """
        cursor = self.conn.cursor()
        if search:
            cursor.execute(
                "SELECT * FROM clipboard_items "
                "WHERE content_type = 'text' AND text_content LIKE ? "
                "ORDER BY pinned DESC, created_at DESC "
                "LIMIT ? OFFSET ?",
                (f"%{search}%", limit, offset),
            )
        else:
            cursor.execute(
                "SELECT * FROM clipboard_items "
                "ORDER BY pinned DESC, created_at DESC "
                "LIMIT ? OFFSET ?",
                (limit, offset),
            )
        return [dict(row) for row in cursor.fetchall()]

    def toggle_pin(self, item_id: int) -> None:
        """切换记录的置顶状态（0→1, 1→0）。"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE clipboard_items "
            "SET pinned = CASE WHEN pinned = 0 THEN 1 ELSE 0 END "
            "WHERE id = ?",
            (item_id,),
        )
        self.conn.commit()

    def delete_item(self, item_id: int) -> str | None:
        """删除一条记录。

        同时返回该记录关联的图片路径（如有），供调用方删除物理文件。

        Args:
            item_id: 记录 ID。

        Returns:
            图片文件路径，无图片时返回 None。
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT image_path FROM clipboard_items WHERE id = ?", (item_id,)
        )
        row = cursor.fetchone()
        image_path = row["image_path"] if row else None

        cursor.execute("DELETE FROM clipboard_items WHERE id = ?", (item_id,))
        self.conn.commit()
        return image_path

    # ------------------------------------------------------------------
    # 清理相关
    # ------------------------------------------------------------------

    def get_expired_ids(self, retention_days: int) -> list[tuple[int, str | None]]:
        """查找过期（超过保留天数）且未置顶的记录。

        Args:
            retention_days: 保留天数。

        Returns:
            [(id, image_path), ...] 列表。
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, image_path FROM clipboard_items "
            "WHERE pinned = 0 "
            "AND datetime(created_at) < datetime('now', 'localtime', ? || ' days')",
            (f"-{retention_days}",),
        )
        return [(row["id"], row["image_path"]) for row in cursor.fetchall()]

    def delete_oldest_unpinned(
        self, keep_count: int
    ) -> list[tuple[int, str | None]]:
        """超出 max_items 时，找出最旧且未置顶的多余记录。

        Args:
            keep_count: 保留的最大条数。

        Returns:
            [(id, image_path), ...] 待删除记录列表。
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM clipboard_items")
        total = cursor.fetchone()["cnt"]

        if total <= keep_count:
            return []

        excess = total - keep_count
        cursor.execute(
            "SELECT id, image_path FROM clipboard_items "
            "WHERE pinned = 0 "
            "ORDER BY created_at ASC "
            "LIMIT ?",
            (excess,),
        )
        return [(row["id"], row["image_path"]) for row in cursor.fetchall()]

    def delete_by_ids(self, ids: list[int]) -> None:
        """批量删除记录（不删除图片文件，由调用方处理）。"""
        if not ids:
            return
        cursor = self.conn.cursor()
        placeholders = ",".join("?" * len(ids))
        cursor.execute(
            f"DELETE FROM clipboard_items WHERE id IN ({placeholders})", ids
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # 工具
    # ------------------------------------------------------------------

    def get_count(self) -> int:
        """返回总记录数。"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM clipboard_items")
        return cursor.fetchone()["cnt"]

    def close(self) -> None:
        """关闭数据库连接。"""
        self.conn.close()
