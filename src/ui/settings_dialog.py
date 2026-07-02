"""设置对话框模块。

提供保存天数、最大条数、全局热键、开机自启等配置项的表单。
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QKeySequenceEdit,
    QDialogButtonBox,
    QLabel,
    QHBoxLayout,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence

from src.config import Config


class SettingsDialog(QDialog):
    """设置对话框。

    修改后点 Save 立即写入 Config 并生效。
    """

    def __init__(self, cfg: Config, parent=None):
        """
        Args:
            cfg: Config 实例。
        """
        super().__init__(parent)
        self.cfg = cfg

        self.setWindowTitle("Settings")
        self.setFixedWidth(380)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        self._build_ui()
        self._load_settings()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """构建设置表单。"""
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        # 标题
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333333;")
        root.addWidget(title)

        # 表单
        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.retention_combo = QComboBox()
        self.retention_combo.addItems(["1", "3", "5"])
        self.retention_combo.setFixedHeight(30)
        self.retention_combo.setStyleSheet(self._input_style())
        form.addRow("Retention (days):", self.retention_combo)

        self.max_items_spin = QSpinBox()
        self.max_items_spin.setRange(100, 2000)
        self.max_items_spin.setSingleStep(100)
        self.max_items_spin.setFixedHeight(30)
        self.max_items_spin.setStyleSheet(self._input_style())
        form.addRow("Max items:", self.max_items_spin)

        self.hotkey_check = QCheckBox("Enable global hotkey")
        self.hotkey_check.setStyleSheet("color: #333333;")
        form.addRow("", self.hotkey_check)

        self.hotkey_edit = QKeySequenceEdit()
        self.hotkey_edit.setFixedHeight(30)
        self.hotkey_edit.setStyleSheet(self._input_style())
        form.addRow("Shortcut:", self.hotkey_edit)

        root.addLayout(form)

        # 开机自启（暂不实现实际注册，只存配置）
        self.autostart_check = QCheckBox("Start with Windows")
        self.autostart_check.setStyleSheet("color: #333333;")
        root.addWidget(self.autostart_check)

        root.addStretch()

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        buttons.setStyleSheet("""
            QPushButton {
                padding: 6px 20px; border-radius: 3px;
                font-size: 12px;
            }
        """)
        root.addWidget(buttons)

    # ------------------------------------------------------------------
    # 加载 / 保存
    # ------------------------------------------------------------------

    def _load_settings(self) -> None:
        """从 Config 加载当前设置到表单。"""
        self.retention_combo.setCurrentText(self.cfg.get("retention_days"))

        self.max_items_spin.setValue(self.cfg.get_int("max_items"))

        enabled = self.cfg.get_bool("hotkey_enabled")
        self.hotkey_check.setChecked(enabled)
        self.hotkey_edit.setEnabled(enabled)

        combo = self.cfg.get("hotkey_combo")
        self.hotkey_edit.setKeySequence(QKeySequence(combo))

        self.autostart_check.setChecked(self.cfg.get_bool("auto_start"))

        # 快捷键开关联动
        self.hotkey_check.toggled.connect(self.hotkey_edit.setEnabled)

    def _on_save(self) -> None:
        """保存设置到 Config 并关闭对话框。"""
        self.cfg.set("retention_days", self.retention_combo.currentText())
        self.cfg.set("max_items", str(self.max_items_spin.value()))
        self.cfg.set("hotkey_enabled", "true" if self.hotkey_check.isChecked() else "false")
        self.cfg.set(
            "hotkey_combo",
            self.hotkey_edit.keySequence().toString(QKeySequence.SequenceFormat.NativeText),
        )
        self.cfg.set("auto_start", "true" if self.autostart_check.isChecked() else "false")
        self.accept()

    # ------------------------------------------------------------------
    # 样式
    # ------------------------------------------------------------------

    @staticmethod
    def _input_style() -> str:
        """统一输入控件的 QSS。"""
        return """
            QComboBox, QSpinBox, QKeySequenceEdit {
                border: 1px solid #E0E0E0;
                border-radius: 3px;
                padding: 2px 6px;
                font-size: 12px;
                color: #333333;
                background: #FFFFFF;
            }
            QComboBox:focus, QSpinBox:focus, QKeySequenceEdit:focus {
                border-color: #5C6BC0;
            }
        """
