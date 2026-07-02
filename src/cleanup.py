"""定时清理模块。

每小时检查并删除过期和超量的剪贴板记录，同时清理关联的图片文件。
"""

import os

from PySide6.QtCore import QObject, QTimer, Signal

from src.database import Database
from src.config import Config


class CleanupManager(QObject):
    """定时清理管理器。

    使用 QTimer 周期性触发清理，支持过期和超量两种策略。

    Signals:
        cleaned: 清理完成后触发，通知 UI 刷新。
    """

    cleaned = Signal()

    # 清理间隔（毫秒）
    INTERVAL = 60 * 60 * 1000  # 1 小时

    def __init__(self, db: Database, cfg: Config, parent: QObject | None = None):
        """
        Args:
            db: Database 实例。
            cfg: Config 实例。
        """
        super().__init__(parent)
        self.db = db
        self.cfg = cfg

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.run)
        self._timer.start(self.INTERVAL)

    # ------------------------------------------------------------------
    # 清理逻辑
    # ------------------------------------------------------------------

    def run(self) -> None:
        """执行一次清理（启动时也会手动调用一次）。"""
        changed = False

        # 1. 过期清理
        retention = self.cfg.get_int("retention_days")
        expired = self.db.get_expired_ids(retention)
        if expired:
            self._remove_image_files(expired)
            self.db.delete_by_ids([eid for eid, _ in expired])
            changed = True

        # 2. 超量清理
        max_items = self.cfg.get_int("max_items")
        overflow = self.db.delete_oldest_unpinned(max_items)
        if overflow:
            self._remove_image_files(overflow)
            self.db.delete_by_ids([oid for oid, _ in overflow])
            changed = True

        if changed:
            self.cleaned.emit()

    def stop(self) -> None:
        """停止定时器。"""
        self._timer.stop()

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    @staticmethod
    def _remove_image_files(items: list[tuple[int, str | None]]) -> None:
        """删除记录关联的图片文件。"""
        for _, img_path in items:
            if img_path and os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except OSError:
                    pass
