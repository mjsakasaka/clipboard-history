"""全局热键模块。

使用 pynput 在后台线程中监听全局快捷键，
触发时通过 Qt Signal 通知主线程。
"""

import threading

from PySide6.QtCore import QObject, Signal
from pynput.keyboard import GlobalHotKeys, Key, KeyCode


class HotkeyManager(QObject):
    """全局热键管理器。

    在独立线程中运行 pynput 监听，支持动态注销和重新注册。

    Signals:
        activated: 热键被按下时触发。
    """

    activated = Signal()

    # pynput 特殊键名映射（从 Qt KeySequence 格式转换）
    _KEY_MAP = {
        "Ctrl": Key.ctrl,
        "Shift": Key.shift,
        "Alt": Key.alt,
        "Win": Key.cmd,
        "Meta": Key.cmd,
    }

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._listener: GlobalHotKeys | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    # ------------------------------------------------------------------
    # 公开接口
    # ------------------------------------------------------------------

    def register(self, combo: str) -> None:
        """注册全局热键。

        Args:
            combo: 快捷键字符串，如 "Ctrl+Shift+V"。
        """
        self.unregister()

        keys = self._parse_combo(combo)
        if not keys:
            print(f"[WARN] Invalid hotkey combo: {combo}")
            return

        self._running = True
        combo_pynput = "+".join(self._to_pynput_name(k) for k in keys)

        def on_activate():
            self.activated.emit()

        self._listener = GlobalHotKeys({combo_pynput: on_activate})
        self._thread = threading.Thread(target=self._run_listener, daemon=True)
        self._thread.start()

    def unregister(self) -> None:
        """注销当前热键并停止监听线程。"""
        self._running = False
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)
            self._thread = None

    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _run_listener(self) -> None:
        """在后台线程中运行 pynput 监听器。"""
        try:
            with self._listener as listener:
                listener.join()
        except Exception as e:
            if self._running:
                print(f"[WARN] Hotkey listener error: {e}")

    @classmethod
    def _parse_combo(cls, combo: str) -> list[str]:
        """解析快捷键字符串为按键列表。

        "Ctrl+Shift+V" → ["Ctrl", "Shift", "V"]
        """
        return [part.strip() for part in combo.split("+") if part.strip()]

    @classmethod
    def _to_pynput_name(cls, key: str) -> str:
        """将按键名转换为 pynput 需要的格式。

        修饰键如 Ctrl → <ctrl>，普通键如 V → v。
        """
        if key in cls._KEY_MAP:
            return f"<{key.lower()}>"
        return key.lower()
