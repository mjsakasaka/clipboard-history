# 发布流程指南

软件发布的标准流程，按顺序执行。

---

## 1. README.md — 项目说明书

GitHub 仓库的首页文档，包含：
- 项目名称和简介
- 功能列表（截图可选）
- 安装方法（依赖安装 + 打包方法）
- 使用方法
- 技术栈
- 许可证信息

**文件位置：** `README.md`（项目根目录）

---

## 2. LICENSE — 开源许可证

为项目添加许可证文件。推荐：
- **MIT License** — 宽松，允许他人自由使用、修改、分发。适合个人工具项目。
- **GPLv3** — 强制衍生项目也必须开源。

**文件位置：** `LICENSE`（项目根目录）

---

## 3. Git 提交 & 推送

将发布相关的文件提交到 Git，并推送到 GitHub：

```bash
git add .
git commit -m "docs: add README, LICENSE, and release guide"
git push origin main
```

---

## 4. GitHub Release — 发布打包文件

在 GitHub 上创建 Release，附带打包好的 `.exe` 文件：

1. 运行 `build.bat`，生成 `dist/ClipboardHistory/` 文件夹和 `dist/ClipboardHistory.zip`
2. 在 GitHub 仓库页面点击 **Releases → Create a new release**
3. 填写：
   - **Tag version:** `v1.0.0`
   - **Release title:** `v1.0.0 — First Release`
   - **Description:** 简要描述本版本功能
4. 将 `dist/ClipboardHistory.zip` 拖入附件区域
5. 点击 **Publish release**

> 用户下载 zip 解压后得到 `ClipboardHistory/` 文件夹，内含 .exe 和 data/ 目录，结构整洁。

### Release 描述模板

```markdown
## Features

- 自动记录剪贴板文字和图片
- 时间降序卡片展示
- 搜索、置顶、删除
- 可配置保存天数（1/3/5 天）和最大条数
- 全局快捷键快速唤起
- 系统托盘常驻运行

## Installation

1. 下载 `ClipboardHistory.zip`
2. 解压到任意位置（如桌面）
3. 进入 `ClipboardHistory/` 文件夹，双击 `ClipboardHistory.exe` 运行

所有数据（数据库、图片）存放在 exe 同级的 `data/` 文件夹中，整体结构整洁。

## Notes

- 仅支持 Windows 10/11
- 如被杀毒软件拦截，请手动放行（PyInstaller 打包的 .exe 偶尔会触发误报）
```

---

## 5. 最终检查清单

提交前逐项确认：

| # | 检查项 | ✓ |
|---|--------|---|
| 1 | 所有 52 个测试通过 | ☐ |
| 2 | `python src/main.py` 能正常启动 | ☐ |
| 3 | 托盘图标正常显示 | ☐ |
| 4 | 复制文字 → 卡片出现 → 点击可粘贴 | ☐ |
| 5 | 复制图片 → 卡片出现 → 点击可粘贴 | ☐ |
| 6 | 搜索、置顶、删除功能正常 | ☐ |
| 7 | 设置面板各项可修改并保存 | ☐ |
| 8 | 全局快捷键唤起窗口（需手动测试） | ☐ |
| 9 | `build.bat` 打包成功 | ☐ |
| 10 | 生成的 .exe 在无 Python 环境下可运行 | ☐ |
| 11 | README.md 内容完整 | ☐ |
| 12 | LICENSE 文件存在 | ☐ |
| 13 | `.gitignore` 排除了 data/、dist/、build/ | ☐ |

---

## 后续迭代方向（可选）

- 添加系统开机自启（注册表写入）
- 支持更多图片格式
- 导出历史记录
- 多语言支持
- 深色模式
