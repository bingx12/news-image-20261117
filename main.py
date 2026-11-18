#!/usr/bin/env python3
"""THE WORLD TODAY - Tuesday, 17 November 2026: one-page front page.

Pure standard library. Draws a deterministic 1024x1024 PNG of the
day's world news to /output/entry.png (or $MAKEFUN_OUTPUT_DIR, or
./out when run locally). No network, no clock, no randomness: two
runs write byte-identical files.

Text is drawn from bitmap glyphs in font_data.py (DejaVu Sans Book +
Bold rendered at 64 px); pictures are drawn programmatically.
"""

import base64
import hashlib
import os
import struct
import sys
import zlib

import font_data

W = 1024
H = 1024

PAPER = (246, 241, 231)
INK = (26, 26, 26)
RED = (168, 32, 32)
GREY = (110, 104, 92)
RULE = (26, 26, 26)
SEA = (46, 95, 122)
SEA_DARK = (28, 66, 90)
SKY = (208, 222, 228)
SAND = (216, 198, 152)
STEEL = (96, 104, 116)
SHIP = (52, 52, 52)
WHITE = (250, 248, 243)
SUN = (224, 164, 60)

canvas = bytearray(W * H * 3)


def fill(color):
    r, g, b = color
    for i in range(0, len(canvas), 3):
        canvas[i] = r
        canvas[i + 1] = g
        canvas[i + 2] = b


def px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        canvas[i] = color[0]
        canvas[i + 1] = color[1]
        canvas[i + 2] = color[2]


def blend_px(x, y, color, cover):
    """Blend ink over the canvas; cover 0..255."""
    if cover <= 0 or not (0 <= x < W and 0 <= y < H):
        return
    i = (y * W + x) * 3
    if cover >= 255:
        canvas[i] = color[0]
        canvas[i + 1] = color[1]
        canvas[i + 2] = color[2]
        return
    inv = 255 - cover
    canvas[i] = (color[0] * cover + canvas[i] * inv) // 255
    canvas[i + 1] = (color[1] * cover + canvas[i + 1] * inv) // 255
    canvas[i + 2] = (color[2] * cover + canvas[i + 2] * inv) // 255


def rect(x0, y0, x1, y1, color):
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W, x1)
    y1 = min(H, y1)
    for y in range(y0, y1):
        base = (y * W + x0) * 3
        for x in range(x0, x1):
            i = base + (x - x0) * 3
            canvas[i] = color[0]
            canvas[i + 1] = color[1]
            canvas[i + 2] = color[2]


def hline(x0, x1, y, color, thick=1):
    rect(x0, y, x1, y + thick, color)


def vline(x, y0, y1, color, thick=1):
    rect(x, y0, x + thick, y1, color)


def line(x0, y0, x1, y1, color, thick=1):
    """Bresenham line with a square brush."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    r = thick // 2
    while True:
        rect(x0 - r, y0 - r, x0 - r + thick, y0 - r + thick, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def disc(cx, cy, rad, color):
    for y in range(cy - rad, cy + rad + 1):
        dy = y - cy
        span = int((rad * rad - dy * dy) ** 0.5)
        for x in range(cx - span, cx + span + 1):
            px(x, y, color)


# ---------------------------------------------------------------- text

_scaled_cache = {}


def _scaled_glyph(weight, ch, size):
    """Return (width, height, dx, dy, coverage bytes) at the wanted size.

    Coverage is an area-averaged sample of the 64 px source bitmap,
    so small text stays smooth. Results are cached per size.
    """
    key = (weight, ch, size)
    hit = _scaled_cache.get(key)
    if hit is not None:
        return hit
    glyph = font_data.GLYPHS.get((weight, ch))
    if glyph is None:
        glyph = font_data.GLYPHS[(weight, "?")]
    advance, gw, gh, dx, dy, data = glyph
    scale = size / float(font_data.SIZE)
    if gw == 0 or gh == 0:
        out = (0, 0, 0, 0, b"")
        _scaled_cache[key] = out
        return out
    raw = base64.b64decode(data)
    # Summed-area table over the source bitmap for fast box averages.
    integ = [0] * ((gw + 1) * (gh + 1))
    for yy in range(gh):
        row_sum = 0
        src_row = yy * gw
        dst_row = (yy + 1) * (gw + 1)
        prev_row = yy * (gw + 1)
        for xx in range(gw):
            row_sum += raw[src_row + xx]
            integ[dst_row + xx + 1] = integ[prev_row + xx + 1] + row_sum
    dw = max(1, int(round(gw * scale)))
    dh = max(1, int(round(gh * scale)))
    cov = bytearray(dw * dh)
    for j in range(dh):
        sy0 = j / scale
        sy1 = (j + 1) / scale
        iy0 = int(sy0)
        iy1 = int(min(gh, sy1 + 0.999999))
        if iy1 <= iy0:
            iy1 = iy0 + 1
        for i in range(dw):
            sx0 = i / scale
            sx1 = (i + 1) / scale
            ix0 = int(sx0)
            ix1 = int(min(gw, sx1 + 0.999999))
            if ix1 <= ix0:
                ix1 = ix0 + 1
            total = (integ[iy1 * (gw + 1) + ix1] - integ[iy0 * (gw + 1) + ix1]
                     - integ[iy1 * (gw + 1) + ix0] + integ[iy0 * (gw + 1) + ix0])
            area = (ix1 - ix0) * (iy1 - iy0)
            cov[j * dw + i] = total // area if area else 0
    out = (dw, dh, int(round(dx * scale)), int(round(dy * scale)), bytes(cov))
    _scaled_cache[key] = out
    return out


def text_width(text, weight, size):
    total = 0.0
    for ch in text:
        glyph = font_data.GLYPHS.get((weight, ch))
        if glyph is None:
            glyph = font_data.GLYPHS[(weight, "?")]
        total += glyph[0]
    return total * size / float(font_data.SIZE)


def draw_text(x, baseline, text, weight, size, color, align="left"):
    """Draw text; x is the left edge (or centre/right anchor)."""
    width = text_width(text, weight, size)
    if align == "center":
        x = x - width / 2.0
    elif align == "right":
        x = x - width
    pen = float(x)
    scale = size / float(font_data.SIZE)
    for ch in text:
        glyph = font_data.GLYPHS.get((weight, ch))
        if glyph is None:
            glyph = font_data.GLYPHS[(weight, "?")]
        advance = glyph[0] * scale
        dw, dh, dx, dy, cov = _scaled_glyph(weight, ch, size)
        ox = int(round(pen)) + dx
        oy = int(baseline) + dy
        for j in range(dh):
            row = (oy + j) * W
            crow = j * dw
            for i in range(dw):
                c = cov[crow + i]
                if c:
                    blend_px(ox + i, oy + j, color, c)
        pen += advance
    return pen


def wrap(text, weight, size, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    words = text.split(" ")
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, weight, size) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class Col:
    """A flowing text column: blocks stack downwards, never overlapping."""

    def __init__(self, x, width, y):
        self.x = x
        self.w = width
        self.y = y

    def kicker(self, text, size=16):
        draw_text(self.x, self.y + size, text, "bold", size, RED)
        self.y += size + 8

    def headline(self, text, size, leading=None):
        if leading is None:
            leading = int(round(size * 1.15))
        lines = wrap(text, "bold", size, self.w)
        for ln in lines:
            draw_text(self.x, self.y + size, ln, "bold", size, INK)
            self.y += leading
        self.y += 4

    def deck(self, text, size, leading=None):
        if leading is None:
            leading = int(round(size * 1.26))
        lines = wrap(text, "regular", size, self.w)
        for ln in lines:
            draw_text(self.x, self.y + size, ln, "regular", size, INK)
            self.y += leading
        self.y += 2

    def gap(self, n):
        self.y += n

    def scene(self, fn, h):
        fn(self.x, self.y, self.w, h)
        self.y += h


# ---------------------------------------------------------------- scenes

def scene_strait(x, y, w, h):
    """Strait of Hormuz: tankers, a mine, a jet overhead."""
    import math as _m
    rect(x, y, x + w, y + h, SKY)
    sea_y = y + int(h * 0.52)
    rect(x, sea_y, x + w, y + h, SEA)
    rect(x, sea_y, x + w, sea_y + 3, SEA_DARK)
    disc(x + w - 52, y + 26, 17, SUN)
    line(x + 40, y + 30, x + 150, y + 52, INK, 2)
    jx, jy = x + 165, y + 55
    line(jx - 26, jy - 8, jx + 18, jy, INK, 3)
    line(jx - 26, jy + 8, jx + 18, jy, INK, 3)
    line(jx - 6, jy - 16, jx + 2, jy, INK, 3)
    tx, ty = x + 36, sea_y + 16
    rect(tx, ty, tx + 190, ty + 26, SHIP)
    rect(tx + 130, ty - 22, tx + 168, ty, WHITE)
    rect(tx + 176, ty - 30, tx + 186, ty, RED)
    rect(tx + 20, ty - 12, tx + 110, ty, (120, 40, 40))
    tx2, ty2 = x + w - 210, sea_y + 30
    rect(tx2, ty2, tx2 + 150, ty2 + 18, (70, 70, 70))
    rect(tx2 + 96, ty2 - 14, tx2 + 124, ty2, WHITE)
    mx, my = x + w // 2 + 30, sea_y + 34
    disc(mx, my, 9, INK)
    for ang in range(0, 360, 45):
        rad = _m.radians(ang)
        line(mx + int(8 * _m.cos(rad)), my + int(8 * _m.sin(rad)),
             mx + int(15 * _m.cos(rad)), my + int(15 * _m.sin(rad)), INK, 2)
    for wx in range(x + 12, x + w - 12, 46):
        line(wx, y + h - 12, wx + 22, y + h - 12, WHITE, 2)
    disc(tx2 + 40, ty2 - 8, 8, (226, 120, 40))
    disc(tx2 + 52, ty2 - 14, 6, (240, 180, 60))


def scene_bridge(x, y, w, h):
    """Kerch Strait: a road span dropped into the water."""
    rect(x, y, x + w, y + h, SKY)
    sea_y = y + int(h * 0.58)
    rect(x, sea_y, x + w, y + h, SEA)
    disc(x + 74, y + 20, 12, SUN)
    deck_y = y + 34
    rect(x + 8, deck_y, x + 110, deck_y + 8, STEEL)
    rect(x + w - 118, deck_y, x + w - 8, deck_y + 8, STEEL)
    for tx in (x + 34, x + w - 62):
        rect(tx, y + 6, tx + 8, deck_y + 8, STEEL)
        rect(tx - 6, y + 6, tx + 14, y + 12, STEEL)
    line(x + 112, deck_y + 6, x + w - 150, sea_y + 26, STEEL, 7)
    line(x + 122, deck_y + 2, x + w - 160, sea_y + 18, (210, 210, 210), 2)
    for sx in range(x + w - 190, x + w - 120, 14):
        line(sx, sea_y + 30, sx + 8, sea_y + 22, WHITE, 2)
    for wx in range(x + 10, x + w - 10, 40):
        line(wx, y + h - 10, wx + 20, y + h - 10, WHITE, 2)


def scene_manila(x, y, w, h):
    """Manila skyline at dusk, flags of the Quad meeting."""
    rect(x, y, x + w, y + h, (232, 204, 158))
    disc(x + w - 46, y + 24, 16, SUN)
    base = y + h
    heights = [52, 78, 64, 92, 58, 84, 70, 48]
    bw = w // len(heights)
    for i, hh in enumerate(heights):
        bx = x + i * bw + 3
        rect(bx, base - hh, bx + bw - 6, base, (64, 72, 84))
        for wy in range(base - hh + 8, base - 6, 12):
            for wx in range(bx + 5, bx + bw - 11, 10):
                px(wx, wy, (240, 200, 90))
                px(wx + 1, wy, (240, 200, 90))
    for fx in (x + 26, x + w - 60):
        vline(fx, y + 8, base - 92, INK, 2)
        rect(fx + 2, y + 8, fx + 30, y + 20, RED)
        rect(fx + 2, y + 20, fx + 30, y + 26, WHITE)


def scene_chips(x, y, w, h):
    """A chip and a falling market bar chart."""
    rect(x, y, x + w, y + h, WHITE)
    cx, cy, cs = x + 16, y + 8, 44
    rect(cx - 6, cy - 6, cx + cs + 6, cy + cs + 6, INK)
    rect(cx, cy, cx + cs, cy + cs, (38, 90, 66))
    rect(cx + 10, cy + 10, cx + cs - 10, cy + cs - 10, (120, 170, 190))
    for i in range(4):
        rect(cx + 7 + i * 11, cy - 12, cx + 11 + i * 11, cy - 6, INK)
        rect(cx + 7 + i * 11, cy + cs + 6, cx + 11 + i * 11, cy + cs + 12, INK)
    bx = x + 96
    bars = [40, 34, 28, 22, 14]
    bw = (w - 110) // len(bars)
    for i, bh in enumerate(bars):
        rect(bx + i * bw + 4, y + h - 10 - bh, bx + (i + 1) * bw - 4,
             y + h - 10, RED if i >= 3 else (70, 70, 70))
    line(bx, y + 12, bx + w - 116, y + h - 26, INK, 2)
    draw_text(x + w - 8, y + 22, "-5%", "bold", 20, RED, align="right")


def scene_measles_bars(x, y, w, h):
    """Cases rising: three bars and a red arrow."""
    rect(x, y, x + w, y + h, WHITE)
    bars = [18, 34, 58]
    for i, bh in enumerate(bars):
        bx = x + 10 + i * 30
        rect(bx, y + h - 8 - bh, bx + 24, y + h - 8,
             RED if i == 2 else (90, 90, 90))
    line(x + 12, y + h - 22, x + w - 12, y + 16, RED, 3)
    line(x + w - 12, y + 16, x + w - 26, y + 18, RED, 3)
    line(x + w - 12, y + 16, x + w - 14, y + 30, RED, 3)


def scene_france_crowd(x, y, w, h):
    """A marching crowd: heads, shoulders, placards."""
    rect(x, y, x + w, y + h, (232, 226, 214))
    for row, yy in enumerate((y + 22, y + 52)):
        for i in range(5):
            hx = x + 12 + i * 16 + (8 if row else 0)
            disc(hx, yy, 8, INK if row == 0 else (70, 70, 70))
            rect(hx - 10, yy + 8, hx + 10, yy + 18, INK if row == 0 else (70, 70, 70))
    for px0 in (x + 8, x + w - 50):
        vline(px0 + 20, y + 6, y + 34, INK, 2)
        rect(px0, y + 6, px0 + 42, y + 28, WHITE)
        hline(px0, px0 + 42, y + 6, INK, 1)
        hline(px0, px0 + 42, y + 28, INK, 1)
        vline(px0, y + 6, y + 28, INK, 1)
        vline(px0 + 42, y + 6, y + 28, INK, 1)


# ---------------------------------------------------------------- page

def main():
    fill(PAPER)
    m = 30
    right = W - m

    # Masthead
    hline(m, right, 24, RULE, 1)
    draw_text(W // 2, 92, "THE WORLD TODAY", "bold", 68, INK, align="center")
    draw_text(W // 2, 128, "TUESDAY, 17 NOVEMBER 2026", "bold", 25, INK,
              align="center")
    draw_text(W // 2, 152, "ONE DAY \u00b7 ONE PAGE \u00b7 THE WORLD",
              "regular", 15, GREY, align="center")
    hline(m, right, 162, RULE, 4)
    hline(m, right, 170, RULE, 1)

    y = 186

    # ---- Lead row: the Gulf (left) and Kerch Bridge (right)
    left = Col(m, 592, y)
    left.kicker("THE GULF \u2014 LEAD")
    left.headline("U.S. STRIKES IRAN AS GULF TANKER WAR SPREADS", 36)
    left.deck("Washington hits missile sites on Qeshm Island after mines "
              "set a fourth tanker ablaze in 24 hours. Drones aimed at a "
              "U.S. radar base in Bahrain are intercepted; Trump calls "
              "dirty-bomb reports \u201ctaken seriously\u201d, unverified.",
              19)
    left.gap(6)
    left.scene(scene_strait, 100)
    rightc = Col(646, right - 646, y)
    rightc.kicker("UKRAINE \u2014 EUROPE")
    rightc.headline("KERCH BRIDGE SPAN FALLS INTO THE SEA", 28)
    rightc.deck("Kyiv hits the bridge for a second straight day; "
                "CNN-verified video shows a road section collapsed into "
                "the strait and traffic halted. Russia answers with "
                "strikes on Kyiv\u2019s bridges, cutting water and heat.",
                18)
    rightc.gap(6)
    rightc.scene(scene_bridge, 100)
    y = max(left.y, rightc.y) + 8
    hline(m, right, y, RULE, 1)
    y += 12

    # ---- Row 2: Trump in Manila (left) and chips (right)
    left = Col(m, 460, y)
    left.scene(scene_manila, 56)
    left.kicker("ASIA \u2014 DIPLOMACY")
    left.headline("TRUMP OPENS ASIA TRIP WITH QUAD IN MANILA", 26)
    left.deck("Quad leaders meet for the first time since his return; "
              "about 1,500 protest outside. Next: APEC in Shenzhen, "
              "then a first Trump\u2013Xi\u2013Putin meeting.",
              17)
    rightc = Col(534, 460, y)
    rightc.scene(scene_chips, 56)
    rightc.kicker("TECH \u2014 MARKETS")
    rightc.headline("U.S. TIGHTENS AI-CHIP RULES; STOCKS SLIDE", 26)
    rightc.deck("New export curbs target data centres renting computing "
                "power to China. Chip shares fall about 5% ahead of "
                "Nvidia\u2019s results.",
                17)
    y = max(left.y, rightc.y) + 8
    hline(m, right, y, RULE, 1)
    y += 12

    # ---- Row 3: measles (left) and France (right)
    left = Col(m, 330, y)
    left.kicker("HEALTH \u2014 UNITED STATES")
    left.headline("U.S. LOSES MEASLES-FREE STATUS", 22)
    left.deck("Most U.S. measles cases in 30+ years; elimination status "
              "lost.",
              17)
    scene_measles_bars(392, y, 98, 84)
    rightc = Col(534, 330, y)
    rightc.kicker("EUROPE \u2014 PROTEST")
    rightc.headline("FRENCH STRIKES DRAW SMALLER CROWDS", 22)
    rightc.deck("146,000 march in a pay strike \u2014 down from 575,000 "
                "on 5 November.",
                17)
    scene_france_crowd(896, y, 98, 84)
    y = max(left.y, rightc.y) + 8
    hline(m, right, y, RULE, 1)
    y += 12

    # ---- Also today strip
    draw_text(m, y + 16, "ALSO TODAY", "bold", 14, RED)
    strip = [
        ("GAZA", "Four nations press Israel to open Gaza aid crossings."),
        ("ISRAEL", "Knesset elects Matan Kahana speaker, 66\u201352, a blow "
         "to Netanyahu."),
        ("EUROPE", "Five states plan a Rwanda migrant return hub; "
         "transfers from 2027."),
        ("GREECE", "Five held over a suspected Iran-linked assassination "
         "plot."),
        ("CLIMATE", "COP31 draft: faster fossil-fuel exit, $120bn a year "
         "by 2035."),
    ]
    sx = m + 108
    sw = (right - sx) // 5
    for i, (label, text) in enumerate(strip):
        cx = sx + i * sw
        draw_text(cx, y + 16, label, "bold", 12, INK)
        yy = y + 34
        for ln in wrap(text, "regular", 12, sw - 12):
            draw_text(cx, yy, ln, "regular", 12, INK)
            yy += 15
    y += 68
    hline(m, right, y, RULE, 1)
    draw_text(W // 2, y + 20,
              "Sources: Reuters \u00b7 BBC \u00b7 CNN \u00b7 AP \u00b7 UN News "
              "\u2014 Stories reported 17 Nov 2026 \u00b7 Drawn "
              "programmatically",
              "regular", 12, GREY, align="center")
    print("layout ends at y=%d (canvas %d)" % (y + 22, H), file=sys.stderr)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        out_dir = "/output" if os.path.isdir("/output") else "out"
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    write_png(path)
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    size = os.path.getsize(path)
    print("wrote %s (%d bytes) sha256 %s" % (path, size, digest))


def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw += canvas[yy * W * 3:(yy + 1) * W * 3]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    data = b"\x89PNG\r\n\x1a\n"
    data += chunk(b"IHDR", ihdr)
    data += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    data += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(data)


if __name__ == "__main__":
    main()
