"""生成应用托盘图标。

用 Pillow 绘制一个简洁的剪贴板图标。
"""

from PIL import Image, ImageDraw


def create_icon(path: str = "assets/icon.png", size: int = 64) -> None:
    """生成剪贴板图标并保存为 PNG。

    Args:
        path: 输出路径。
        size: 图标尺寸（正方形）。
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    s = size  # 缩写

    # 剪贴板底板（深灰圆角矩形）
    board_color = (100, 105, 115)
    draw.rounded_rectangle(
        [s * 0.12, s * 0.08, s * 0.88, s * 0.94],
        radius=s * 0.1,
        fill=board_color,
    )

    # 纸张区域（白色）
    paper_color = (248, 248, 248)
    draw.rounded_rectangle(
        [s * 0.20, s * 0.16, s * 0.80, s * 0.88],
        radius=s * 0.05,
        fill=paper_color,
    )

    # 顶部夹子
    clip_color = (130, 135, 145)
    draw.rounded_rectangle(
        [s * 0.34, s * 0.02, s * 0.66, s * 0.16],
        radius=s * 0.06,
        fill=clip_color,
    )

    # 文字横线（灰色）
    line_color = (200, 200, 205)
    lx1, lx2 = s * 0.30, s * 0.70
    draw.rounded_rectangle([lx1, s * 0.28, lx2, s * 0.34], radius=2, fill=line_color)
    draw.rounded_rectangle([lx1, s * 0.42, lx2, s * 0.48], radius=2, fill=line_color)
    draw.rounded_rectangle([lx1, s * 0.56, s * 0.58, s * 0.62], radius=2, fill=line_color)

    img.save(path, "PNG")
    print(f"Icon saved to {path}")


if __name__ == "__main__":
    create_icon()
