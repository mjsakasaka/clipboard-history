"""剪贴板后台监控模块。

每 500ms 轮询 Windows 剪贴板，检测文字和图片变化，
通过内容哈希去重后写入数据库。
"""

import hashlib
import io
import os
from datetime import datetime

from PySide6.QtCore import QThread, Signal
from PIL import Image, ImageGrab

import win32clipboard


class ClipboardMonitor(QThread):
    """后台线程，持续监控剪贴板并记录新内容。

    Signals:
        new_item(dict): 新增记录时发射，携带记录字典。
    """

    new_item = Signal(dict)

    # 轮询间隔（毫秒）
    POLL_INTERVAL = 500

    def __init__(self, db, image_dir: str = "data/images"):
        """
        Args:
            db: Database 实例。
            image_dir: 图片文件存储目录。
        """
        super().__init__()
        self.db = db
        self.image_dir = image_dir
        self._last_hash: str | None = None
        self._running = False
        self._paused = False

        os.makedirs(image_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    def run(self) -> None:
        """线程主循环（由 QThread.start() 自动调用）。"""
        self._running = True
        while self._running:
            if not self._paused:
                try:
                    self._check_clipboard()
                except Exception as e:
                    print(f"[WARN] 剪贴板检查异常: {e}")
            self.msleep(self.POLL_INTERVAL)

    def stop_monitoring(self) -> None:
        """停止监控循环。"""
        self._running = False

    def pause_monitoring(self) -> None:
        """暂停记录（线程保持运行）。"""
        self._paused = True

    def resume_monitoring(self) -> None:
        """恢复记录。"""
        self._paused = False

    @property
    def is_paused(self) -> bool:
        return self._paused

    # ------------------------------------------------------------------
    # 剪贴板读取
    # ------------------------------------------------------------------

    def _check_clipboard(self) -> None:
        """读取剪贴板，去重后写入数据库。"""
        content = self._read_clipboard()
        if content is None:
            return

        content_hash = self._compute_hash(content)
        if content_hash == self._last_hash:
            return  # 与上次内容相同，跳过

        self._last_hash = content_hash
        item = self._save_content(content)
        if item:
            self.new_item.emit(item)

    def _read_clipboard(self) -> dict | None:
        """读取当前剪贴板内容。

        Returns:
            {'type': 'text', 'text': ...} 或
            {'type': 'image', 'image': <PIL.Image>} 或
            None（无法识别或无内容）。
        """
        # 优先尝试读取图片
        try:
            grabbed = ImageGrab.grabclipboard()
            if isinstance(grabbed, Image.Image):
                return {"type": "image", "image": grabbed}
            # grabbed 是文件路径列表或 None，说明不是图片，继续尝试文字
        except Exception:
            pass

        # 尝试读取文字
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(
                win32clipboard.CF_UNICODETEXT
            ):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                win32clipboard.CloseClipboard()
                if data and data.strip():
                    return {"type": "text", "text": data.strip()}
            win32clipboard.CloseClipboard()
        except Exception:
            # 确保剪贴板被关闭
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass

        return None

    # ------------------------------------------------------------------
    # 去重 & 存储
    # ------------------------------------------------------------------

    def _compute_hash(self, content: dict) -> str:
        """计算内容哈希（MD5），用于连续相同内容的去重。"""
        if content["type"] == "text":
            raw = content["text"].encode("utf-8")
        else:
            # 将图片编码为 PNG 字节再哈希，比 tobytes() 更高效
            buf = io.BytesIO()
            content["image"].save(buf, format="PNG")
            raw = buf.getvalue()
        return hashlib.md5(raw).hexdigest()

    def _save_content(self, content: dict) -> dict:
        """将内容写入数据库，图片则额外保存到磁盘。

        Returns:
            新记录的字典，供 new_item 信号使用。
        """
        if content["type"] == "text":
            item_id = self.db.add_item("text", text_content=content["text"])
            return {
                "id": item_id,
                "content_type": "text",
                "text_content": content["text"],
                "image_path": None,
                "pinned": 0,
            }
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{timestamp}.png"
            filepath = os.path.join(self.image_dir, filename)
            content["image"].save(filepath, "PNG")

            item_id = self.db.add_item("image", image_path=filepath)
            return {
                "id": item_id,
                "content_type": "image",
                "text_content": None,
                "image_path": filepath,
                "pinned": 0,
            }
