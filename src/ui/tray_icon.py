"""系统托盘模块。

提供系统托盘图标和右键菜单，管理后台运行时的用户交互。
"""

from PySide6.QtWidgets import (
    QSystemTrayIcon,
    QMenu,
    QWidget,
)
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Signal


class TrayIcon(QSystemTrayIcon):
    """系统托盘图标，提供右键菜单控制应用。

    Signals:
        show_window_requested: 用户请求打开主窗口。
        settings_requested: 用户请求打开设置。
        quit_requested: 用户请求退出程序。
    """

    show_window_requested = Signal()
    settings_requested = Signal()
    quit_requested = Signal()

    def __init__(
        self,
        icon_path: str = "assets/icon.png",
        parent: QWidget | None = None,
    ):
        """初始化系统托盘。

        Args:
            icon_path: 图标文件路径。找不到时使用系统默认图标。
            parent: Qt 父组件。
        """
        super().__init__(parent)

        # 加载图标，失败则降级使用系统图标
        icon = QIcon(icon_path)
        if icon.isNull():
            icon = self._fallback_icon()
        self.setIcon(icon)
        self.setToolTip("Clipboard History")

        self._menu = self._create_menu()
        self.setContextMenu(self._menu)

        # 双击托盘图标 → 打开主窗口
        self.activated.connect(self._on_activated)

    # ------------------------------------------------------------------
    # 菜单
    # ------------------------------------------------------------------

    def _create_menu(self) -> QMenu:
        """构建右键菜单。"""
        menu = QMenu()

        open_action = QAction("Open History Panel", menu)
        open_action.triggered.connect(self.show_window_requested.emit)
        menu.addAction(open_action)

        settings_action = QAction("Settings", menu)
        settings_action.triggered.connect(self.settings_requested.emit)
        menu.addAction(settings_action)

        menu.addSeparator()

        self._pause_action = QAction("Pause Monitoring", menu)
        self._pause_action.setCheckable(True)
        self._pause_action.toggled.connect(self._on_pause_toggled)
        menu.addAction(self._pause_action)

        menu.addSeparator()

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        return menu

    # ------------------------------------------------------------------
    # 暂停/恢复
    # ------------------------------------------------------------------

    @property
    def pause_action(self) -> QAction:
        """返回暂停/恢复菜单项，供外部绑定切换逻辑。"""
        return self._pause_action

    @property
    def is_monitoring_paused(self) -> bool:
        return self._pause_action.isChecked()

    def _on_pause_toggled(self, checked: bool) -> None:
        """暂停状态切换 → 更新菜单文字和托盘提示。"""
        if checked:
            self._pause_action.setText("Resume Monitoring")
            self.setToolTip("Clipboard History (Paused)")
        else:
            self._pause_action.setText("Pause Monitoring")
            self.setToolTip("Clipboard History")

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """托盘图标被点击/双击时触发。"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window_requested.emit()

    @staticmethod
    def _fallback_icon() -> QIcon:
        """当图标文件不存在时使用的系统默认图标。"""
        from PySide6.QtWidgets import QApplication

        style = QApplication.style()
        if style:
            return style.standardIcon(
                QApplication.style().StandardPixmap.SP_FileDialogListView
            )
        return QIcon()
