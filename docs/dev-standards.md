# 开发规范

## 命名规范

### 文件

| 类型 | 规范 | 示例 |
|------|------|------|
| Python 模块 | 小写下划线 | `clipboard_monitor.py` |
| 包目录 | 小写 | `ui/`, `utils/` |
| 文档 | 小写连字符 | `tech-spec.md` |
| 资源文件 | 小写 + 扩展名 | `icon.png` |

### 代码

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `ClipboardMonitor`, `MainWindow` |
| 函数/方法 | snake_case | `get_items()`, `toggle_pin()` |
| 变量 | snake_case | `current_hash`, `item_count` |
| 常量 | UPPER_SNAKE | `POLL_INTERVAL`, `MAX_PREVIEW_LEN` |
| 私有方法 | `_` 前缀 | `_check_clipboard()`, `_cleanup_expired()` |
| Qt 信号 | snake_case | `new_item = Signal(dict)` |

---

## 代码风格

### 基本规则

- 编码：UTF-8
- 缩进：4 空格（不用 Tab）
- 行宽：不超过 100 字符
- import 分组：标准库 → 第三方 → 本地模块，每组间空一行

```python
# 正确示例
import os
import hashlib
from datetime import datetime

from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt

from src.database import Database
from src.config import Config
```

### 注释

- 每个类和公共方法必须写 docstring
- 复杂逻辑加行内注释说明"为什么"，而不是"做什么"
- 注释用中文（本项目面向中文用户）

```python
class ClipboardMonitor(QThread):
    """后台线程，每 500ms 轮询剪贴板并记录新内容。"""

    def _get_clipboard_hash(self) -> str:
        """计算当前剪贴板内容的 MD5 哈希，用于去重判断。"""
        ...
```

### 异常处理

- 剪贴板读取失败：记录日志，继续运行，不崩溃
- 数据库写入失败：记录日志，重试 1 次
- 图片保存失败：跳过该记录，不阻塞后续监控

```python
try:
    content = self._read_clipboard()
except Exception as e:
    print(f"[WARN] 读取剪贴板失败: {e}")
    return
```

---

## 提交规范

- 每个阶段完成后提交一次
- 提交信息格式：`[阶段N] 简短描述`
- 提交信息用中文

```
[阶段0] 工程搭建：创建目录和标准文档
[阶段1] 数据层：实现 database.py 和 config.py
[阶段2] 剪贴板监控：实现轮询和入库
...
```

---

## 测试规范

- 每个模块编写独立测试脚本 `test_xxx.py`
- 测试覆盖核心路径和边界情况
- 手动测试记录在当日开发日志中

### 数据库测试示例

```python
# test_db.py
def test_add_text():
    db = Database(":memory:")  # 内存数据库，不影响正式数据
    db.add_item("text", "hello", None)
    assert db.get_count() == 1

def test_add_duplicate():
    db = Database(":memory:")
    db.add_item("text", "hello", None)
    db.add_item("text", "hello", None)
    assert db.get_count() == 1  # 去重

def test_toggle_pin():
    db = Database(":memory:")
    item_id = db.add_item("text", "test", None)
    db.toggle_pin(item_id)
    items = db.get_items()
    assert items[0]["pinned"] == 1
```

---

## 开发日志规范

每天开发结束时，更新 `dev-logs/YYYY-MM-DD.md`：

```markdown
# 开发日志 — YYYY-MM-DD

## ✅ 已完成
- [阶段0] 创建了目录结构
- [阶段0] 编写了 requirements.md

## 📋 待办
- [ ] 实现 database.py
- [ ] 编写数据库测试

## ⚠️ 问题 & 解决
- PySide6 安装失败 → 使用 `pip install --user PySide6` 解决

## 📝 备注
- 图片存储路径需要确认
```
