# 分阶段执行计划

> 每个阶段独立推进，确认功能稳定后再进入下一阶段。
> 遇到任何问题连续失败 3 次，立即停止并报告。

---

## 阶段 0：工程搭建

**目标：** 项目骨架就绪，所有标准文档写定，开发环境可运行。

### 步骤

| # | 任务 | 产出物 |
|---|------|--------|
| 0.1 | 创建目录结构 | docs/, dev-logs/, src/, assets/, data/images/ |
| 0.2 | 编写 [requirements.md](requirements.md) | 需求文档 |
| 0.3 | 编写 [tech-spec.md](tech-spec.md) | 技术规范 |
| 0.4 | 编写 [design-spec.md](design-spec.md) | 设计规范 |
| 0.5 | 编写 [execution-plan.md](execution-plan.md) | 本文件 |
| 0.6 | 编写 [dev-standards.md](dev-standards.md) | 开发规范 |
| 0.7 | 创建 `requirements.txt` | Python 依赖清单 |
| 0.8 | 创建 `__init__.py` 文件 | 包初始化 |
| 0.9 | 验证 Python 版本和依赖安装 | 环境就绪确认 |

### 验证

```bash
python --version          # 应输出 Python 3.10+
pip install -r requirements.txt  # 所有依赖安装成功
python -c "from PySide6.QtWidgets import QApplication; print('OK')"  # 无报错
```

---

## 阶段 1：数据层

**目标：** SQLite 数据库就绪，配置管理可用，可以独立测试。

### 步骤

| # | 任务 | 产出物 |
|---|------|--------|
| 1.1 | 实现 `database.py` — Database 类 | 建表、CRUD、查询 |
| 1.2 | 实现 `config.py` — Config 类 | 读写设置 |
| 1.3 | 编写 `test_db.py` 测试脚本 | 验证数据库操作 |

### 核心接口

```python
# database.py
db = Database("data/clipboard.db")
db.add_item("text", "hello world", None)
items = db.get_items(search="hello")
db.toggle_pin(1)
db.delete_item(1)
db.get_count()
db.get_expired_ids(3)

# config.py
cfg = Config(db)
cfg.get("retention_days")  # "3"
cfg.set("retention_days", "5")
```

### 验证

```bash
python src/test_db.py  # 所有测试通过
```

---

## 阶段 2：剪贴板监控

**目标：** 后台线程能正确检测并记录文字和图片的剪贴板变化。

### 步骤

| # | 任务 | 产出物 |
|---|------|--------|
| 2.1 | 实现 `clipboard_monitor.py` | ClipboardMonitor 类 |
| 2.2 | 实现内容哈希去重 | 避免重复记录 |
| 2.3 | 集成 Database.add_item() | 新内容自动入库 |
| 2.4 | 手动功能测试 | 复制文字和图片验证 |

### 核心逻辑

```
ClipboardMonitor(QThread)
├── run()
│   ├── 每 500ms 检查剪贴板
│   ├── 获取内容的 MD5 哈希
│   ├── 与上次哈希对比
│   ├── 不同 → 存入数据库
│   └── 发射 new_item 信号
├── start_monitoring()
├── stop_monitoring()
└── new_item = Signal(dict)
```

### 验证

- 复制文字 → 查询数据库确认已记录
- 复制图片 → 检查 data/images/ 下有文件，数据库有记录
- 连续复制相同内容 → 确认只有一条记录

---

## 阶段 3：系统托盘

**目标：** 程序作为后台应用运行，托盘图标可操作。

### 步骤

| # | 任务 | 产出物 |
|---|------|--------|
| 3.1 | 准备应用图标 | assets/icon.png |
| 3.2 | 实现 `tray_icon.py` | TrayIcon 类 |
| 3.3 | 实现 `main.py` | 程序入口 |
| 3.4 | 集成监控和托盘 | 启动即运行 |

### 核心逻辑

```
main.py
├── app = QApplication([])
├── db = Database("data/clipboard.db")
├── cfg = Config(db)
├── monitor = ClipboardMonitor(db)
├── tray = TrayIcon(app, monitor, cfg)
├── monitor.start()
└── app.exec()
```

### 托盘菜单

```
┌─────────────────┐
│ 📋 打开历史面板   │
│ ⚙ 设置          │
│ ─────────────── │
│ ⏸ 暂停监控      │
│ ❌ 退出          │
└─────────────────┘
```

### 验证

```bash
python src/main.py
```
- 托盘出现图标 ✓
- 右键菜单可用 ✓
- 暂停/恢复监控正常 ✓
- 退出后进程结束 ✓

---

## 阶段 4：主窗口 UI

**目标：** 用户能通过托盘打开主窗口，看到卡片列表。

### 步骤

| # | 任务 | 产出物 |
|---|------|--------|
| 4.1 | 实现 `card_widget.py` | CardWidget 类 |
| 4.2 | 实现 `main_window.py` | MainWindow 类 |
| 4.3 | 连接信号：新条目 → 刷新列表 | 实时更新 |

### 主窗口组件树

```
MainWindow(QWidget)
├── QVBoxLayout
│   ├── 搜索栏 (QHBoxLayout)
│   │   ├── QLineEdit (搜索框)
│   │   └── QPushButton (设置)
│   └── QScrollArea
│       └── QVBoxLayout (卡片容器)
│           ├── CardWidget (置顶)
│           ├── CardWidget
│           └── CardWidget ...
└── Toast (QLabel, 底部叠加)
```

### 验证

- 打开主窗口 → 看到已有记录 ✓
- 新复制内容 → 卡片实时出现 ✓
- 卡片按置顶优先 + 时间降序排列 ✓
- 空数据库时 → 显示空状态 ✓

---

## 阶段 5：交互功能

**目标：** 所有卡片操作可用。

### 步骤

| # | 任务 | 产出物 |
|---|------|--------|
| 5.1 | 点击卡片 → 复制到剪贴板 | 文字和图片粘贴 |
| 5.2 | 置顶/取消置顶 | 📌 按钮交互 |
| 5.3 | 删除记录 | 🗑 按钮 + 确认框 |
| 5.4 | 实时搜索 | 搜索框过滤 |
| 5.5 | Toast 提示 | "已复制"反馈 |

### 验证

- 点击文字卡片 → 粘贴到记事本 → 内容正确 ✓
- 点击图片卡片 → 粘贴到画图 → 图片正确 ✓
- 置顶卡片 → 移到最前，图标变色 ✓
- 删除 → 确认框弹出 → 确认后消失 ✓
- 搜索 "hello" → 只显示含 hello 的卡片 ✓

---

## 阶段 6：设置 + 热键

**目标：** 用户可自定义软件行为，可选全局快捷键。

### 步骤

| # | 任务 | 产出物 |
|---|------|--------|
| 6.1 | 实现 `settings_dialog.py` | 设置对话框 |
| 6.2 | 实现 `hotkey.py` | 全局热键注册 |
| 6.3 | 设置与 Config 联动 | 修改即时生效 |

### 验证

- 托盘菜单 → 设置 → 打开对话框 ✓
- 修改保存天数 → 设置写入数据库 ✓
- 修改最大条数 → 设置写入数据库 ✓
- 修改快捷键 → 新快捷键生效 ✓
- 禁用快捷键 → 按键无效 ✓

---

## 阶段 7：清理 + 收尾

**目标：** 自动清理正常运行，所有功能完善。

### 步骤

| # | 任务 | 产出物 |
|---|------|--------|
| 7.1 | 实现 `cleanup.py` | Cleanup 定时任务 |
| 7.2 | 完善托盘状态（暂停时图标变化） | 视觉反馈 |
| 7.3 | 异常处理加固 | 崩溃保护 |
| 7.4 | 全面功能测试 | 逐项验证 |

### 验证

- 运行 1 小时后确认清理触发 ✓
- 暂停监控时，复制不记录 ✓
- 异常复制内容不导致崩溃 ✓

---

## 阶段 8：打包

**目标：** 生成可分发的 .exe 文件。

### 步骤

| # | 任务 | 产出物 |
|---|------|--------|
| 8.1 | 编写 PyInstaller spec | build.spec |
| 8.2 | 编写 `build.bat` | 一键打包脚本 |
| 8.3 | 打包测试 | ClipboardHistory.exe |
| 8.4 | 在干净环境测试 | 无 Python 的电脑上可运行 |

### 验证

```bash
build.bat                    # 打包成功
dist/ClipboardHistory.exe    # 双击可运行
```

- 无 Python 环境的 Windows 电脑上正常运行 ✓
- 托盘图标正常显示 ✓
- 所有功能可用 ✓
