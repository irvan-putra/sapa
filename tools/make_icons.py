#!/usr/bin/env python3
"""Launcher icon generator: one picture plus the shared version badge.

Deterministic. Same version in, same PNGs out. Inputs are pinned: Pillow
PILLOW_PIN and DejaVu Sans Bold with sha256 FONT_SHA256. The script fails
instead of falling back to another font or Pillow version, because a
different rasterizer or font changes the pixels.
    pip install pillow==12.3.0   (fonts-dejavu-core provides the font)

Badge: numbers only, a full-width strip across the bottom 24% of the icon.
Picture safety: every picture pixel is checked to lie inside the circle that
touches the icon edges (shrunk by a margin), so round launcher masks do not
clip it; the version text is checked the same way.
"""
import glob, hashlib, json, math, os, re, sys
import PIL
from PIL import Image, ImageChops, ImageDraw, ImageFont

PILLOW_PIN = "12.3.0"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SHA256 = "d1c3ff99f1e1ce1827a33efd4dad81f40babda06bff9e43bd7591c86662a287b"
DENSITIES = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
S = 768
STRIP_TOP = 0.76      # strip covers 76%..100% of the icon height
TEXT_SIZE = 0.115     # numeral size, fraction of icon size
SAFE_R = 0.485        # picture and text must stay inside this radius (fraction)

if PIL.__version__ != PILLOW_PIN:
    sys.exit("Pillow %s required, found %s" % (PILLOW_PIN, PIL.__version__))


def font(px):
    if not os.path.exists(FONT_PATH):
        sys.exit("missing font " + FONT_PATH)
    if hashlib.sha256(open(FONT_PATH, "rb").read()).hexdigest() != FONT_SHA256:
        sys.exit("unexpected font file " + FONT_PATH)
    return ImageFont.truetype(FONT_PATH, px)


def circle_mask(size, r=SAFE_R):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse([size * (.5 - r), size * (.5 - r), size * (.5 + r), size * (.5 + r)], fill=255)
    return m


def assert_inside_circle(layer, what, size=S, r=SAFE_R):
    alpha = layer.getchannel("A").point(lambda v: 255 if v > 8 else 0)
    outside = ImageChops.multiply(alpha, ImageChops.invert(circle_mask(size, r)))
    box = outside.getbbox()
    if box:
        sys.exit("%s leaves the round-mask safe circle at %s" % (what, box))


def new_layer(size=S):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def sparkle(d, cx, cy, r, fill, size=S):
    pts = []
    for i in range(96):
        t = i * 2 * math.pi / 96
        pts.append((cx * size + r * size * math.cos(t) ** 3, cy * size + r * size * math.sin(t) ** 3))
    d.polygon(pts, fill=fill)


def rrect(d, box, radius, fill, size=S):
    d.rounded_rectangle([c * size for c in box], radius=radius * size, fill=fill)


def compose(bg, art, version, strip, text, rounded=None, size=S, circle_check=True):
    """Background, then the picture layer, then the badge strip."""
    if circle_check:
        assert_inside_circle(art, "picture", size)
    base = Image.new("RGBA", (size, size), bg) if bg else Image.new("RGBA", (size, size), (0, 0, 0, 0))
    base.alpha_composite(art)
    d = ImageDraw.Draw(base)
    y0 = int(size * STRIP_TOP)
    d.rectangle([0, y0, size, size], fill=strip)
    tl, td = new_layer(size)
    f = font(int(size * TEXT_SIZE))
    td.text((size / 2, (y0 + size) / 2), version, font=f, fill=text, anchor="mm")
    if circle_check:
        assert_inside_circle(tl, "version text", size)
    base.alpha_composite(tl)
    if rounded:
        m = Image.new("L", (size, size), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, size - 1, size - 1], radius=rounded * size, fill=255)
        base.putalpha(ImageChops.multiply(base.getchannel("A"), m))
    return base


def parse_version(argv, fallback=None):
    v = argv[1] if len(argv) > 1 else fallback
    if not v or not re.fullmatch(r"\d+\.\d+\.\d+", v):
        sys.exit("version must be X.Y.Z")
    return v


def write_densities(img, res_dir, name="ic_launcher.png"):
    """Write the single 192px family drawable, without density variants."""
    out = os.path.join(res_dir, "drawable")
    os.makedirs(out, exist_ok=True)
    img.resize((192, 192), Image.LANCZOS).save(os.path.join(out, name), optimize=True)


BG = (234, 242, 251, 255)
BAND, TEXT = (20, 33, 61, 255), (255, 255, 255, 255)


def _fit(img, size, frac, cy):
    w, h = img.size
    k = size * frac / max(w, h)
    r = img.resize((max(1, int(w * k)), max(1, int(h * k))), Image.LANCZOS)
    c = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    c.paste(r, ((size - r.width) // 2, int(size * cy - r.height / 2)), r)
    return c


def legacy(version, sticker):
    return compose(BG, _fit(sticker, S, .52, .38), version, BAND, TEXT, rounded=.2)


def foreground(version, sticker, size=432):
    """Adaptive foreground. The launcher shows the middle two thirds (the
    visible square, 72..360 of 432). The picture and the number sit inside the
    circle of that area, and the same full-width bottom strip as the legacy icon
    covers the bottom 24% of the visible area (and bleeds past it, so every mask
    shape shows a strip, not a floating pill)."""
    v0, vs = size / 6.0, size * 2 / 3.0       # visible square origin and side (72, 288)
    art = _fit(sticker, size, .52 * vs / size, (v0 + .38 * vs) / size)
    assert_inside_circle(art, "sticker", size, r=.333)
    tl, td = new_layer(size)
    top = v0 + STRIP_TOP * vs
    td.text((size / 2, (top + v0 + vs) / 2), version, font=font(int(vs * TEXT_SIZE)), fill=TEXT, anchor="mm")
    assert_inside_circle(tl, "version text", size, r=.333)
    out = art
    ImageDraw.Draw(out).rectangle([0, top, size, size], fill=BAND)
    out.alpha_composite(tl)
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, ".."))
    gradle = open(os.path.join(root, "app/build.gradle")).read()
    version = parse_version(sys.argv, re.search(r'versionName\s+"([^"]+)"', gradle).group(1))
    sticker = Image.open(os.path.join(here, "assets", "sapa-sticker.png")).convert("RGBA")
    sticker = sticker.crop(sticker.getbbox())
    res = os.path.join(root, "app/src/main/res")
    write_densities(legacy(version, sticker), res)
    files = [os.path.join(res, "drawable", "ic_launcher.png")]
    manifest = {"version": version,
                "sha256": {os.path.relpath(p, root): hashlib.sha256(open(p, "rb").read()).hexdigest() for p in files}}
    with open(os.path.join(here, "icon-manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("wrote icons and manifest for", version)


if __name__ == "__main__":
    main()
