# 技术规范

## 技术栈

| 层级 | 技术 | 版本要求 |
|------|------|----------|
| 语言 | Python | 3.10+ |
| GUI 框架 | PySide6 | ≥6.5 |
| Windows API | pywin32 | ≥306 |
| 全局热键 | pynput | ≥1.7 |
| 图片处理 | Pillow | ≥10.0 |
| 数据库 | sqlite3 | Python 内置 |
| 打包工具 | PyInstaller | ≥6.0 |

## 环境安装

```bash
pip install PySide6 pywin32 pynput Pillow pyinstaller
```

或使用 requirements.txt：

```bash
pip install -r requirements.txt
```

---

## 项目结构

```
copy_history/
├── docs/                       # 项目标准文档
│   ├── requirements.md         # 开发需求
│   ├── tech-spec.md            # 本文件，技术规范
│   ├── design-spec.md          # UI/UX 设计规范
│   ├── execution-plan.md       # 分阶段执行计划
│   └── dev-standards.md        # 开发规范
├── dev-logs/                   # 开发日志
│   └── YYYY-MM-DD.md
├── src/                        # 源代码
│   ├── main.py                 # 程序入口
│   ├── config.py               # 配置管理
│   ├── database.py             # SQLite 数据库操作
│   ├── clipboard_monitor.py    # 剪贴板后台监控
│   ├── cleanup.py              # 过期/超量清理
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py      # 主窗口
│   │   ├── card_widget.py      # 卡片组件
│   │   ├── settings_dialog.py  # 设置对话框
│   │   └── tray_icon.py        # 系统托盘
│   └── utils/
│       ├── __init__.py
│       └── hotkey.py           # 全局热键
├── assets/
│   └── icon.png                # 应用图标
├── data/                       # 运行时数据
│   ├── clipboard.db            # SQLite 数据库文件
│   └── images/                 # 图片存储
├── requirements.txt
└── build.bat
```

---

## 数据库设计

### 数据库文件

- 位置：`data/clipboard.db`
- 引擎：SQLite 3
- 编码：UTF-8

### 表结构

#### `clipboard_items` — 剪贴板记录

```sql
CREATE TABLE IF NOT EXISTS clipboard_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    content_type TEXT NOT NULL CHECK(content_type IN ('text', 'image')),
    text_content TEXT,
    image_path  TEXT,
    pinned      INTEGER DEFAULT 0 CHECK(pinned IN (0, 1)),
    created_at  TIMESTAMP DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_created_at ON clipboard_items(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pinned ON clipboard_items(pinned);
```

#### `settings` — 应用设置

```sql
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

### 默认设置

```python
DEFAULT_SETTINGS = {
    "retention_days": "3",
    "max_items": "500",
    "hotkey_enabled": "true",
    "hotkey_combo": "Ctrl+Shift+V",
    "auto_start": "true",
}
```

---

## 核心模块说明

### main.py — 程序入口

- 初始化 QApplication
- 初始化数据库（Database）
- 初始化配置（Config）
- 创建系统托盘（TrayIcon）
- 启动剪贴板监控（ClipboardMonitor）
- 启动清理定时器（Cleanup）
- 可选：注册全局热键
- 进入 Qt 事件循环

### config.py — 配置管理

```python
class Config:
    def get(key: str) -> str
    def set(key: str, value: str)
    def get_int(key: str) -> int
    def get_bool(key: str) -> bool
    def reset_defaults()
```

配置存储在 `settings` 表中，通过 Database 访问。

### database.py — 数据操作

```python
class Database:
    def __init__(db_path: str)
    def add_item(content_type, text_content, image_path) -> int
    def get_items(search="", limit=500, offset=0) -> list[dict]
    def toggle_pin(item_id: int)
    def delete_item(item_id: int)
    def get_expired_ids(retention_days: int) -> list[int]
    def delete_oldest_unpinned(keep_count: int)
    def get_count() -> int
```

### clipboard_monitor.py — 剪贴板监控

- 使用 `win32clipboard` 读取剪贴板
- 轮询间隔：500ms
- 计算内容哈希去重
- 文字：存储原文（去首尾空白后判断是否为空）
- 图片：保存到 `data/images/{timestamp}.png`，存储路径
- 信号通知 UI 刷新（使用 Qt Signal）

### cleanup.py — 清理任务

- 使用 QTimer，每小时触发一次
- 删除过期记录（按 retention_days）
- 删除超量记录（按 max_items）
- 删除时同时清理图片文件

### ui/tray_icon.py — 系统托盘

- 使用 QSystemTrayIcon
- 图标：assets/icon.png
- 右键菜单：打开 / 设置 / 暂停恢复 / 退出
- 左键双击：打开主窗口

### ui/main_window.py — 主窗口

- QWidget 窗口
- 顶部：搜索栏（QLineEdit）+ 设置按钮
- 主体：QScrollArea > QVBoxLayout（卡片列表）
- 初始化时加载所有记录
- 搜索时实时过滤
- 新记录到来时（来自监控信号）刷新列表

### ui/card_widget.py — 卡片组件

- QFrame 子类
- 左侧：内容预览区
  - 文字：QLabel 显示截断文本
  - 图片：QLabel 显示缩略图（QPixmap）
- 右侧：操作按钮
  - 📌 置顶按钮（QPushButton）
  - 🗑 删除按钮（QPushButton）
- 底部：时间显示

### ui/settings_dialog.py — 设置对话框

- QDialog 子类
- 表单布局
- 保存天数：QComboBox（1/3/5）
- 最大条数：QSpinBox（100-2000, step=100）
- 启用快捷键：QCheckBox
- 快捷键录制：自定义 KeySequenceEdit 或 QKeySequenceEdit
- 开机自启：QCheckBox
- 底部：保存 / 取消按钮

### utils/hotkey.py — 全局热键

- 使用 pynput.keyboard.GlobalHotKeys
- 在后台线程运行
- 触发时通过 Qt Signal 通知主线程打开窗口
- 支持动态注册/注销

---

## 数据流

```
剪贴板变化
  │
  ▼
ClipboardMonitor (后台线程，500ms 轮询)
  │  去重判断（内容哈希）
  │
  ├── 文字 → 存入 DB (text_content)
  │
  └── 图片 → 保存到 data/images/
           → 存入 DB (image_path)
  │
  ▼
Database.add_item()
  │
  ├── 检查 max_items → 超了删除最旧未置顶
  │
  └── Qt Signal 发射新记录通知
       │
       ▼
     MainWindow 接收信号
       │
       └── 刷新卡片列表（如果窗口打开）
```

---

## 打包配置（PyInstaller）

```python
# build.spec 关键配置
app = Analysis(
    ['src/main.py'],
    datas=[('assets/', 'assets/')],
    hiddenimports=['PySide6', 'win32clipboard', 'pynput', 'PIL'],
)
```

输出：单文件 .exe，存放于 `dist/ClipboardHistory.exe`
