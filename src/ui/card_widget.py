"""卡片组件模块。

每条剪贴板历史记录渲染为一张卡片，包含内容预览、时间戳和操作按钮。
"""

from datetime import datetime

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap


class CardWidget(QFrame):
    """单条剪贴板历史卡片。

    Signals:
        clicked: 用户点击卡片内容区域。
        pin_toggled: 用户切换置顶状态，参数为 item_id。
        delete_requested: 用户请求删除，参数为 item_id。
    """

    clicked = Signal(dict)
    pin_toggled = Signal(int)
    delete_requested = Signal(int)

    # 样式常量
    STYLE_NORMAL = """
        CardWidget {
            background-color: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 4px;
        }
    """
    STYLE_HOVER = """
        CardWidget {
            background-color: #F0F0F0;
            border: 1px solid #D0D0D0;
            border-radius: 4px;
        }
    """

    def __init__(self, item: dict, parent=None):
        """
        Args:
            item: 数据库记录字典（id, content_type, text_content, image_path,
                  pinned, created_at）。
        """
        super().__init__(parent)
        self.item = item
        self.setStyleSheet(self.STYLE_NORMAL)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._build_ui()
        self._apply_pin_style()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """构建卡片布局。"""
        root = QHBoxLayout(self)
        root.setContentsMargins(12, 8, 8, 8)
        root.setSpacing(8)

        # ---- 左侧：内容预览 ----
        preview = self._create_preview()
        root.addLayout(preview, 1)

        # ---- 右侧：操作按钮 ----
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(4)

        self.pin_btn = QPushButton()
        self.pin_btn.setFixedSize(28, 28)
        self.pin_btn.setToolTip("Pin / Unpin")
        self.pin_btn.clicked.connect(lambda: self.pin_toggled.emit(self.item["id"]))
        btn_layout.addWidget(self.pin_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.delete_btn = QPushButton()
        self.delete_btn.setFixedSize(28, 28)
        self.delete_btn.setToolTip("Delete")
        self.delete_btn.clicked.connect(
            lambda: self.delete_requested.emit(self.item["id"])
        )
        btn_layout.addWidget(self.delete_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        btn_layout.addStretch()
        root.addLayout(btn_layout)

    def _create_preview(self) -> QVBoxLayout:
        """创建内容预览区域布局。"""
        layout = QVBoxLayout()
        layout.setSpacing(4)

        if self.item["content_type"] == "text":
            content = QLabel(self._truncate_text(self.item.get("text_content", "")))
            content.setWordWrap(True)
            content.setMaximumHeight(60)
            content.setStyleSheet("color: #333333; font-size: 12px;")
            layout.addWidget(content)
        else:
            thumb = QLabel()
            pixmap = QPixmap(self.item.get("image_path", ""))
            if not pixmap.isNull():
                pixmap = pixmap.scaledToHeight(
                    60, Qt.TransformationMode.SmoothTransformation
                )
            thumb.setPixmap(pixmap)
            thumb.setFixedHeight(60)
            thumb.setStyleSheet("border-radius: 2px;")
            layout.addWidget(thumb)

        # 时间戳
        ts = QLabel(self._format_time(self.item.get("created_at", "")))
        ts.setStyleSheet("color: #9E9E9E; font-size: 10px;")
        layout.addWidget(ts)

        return layout

    # ------------------------------------------------------------------
    # 样式 & 事件
    # ------------------------------------------------------------------

    def _apply_pin_style(self) -> None:
        """根据置顶状态设置按钮样式。"""
        is_pinned = self.item.get("pinned", 0) == 1
        if is_pinned:
            self.pin_btn.setText("\U0001f4cc")  # 📌
            self.pin_btn.setStyleSheet("""
                QPushButton { font-size: 14px; border: none; color: #FFA726; }
                QPushButton:hover { color: #FF9800; }
            """)
        else:
            self.pin_btn.setText("\U0001f4cc")  # 同样图标
            self.pin_btn.setStyleSheet("""
                QPushButton { font-size: 14px; border: none; color: #BDBDBD; }
                QPushButton:hover { color: #FFA726; }
            """)

        self.delete_btn.setText("\U0001f5d1")  # 🗑
        self.delete_btn.setStyleSheet("""
            QPushButton { font-size: 14px; border: none; color: #BDBDBD; }
            QPushButton:hover { color: #EF5350; }
        """)

    def enterEvent(self, event) -> None:
        """鼠标进入 → 悬停样式。"""
        self.setStyleSheet(self.STYLE_HOVER)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """鼠标离开 → 恢复默认样式。"""
        self.setStyleSheet(self.STYLE_NORMAL)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        """点击卡片 → 触发复制（阶段 5 完善）。"""
        self.clicked.emit(self.item)
        super().mousePressEvent(event)

    # ------------------------------------------------------------------
    # 工具
    # ------------------------------------------------------------------

    @staticmethod
    def _truncate_text(text: str, max_lines: int = 3, max_chars: int = 80) -> str:
        """截断过长文字，用于预览。"""
        if not text:
            return ""
        # 单行截断
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        # 多行截断
        lines = text.split("\n")
        if len(lines) > max_lines:
            text = "\n".join(lines[:max_lines]) + "..."
        return text

    @staticmethod
    def _format_time(ts: str) -> str:
        """格式化 SQLite 时间戳为可读格式。"""
        if not ts:
            return ""
        try:
            dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return ts
        now = datetime.now()
        diff = now - dt
        if diff.days == 0:
            return dt.strftime("Today %H:%M")
        elif diff.days == 1:
            return dt.strftime("Yesterday %H:%M")
        else:
            return dt.strftime("%Y-%m-%d %H:%M")
