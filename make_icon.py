"""
One-off: draws a simple camera glyph and saves it as a multi-size .ico for
the desktop shortcut. Not part of the app's runtime — run once, then the
.ico file is what matters.
"""
from PIL import Image, ImageDraw

SIZES = [16, 32, 48, 256]
BG = (30, 30, 30, 255)
BODY = (240, 200, 60, 255)
LENS_OUTER = (30, 30, 30, 255)
LENS_INNER = (80, 160, 220, 255)


def draw_camera(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = size * 0.08

    # rounded background square
    d.rounded_rectangle([pad, pad, size - pad, size - pad], radius=size * 0.18, fill=BG)

    # camera body
    body_top = size * 0.38
    d.rounded_rectangle(
        [size * 0.14, body_top, size * 0.86, size * 0.82], radius=size * 0.06, fill=BODY
    )
    # viewfinder bump
    d.rectangle([size * 0.35, size * 0.28, size * 0.65, body_top + 2], fill=BODY)

    # lens
    center = (size * 0.5, size * 0.6)
    r_outer = size * 0.16
    r_inner = size * 0.10
    d.ellipse(
        [center[0] - r_outer, center[1] - r_outer, center[0] + r_outer, center[1] + r_outer],
        fill=LENS_OUTER,
    )
    d.ellipse(
        [center[0] - r_inner, center[1] - r_inner, center[0] + r_inner, center[1] + r_inner],
        fill=LENS_INNER,
    )
    return img


if __name__ == "__main__":
    base = draw_camera(256)
    base.save("assets/icon.ico", sizes=[(s, s) for s in SIZES])
    print("wrote assets/icon.ico")
