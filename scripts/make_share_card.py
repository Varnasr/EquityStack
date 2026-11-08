#!/usr/bin/env python3
"""Draws the 1200x630 link-preview card, assets/share-card.jpg.

Run it after changing the title, line or colours below:

    python3 scripts/make_share_card.py

The words are copied from the page's own meta description, so change them there
first. Needs Pillow. Fonts are Inter (SIL Open Font License, see
fonts/OFL-Inter.txt), subset and kept beside this script. Style follows the
OpenStacks house style: 2px rules, no shadows, no rounded corners, saffron as
the single accent. Text colours are measured against what they sit on and the
script stops below 4.5:1.
"""
import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "assets" / "share-card.jpg"

TITLE = 'EquityStack'
SUBTITLE = None        # optional second line under the title, or None
LINE = 'Python for distributional analysis and design-based survey estimation in development research.'
LABEL = 'Part of the OpenStacks family'              # small label, top left
ADDRESS = 'varnasr.github.io/EquityStack/'
BAND = '#b23a2a'                # colour of the bottom band

BLACK, WHITE, SAFFRON, ASH = "#0d0d0f", "#f6f2ea", "#f2a541", "#d8d3c8"
S = 2                        # draw at 2x, then reduce, for smooth edges
W, H = 1200, 630


def lum(c):
    c = c.lstrip("#")
    ch = [int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def ratio(a, b):
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


for ink, ground, what in [(WHITE, BLACK, "title"), (SAFFRON, BLACK, "subtitle and label"),
                          (ASH, BLACK, "line"), (WHITE, BAND, "address")]:
    assert ratio(ink, ground) >= 4.5, f"{what}: {ratio(ink, ground):.2f}:1 is below 4.5:1"


def font(name, px):
    return ImageFont.truetype(str(HERE / "fonts" / name), px * S)


def width(d, text, f, track=0):
    return d.textlength(text, font=f) + track * S * max(len(text) - 1, 0)


def spaced(d, xy, text, f, fill, track):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += d.textlength(ch, font=f) + track * S


def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if width(d, t, f) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def render():
    im = Image.new("RGB", (W * S, H * S), BLACK)
    d = ImageDraw.Draw(im)
    pad, maxw = 72 * S, (W - 144) * S

    # top strip
    d.rectangle([0, 0, W * S, 76 * S], fill=BLACK)
    d.rectangle([0, 74 * S, W * S, 76 * S], fill=WHITE)
    d.rectangle([pad, 30 * S, pad + 16 * S, 46 * S], fill=SAFFRON)
    spaced(d, (pad + 32 * S, 26 * S), LABEL.upper(), font("Inter-SemiBold.otf", 22), SAFFRON, 3)

    # bottom band
    d.rectangle([0, (H - 84) * S, W * S, H * S], fill=BAND)
    d.rectangle([0, (H - 86) * S, W * S, (H - 84) * S], fill=WHITE)
    f = font("Inter-SemiBold.otf", 26)
    d.text((pad, (H - 84) * S + 26 * S), ADDRESS, font=f, fill=WHITE)

    # title: one line if it fits at 112px or more, otherwise two lines
    title = TITLE.upper()
    for px in range(150, 111, -2):
        f = font("InterDisplay-ExtraBold.otf", px)
        if width(d, title, f) <= maxw:
            tl = [title]
            break
    else:
        for px in range(120, 70, -2):
            f = font("InterDisplay-ExtraBold.otf", px)
            tl = wrap(d, title, f, maxw)
            if len(tl) <= 2 and all(width(d, x, f) <= maxw for x in tl):
                break
    lh = int(px * 0.98)
    y = 100 * S
    for ln in tl:
        d.text((pad, y), ln, font=f, fill=WHITE)
        y += lh * S
    y += 18 * S
    if SUBTITLE:
        fs = font("InterDisplay-ExtraBold.otf", 40)
        d.text((pad, y), SUBTITLE, font=fs, fill=SAFFRON)
        y += 68 * S
    else:
        d.rectangle([pad, y + 6 * S, pad + 120 * S, y + 14 * S], fill=SAFFRON)
        y += 46 * S

    # one line from the page's own description
    fl = font("Inter-Regular.otf", 38)
    for ln in wrap(d, LINE, fl, maxw - 40 * S):
        d.text((pad, y), ln, font=fl, fill=ASH)
        y += 52 * S
    assert y <= (H - 92) * S, f"text runs into the bottom band ({y // S}px)"
    return im.resize((W, H), Image.LANCZOS)


def jpeg():
    b = io.BytesIO()
    render().save(b, "JPEG", quality=90, optimize=True, subsampling=0)
    return b.getvalue()


if __name__ == "__main__":
    data = jpeg()
    assert len(data) <= 250_000, f"{len(data)} bytes is over the 250 KB limit"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(data)
    print(f"wrote {OUT} ({len(data)} bytes, {W}x{H})")
