"""应用配置管理模块。

配置以 key-value 形式存储在 SQLite 的 settings 表中。
首次启动时自动写入默认值。
"""

from src.database import Database


class Config:
    """应用配置管理器。"""

    DEFAULT_SETTINGS: dict[str, str] = {
        "retention_days": "3",
        "max_items": "500",
        "hotkey_enabled": "true",
        "hotkey_combo": "Ctrl+Shift+V",
        "auto_start": "true",
    }

    def __init__(self, db: Database):
        """初始化配置管理器并写入默认值（仅首次）。

        Args:
            db: Database 实例。
        """
        self.db = db
        self._init_defaults()

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------

    def _init_defaults(self) -> None:
        """将默认设置写入数据库（已存在的 key 会被忽略）。"""
        cursor = self.db.conn.cursor()
        for key, value in self.DEFAULT_SETTINGS.items():
            cursor.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
        self.db.conn.commit()

    # ------------------------------------------------------------------
    # 读写
    # ------------------------------------------------------------------

    def get(self, key: str) -> str:
        """读取字符串配置。不存在时返回默认值。"""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            return row["value"]
        return self.DEFAULT_SETTINGS.get(key, "")

    def set(self, key: str, value: str) -> None:
        """写入字符串配置。"""
        cursor = self.db.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, str(value)),
        )
        self.db.conn.commit()

    # ------------------------------------------------------------------
    # 类型转换
    # ------------------------------------------------------------------

    def get_int(self, key: str) -> int:
        """读取整数配置。"""
        try:
            return int(self.get(key))
        except ValueError:
            return int(self.DEFAULT_SETTINGS.get(key, 0))

    def get_bool(self, key: str) -> bool:
        """读取布尔配置。"""
        return self.get(key).lower() == "true"

    # ------------------------------------------------------------------
    # 工具
    # ------------------------------------------------------------------

    def reset_defaults(self) -> None:
        """将所有设置恢复为默认值。"""
        for key, value in self.DEFAULT_SETTINGS.items():
            self.set(key, value)
