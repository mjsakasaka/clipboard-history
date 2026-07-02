"""主窗口模块。

显示剪贴板历史卡片列表，提供搜索、复制、置顶、删除功能。
"""

import os

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QLabel,
    QMessageBox,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon

import win32clipboard
from PIL import Image

from src.database import Database
from src.ui.card_widget import CardWidget


class MainWindow(QWidget):
    """剪贴板历史主窗口。

    搜索栏 + 卡片列表，支持实时搜索、复制到剪贴板、置顶和删除。

    Signals:
        settings_requested: 用户点击工具栏设置按钮。
    """

    settings_requested = Signal()

    def __init__(self, db: Database, icon_path: str = "assets/icon.png", parent=None):
        """
        Args:
            db: Database 实例。
            icon_path: 窗口图标路径。
        """
        super().__init__(parent)
        self.db = db

        self.setWindowTitle("Clipboard History")
        self.setMinimumSize(360, 440)
        self.resize(400, 560)

        # 窗口关闭 → 隐藏而非退出
        self.setWindowIcon(QIcon(icon_path))

        self._cards: list[CardWidget] = []
        self._toast_timer: QTimer | None = None

        self._build_ui()
        self.refresh_list()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """构建主窗口布局。"""
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- 顶部栏 ----
        toolbar = self._create_toolbar()
        root.addLayout(toolbar)

        # ---- 卡片列表 ----
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background-color: #FAFAFA; }
            QScrollBar:vertical {
                width: 6px; background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #BDBDBD; border-radius: 3px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #9E9E9E; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.card_container = QWidget()
        self.card_container.setStyleSheet("background-color: #FAFAFA;")
        self.card_layout = QVBoxLayout(self.card_container)
        self.card_layout.setContentsMargins(8, 8, 8, 8)
        self.card_layout.setSpacing(6)
        self.card_layout.addStretch()

        self.scroll_area.setWidget(self.card_container)
        root.addWidget(self.scroll_area, 1)

        # ---- 空状态（覆盖在卡片区域上，有数据时隐藏） ----
        self.empty_label = QLabel()
        self.empty_label.setText("No clipboard history yet.\n\n"
                                 "Copy some text or an image to get started.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(
            "color: #BDBDBD; font-size: 13px; background-color: #FAFAFA;"
        )
        self.empty_label.hide()

        # ---- Toast 提示（底部叠加） ----
        self.toast = QLabel(self)
        self.toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.toast.setStyleSheet("""
            QLabel {
                background-color: #424242; color: #FFFFFF;
                border-radius: 4px; padding: 8px 16px;
                font-size: 12px;
            }
        """)
        self.toast.setFixedHeight(36)
        self.toast.hide()

    def _create_toolbar(self) -> QHBoxLayout:
        """创建顶部搜索栏和设置按钮。"""
        layout = QHBoxLayout()
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search clipboard history...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E0E0E0; border-radius: 4px;
                padding: 0 8px; font-size: 12px; color: #333333;
                background-color: #FFFFFF;
            }
            QLineEdit:focus {
                border: 1.5px solid #5C6BC0;
            }
        """)
        self.search_input.textChanged.connect(self._on_search)
        layout.addWidget(self.search_input, 1)

        # 设置按钮
        settings_btn = QPushButton()
        settings_btn.setText("⚙")  # ⚙
        settings_btn.setFixedSize(36, 36)
        settings_btn.setToolTip("Settings")
        settings_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px; border: none; color: #757575;
                background: transparent;
            }
            QPushButton:hover { color: #333333; }
        """)
        settings_btn.clicked.connect(self.settings_requested.emit)
        layout.addWidget(settings_btn)

        return layout

    # ------------------------------------------------------------------
    # 列表刷新
    # ------------------------------------------------------------------

    def refresh_list(self) -> None:
        """从数据库重新加载并渲染卡片列表。"""
        self._clear_cards()

        search = self.search_input.text().strip() if self.search_input else ""
        items = self.db.get_items(search=search)

        if not items:
            self.empty_label.show()
            self.card_layout.addWidget(
                self.empty_label, 0, Qt.AlignmentFlag.AlignCenter
            )
            self.card_layout.addStretch()
            return

        self.empty_label.hide()

        # 移除上一次刷新末尾的 stretch（如果存在）
        if self.card_layout.count() > 0:
            last = self.card_layout.itemAt(self.card_layout.count() - 1)
            if last and last.spacerItem():
                self.card_layout.removeItem(last)

        for item in items:
            card = CardWidget(item)
            card.clicked.connect(self._on_card_clicked)
            card.pin_toggled.connect(self._on_pin_toggled)
            card.delete_requested.connect(self._on_delete_requested)
            self.card_layout.addWidget(card)
            self._cards.append(card)

        self.card_layout.addStretch()

    def _clear_cards(self) -> None:
        """移除所有卡片组件。"""
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()

        # 移除 stretch
        while self.card_layout.count() > 0:
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

    # ------------------------------------------------------------------
    # 搜索
    # ------------------------------------------------------------------

    def _on_search(self, text: str) -> None:
        """搜索框文字变化 → 实时刷新列表。"""
        self.refresh_list()

    # ------------------------------------------------------------------
    # 卡片交互
    # ------------------------------------------------------------------

    def _on_card_clicked(self, item: dict) -> None:
        """点击卡片 → 复制内容到系统剪贴板。"""
        try:
            if item["content_type"] == "text":
                self._copy_text(item["text_content"])
            else:
                self._copy_image(item["image_path"])
            self._show_toast("Copied to clipboard")
        except Exception as e:
            self._show_toast(f"Copy failed: {e}")

    def _copy_text(self, text: str) -> None:
        """将文字写入 Windows 剪贴板。"""
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
        win32clipboard.CloseClipboard()

    def _copy_image(self, image_path: str) -> None:
        """将图片文件写入 Windows 剪贴板。

        使用 Pillow 读取图片 → 转换为 DIB 格式 → 写入剪贴板。
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")

        img = Image.open(image_path)
        # 转换为位图并写入剪贴板
        from io import BytesIO

        output = BytesIO()
        img.convert("RGB").save(output, format="BMP")
        data = output.getvalue()[14:]  # 跳过 BMP 文件头（14 字节）

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()

    def _on_pin_toggled(self, item_id: int) -> None:
        """切换置顶状态。"""
        self.db.toggle_pin(item_id)
        self.refresh_list()

    def _on_delete_requested(self, item_id: int) -> None:
        """删除确认 → 删除记录。"""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this item?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        img_path = self.db.delete_item(item_id)
        if img_path and os.path.exists(img_path):
            try:
                os.remove(img_path)
            except OSError:
                pass
        self.refresh_list()

    # ------------------------------------------------------------------
    # Toast
    # ------------------------------------------------------------------

    def _show_toast(self, message: str) -> None:
        """在窗口底部显示短暂提示。"""
        self.toast.setText(message)
        self.toast.adjustSize()
        w = self.toast.width() + 32
        self.toast.setFixedWidth(w)
        x = (self.width() - w) // 2
        y = self.height() - 56
        self.toast.move(x, y)
        self.toast.show()
        self.toast.raise_()

        if self._toast_timer:
            self._toast_timer.stop()
        self._toast_timer = QTimer(self)
        self._toast_timer.setSingleShot(True)
        self._toast_timer.timeout.connect(self.toast.hide)
        self._toast_timer.start(1500)

    def resizeEvent(self, event) -> None:
        """窗口大小变化时重定位 toast。"""
        super().resizeEvent(event)
        if self.toast.isVisible():
            x = (self.width() - self.toast.width()) // 2
            y = self.height() - 56
            self.toast.move(x, y)
