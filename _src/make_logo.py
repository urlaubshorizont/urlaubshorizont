"""Erzeugt alle Logo-Dateien von Urlaubshorizont (Richtung „Seekarte“).

Aufruf (im Projektordner):  python _src/make_logo.py
Braucht: pip install fonttools brotli uharfbuzz pillow

Ausgabe (veröffentlicht):
  logo/logo.svg              Zeichen + Schriftzug, dunkel (für helle Flächen)
  logo/logo-hell.svg         Zeichen + Schriftzug, hell (für dunkle Flächen)
  logo/zeichen.svg           nur das Zeichen
  logo/zeichen-512.png       Profilbild (Pinterest, Social Media)
  favicon.svg                Browser-Tab (vereinfacht für 16 px)
  apple-touch-icon.png       180 × 180 für Handy-Startbildschirme
Ausgabe (privat): _agent/fonts/*.ttf für die Pin-Grafiken.

Der Schriftzug ist in Pfade umgewandelt: Das Logo sieht überall gleich aus,
auch wo die Schrift nicht installiert ist.
"""
import io
import math
import os

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONTS = os.path.join(ROOT, "fonts")

# Farben Richtung „Seekarte“
PAPER, INK, SHALLOW, LIGHT, LIGHT_ON_DARK = "#F4F7F6", "#0F2D3F", "#BFD9E6", "#A8235F", "#E0679B"


# ---------------------------------------------------------------- Zeichen
def mark_svg(fg=INK, bg=PAPER, sea=SHALLOW, sun=LIGHT, waves=2, stroke=3.0, cid="c"):
    """Kreis mit Horizontlinie, halber Sonne (Leuchtfeuer-Magenta) und Tiefenlinien."""
    wave_d = ["M2 45 q7.5 -3.2 15 0 t15 0 t15 0 t15 0", "M2 53 q7.5 -3.2 15 0 t15 0 t15 0 t15 0"][:waves]
    wave = "".join(
        f'<path d="{d}" fill="none" stroke="{fg}" stroke-width="{1.6 if waves == 2 else 2.6}" '
        f'stroke-linecap="round"{" opacity=\".55\"" if i else ""}/>' for i, d in enumerate(wave_d))
    sea_rect = f'<rect x="0" y="36" width="64" height="28" fill="{sea}"/>' if sea else ""
    return (f'<clipPath id="{cid}"><circle cx="32" cy="32" r="28.5"/></clipPath>'
            f'<circle cx="32" cy="32" r="30" fill="{bg}"/>'
            f'<g clip-path="url(#{cid})">{sea_rect}{wave}</g>'
            f'<path d="M21 36 A11 11 0 0 1 43 36 Z" fill="{sun}"/>'
            f'<line x1="3" y1="36" x2="61" y2="36" stroke="{fg}" stroke-width="{stroke}"/>'
            f'<circle cx="32" cy="32" r="30" fill="none" stroke="{fg}" stroke-width="{stroke}"/>')


def svg_doc(w, h, inner, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" role="img" aria-label="{title}">'
            f'<title>{title}</title>{inner}</svg>\n')


# ---------------------------------------------------------------- Schriftzug
def brygada_600():
    f = TTFont(os.path.join(FONTS, "brygada-1918-latin-wght-normal.woff2"))
    f.flavor = None
    return instantiateVariableFont(f, {"wght": 600})


def text_paths(font, text, size):
    """Formt den Text mit HarfBuzz (Kerning, Ligaturen) und gibt SVG-Pfaddaten + Breite zurück."""
    buf = io.BytesIO()
    font.save(buf)
    data = buf.getvalue()
    upm = font["head"].unitsPerEm
    hbf = hb.Font(hb.Face(hb.Blob(data)))
    b = hb.Buffer()
    b.add_str(text)
    b.guess_segment_properties()
    hb.shape(hbf, b, {"kern": True, "liga": True})
    glyphs = font.getGlyphSet()
    order = font.getGlyphOrder()
    s = size / upm
    x = 0
    parts = []
    for info, pos in zip(b.glyph_infos, b.glyph_positions):
        pen = SVGPathPen(glyphs)
        # y nach unten (SVG), Grundlinie bei 0
        glyphs[order[info.codepoint]].draw(TransformPen(pen, (s, 0, 0, -s, (x + pos.x_offset) * s, -pos.y_offset * s)))
        parts.append(pen.getCommands())
        x += pos.x_advance
    return " ".join(p for p in parts if p), x * s


def write(path, content, mode="w"):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, mode, **({} if "b" in mode else {"encoding": "utf-8", "newline": "\n"})) as f:
        f.write(content)
    print("geschrieben:", path)


# ---------------------------------------------------------------- PNG (Pillow)
def mark_png(size, pad=0.0, bg=None):
    """Zeichnet das Zeichen in hoher Auflösung und verkleinert es (glatte Kanten)."""
    k = 8
    S = size * k
    img = Image.new("RGBA", (S, S), bg or (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    inner = S * (1 - 2 * pad)
    off = S * pad
    u = inner / 64  # 1 Einheit des 64er-Rasters

    def P(x, y):
        return (off + x * u, off + y * u)

    # Kreisfläche
    d.ellipse([P(2, 2), P(62, 62)], fill=PAPER)
    # Meer (nur innerhalb des Kreises): Maske
    sea = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sea)
    sd.rectangle([P(0, 36), P(64, 64)], fill=SHALLOW)
    for i, y0 in enumerate((45, 53)):
        pts = [P(2 + t, y0 - 1.6 * math.sin(math.pi * t / 15)) for t in [j * 0.25 for j in range(0, 241)]]
        col = INK if i == 0 else "#7A94A3"
        sd.line(pts, fill=col, width=max(1, round(1.6 * u)), joint="curve")
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse([P(3.5, 3.5), P(60.5, 60.5)], fill=255)
    img.paste(sea, (0, 0), Image.composite(sea, Image.new("RGBA", (S, S)), mask).split()[3])
    # Sonne (Halbkreis)
    d.pieslice([P(21, 25), P(43, 47)], 180, 360, fill=LIGHT)
    # Horizont und Ring
    w = round(3 * u)
    d.line([P(3, 36), P(61, 36)], fill=INK, width=w)
    d.ellipse([P(2 - 1.5, 2 - 1.5), P(62 + 1.5, 62 + 1.5)], outline=INK, width=w)
    return img.resize((size, size), Image.LANCZOS)


def main():
    font = brygada_600()
    size = 34
    paths, width = text_paths(font, "Urlaubshorizont", size)
    gap, mark = 14, 64
    baseline = 43.5          # Schriftzug optisch auf Höhe der Horizontlinie
    W = mark + gap + width + 2
    t = f'translate({mark + gap:.2f} {baseline})'

    write("logo/logo.svg", svg_doc(W, 64, mark_svg(cid="l1") + f'<path transform="{t}" fill="{INK}" d="{paths}"/>',
                                   "Urlaubshorizont"))
    write("logo/logo-hell.svg", svg_doc(W, 64, mark_svg(fg=PAPER, bg=INK, sea=None, sun=LIGHT_ON_DARK, cid="l2")
                                        + f'<path transform="{t}" fill="{PAPER}" d="{paths}"/>', "Urlaubshorizont"))
    write("logo/zeichen.svg", svg_doc(64, 64, mark_svg(cid="z"), "Urlaubshorizont"))
    # Favicon: nur eine, kräftigere Tiefenlinie, dickere Striche – bleibt bei 16 px erkennbar
    write("favicon.svg", svg_doc(64, 64, mark_svg(waves=1, stroke=4.5, cid="f"), "Urlaubshorizont"))

    buf = io.BytesIO()
    mark_png(512, pad=0.06, bg=SHALLOW).save(buf, "PNG", optimize=True)
    write("logo/zeichen-512.png", buf.getvalue(), "wb")
    buf = io.BytesIO()
    mark_png(180, pad=0.1, bg=PAPER).convert("RGB").save(buf, "PNG", optimize=True)
    write("apple-touch-icon.png", buf.getvalue(), "wb")

    # Statische TTF-Schriften für die Pin-Grafiken (Pillow liest kein woff2)
    out = os.path.join(ROOT, "_agent", "fonts")
    if os.path.isdir(os.path.join(ROOT, "_agent")):
        os.makedirs(out, exist_ok=True)
        font.save(os.path.join(out, "Brygada1918-SemiBold.ttf"))
        it = TTFont(os.path.join(FONTS, "brygada-1918-latin-wght-italic.woff2"))
        it.flavor = None
        instantiateVariableFont(it, {"wght": 400}).save(os.path.join(out, "Brygada1918-Italic.ttf"))
        for src, name in (("atkinson-hyperlegible-latin-400-normal", "AtkinsonHyperlegible-Regular"),
                          ("atkinson-hyperlegible-latin-700-normal", "AtkinsonHyperlegible-Bold"),
                          ("ibm-plex-mono-latin-400-normal", "IBMPlexMono-Regular")):
            f = TTFont(os.path.join(FONTS, src + ".woff2"))
            f.flavor = None
            f.save(os.path.join(out, name + ".ttf"))
        print("Pin-Schriften:", sorted(os.listdir(out)))


if __name__ == "__main__":
    main()
