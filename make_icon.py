from PIL import Image, ImageDraw

BG = "#1a1a1a"
KEY = "#3d3d3d"
ACCENT = "#0a84ff"
BORDER = "#252525"

SIZE = 256


def draw_keyboard(size):
    img = Image.new("RGBA", (size, size), BG)
    draw = ImageDraw.Draw(img)

    pad = size // 16
    radius = size // 8
    draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=radius, fill=BG, outline=BORDER, width=max(1, size // 64)
    )

    cols, rows = 6, 4
    margin_x = size // 6
    margin_y = size // 5
    grid_w = size - margin_x * 2
    grid_h = size - margin_y * 2
    gap = size // 40
    key_w = (grid_w - gap * (cols - 1)) // cols
    key_h = (grid_h - gap * (rows - 1)) // rows
    key_radius = max(2, size // 40)

    for r in range(rows):
        for c in range(cols):
            x0 = margin_x + c * (key_w + gap)
            y0 = margin_y + r * (key_h + gap)
            x1 = x0 + key_w
            y1 = y0 + key_h

            if r == rows - 1 and c in (2, 3):
                fill = ACCENT
            else:
                fill = KEY

            draw.rounded_rectangle(
                [x0, y0, x1, y1],
                radius=key_radius, fill=fill
            )

    return img


def main():
    sizes = [16, 24, 32, 48, 64, 128, 256]
    base = draw_keyboard(SIZE)
    base.save(
        "keyboard_icon.ico",
        format="ICO",
        sizes=[(s, s) for s in sizes]
    )
    base.save("keyboard_icon.png")
    print("已生成 keyboard_icon.ico 和 keyboard_icon.png")


if __name__ == "__main__":
    main()