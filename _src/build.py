"""Erzeugt die komplette Website urlaubshorizont.de aus content.py.

Aufruf (im Projektordner):  python3 _src/build.py
Ausgabe: alle Seiten im Projektordner (eine Ebene über _src/).
Der Ordner _src/ wird von GitHub Pages nicht veröffentlicht.
"""
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from content import SITE, MONTHS, DESTINATIONS, ARTICLES  # noqa: E402

E = html.escape
CSS = open(os.path.join(HERE, "style.css"), encoding="utf-8").read()


# ---------------------------------------------------------------- Bausteine
PHOTO_DIR = os.path.join(OUT, "bilder")          # veröffentlicht
SOURCE_DIR = os.path.join(HERE, "fotos")         # deine Originale, NICHT veröffentlicht


def process_photos():
    """Originale aus _src/fotos/ verkleinern, Metadaten (GPS, Kamera) entfernen
    und als bilder/<reiseziel>.jpg speichern."""
    os.makedirs(PHOTO_DIR, exist_ok=True)
    if not os.path.isdir(SOURCE_DIR):
        return
    try:
        from PIL import Image, ImageOps
    except ImportError:
        print("Hinweis: Pillow fehlt. Installieren mit:  pip install pillow")
        print("         Ohne Pillow werden Fotos aus _src/fotos/ nicht übernommen.")
        return
    slugs = {d["slug"] for d in DESTINATIONS}
    for name in sorted(os.listdir(SOURCE_DIR)):
        slug, ext = os.path.splitext(name)
        if ext.lower() not in (".jpg", ".jpeg", ".png", ".webp", ".heic"):
            continue
        if slug not in slugs:
            print(f"Übersprungen: {name} (Dateiname muss einem Reiseziel entsprechen, z. B. kanaren.jpg)")
            continue
        src = os.path.join(SOURCE_DIR, name)
        dst = os.path.join(PHOTO_DIR, f"{slug}.jpg")
        if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
            continue
        img = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        img.thumbnail((2000, 2000))
        img.save(dst, "JPEG", quality=82, optimize=True, progressive=True)  # ohne EXIF/GPS
        print(f"Foto übernommen: {name} -> bilder/{slug}.jpg ({os.path.getsize(dst) // 1024} KB)")


def photo(slug):
    """Dateiname des Reiseziel-Fotos in bilder/ oder None."""
    for ext in ("jpg", "jpeg", "webp", "png"):
        if os.path.exists(os.path.join(PHOTO_DIR, f"{slug}.{ext}")):
            return f"{slug}.{ext}"
    return None


def tile_style(d, prefix):
    """Inline-Style für Flächen: Foto, falls vorhanden, sonst Farbhorizont."""
    p = photo(d["slug"])
    base = f"--sky:{d['sky']};--land:{d['land']}"
    return f"{base};--img:url('{prefix}bilder/{p}')" if p else base


def tile_class(d):
    return " has-img" if photo(d["slug"]) else ""

def months_bar(best, compact=False):
    cells = "".join(
        f'<li class="m{" on" if i + 1 in best else ""}" title="{MONTHS[i]}">'
        f'<span aria-hidden="true">{MONTHS[i][0]}</span></li>'
        for i in range(12)
    )
    label = "Beste Reisezeit: " + ", ".join(MONTHS[i - 1] for i in sorted(best))
    return f'<ol class="months{" compact" if compact else ""}" aria-label="{E(label)}">{cells}</ol>'


def nav_link(href, label, active):
    cur = ' aria-current="page"' if active else ""
    return f'<a href="{href}"{cur}>{label}</a>'


def page(path, title, desc, body, active="", og_image="", index=True):
    depth = path.count("/")
    robots = "" if index else '<meta name="robots" content="noindex, follow">'
    root = "../" * depth
    canonical = SITE["url"] + "/" + (path[:-len("index.html")] if path.endswith("index.html") else path)
    verify = (f'<meta name="p:domain_verify" content="{E(SITE["pinterest_verify"])}">'
              if SITE["pinterest_verify"] else "")
    og_tag = f'<meta property="og:image" content="{og_image}">' if og_image else ""
    pin = (f'<a href="{E(SITE["pinterest"])}" rel="noopener" target="_blank">Pinterest</a>'
           if SITE["pinterest"] else "")
    nav = (nav_link(f"{root}#reiseziele", "Reiseziele", active == "home")
           + nav_link(f"{root}ratgeber/", "Ratgeber", active == "ratgeber")
           + nav_link(f"{root}reisekalender/", "Reisekalender", active == "kalender")
           + nav_link(f"{root}ueber-uns/", "Über uns", active == "about"))
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
{robots}
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE['name']}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="de_DE">
{og_tag}
{verify}
<link rel="icon" href="{root}favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="{root}apple-touch-icon.png">
<link rel="preload" href="/fonts/atkinson-hyperlegible-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/brygada-1918-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<meta name="theme-color" content="#0F2D3F">
<style>
{CSS}
</style>
</head>
<body>
<a class="skip" href="#inhalt">Zum Inhalt springen</a>
<header class="site">
  <a class="brand" href="{root}"><img src="{root}logo/zeichen.svg" alt="" width="38" height="38">{SITE['name']}</a>
  <nav aria-label="Hauptnavigation">{nav}</nav>
</header>
<main id="inhalt">
{body}
</main>
<footer class="site">
  <div class="foot-grid">
    <div>
      <p class="foot-brand">{SITE['name']}</p>
      <p class="note">{SITE['claim']}.</p>
    </div>
    <nav aria-label="Reiseziele">
      {''.join(f'<a href="{root}reiseziele/{d["slug"]}/">{d["name"]}</a>' for d in DESTINATIONS)}
    </nav>
    <nav aria-label="Rechtliches">
      <a href="{root}ratgeber/">Ratgeber</a>
      <a href="{root}reisekalender/">Reisekalender</a>
      <a href="{root}ueber-uns/">Über uns</a>
      <a href="{root}impressum/">Impressum</a>
      <a href="{root}datenschutz/">Datenschutz</a>
      {pin}
    </nav>
  </div>
  <p class="note disclosure">Links zu Buchungsportalen können Affiliate-Links sein. Buchst du darüber, erhalten wir eventuell eine Provision. Für dich ändert sich am Preis nichts.</p>
  <p class="copy">© {SITE['year']} {SITE['name']}</p>
</footer>
</body>
</html>
"""


def write(path, content):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def hotel_link(h):
    if h.get("link"):
        return h["link"]
    from content import booking_url
    return booking_url(*h["booking"])


def booking_button(h, label="Preise und Verfügbarkeit bei Booking.com"):
    return (f'<a class="btn" href="{E(hotel_link(h))}" rel="sponsored nofollow noopener" '
            f'target="_blank">{label}</a>')


def hotel_media(d, h, cls="hotel-img"):
    if h.get("image"):
        return (f'<img class="{cls}" src="{E(h["image"])}" alt="{E(h["name"])}" '
                f'loading="lazy" width="640" height="400">')
    return (f'<div class="hotel-band" style="--sky:{d["sky"]};--land:{d["land"]}" aria-hidden="true">'
            f'<span></span></div>')


def hotel_card(d, h, prefix):
    """Kompakte Karte, verlinkt auf die Hotelseite. prefix = Weg von der aktuellen
    Seite zum Reiseziel-Ordner (z. B. "" auf der Reiseziel-Seite, "../" auf einer Hotelseite)."""
    tags = "".join(f"<li>{E(t)}</li>" for t in h["tags"])
    return f"""
    <li class="hotel compact" id="hotel-{h['id']}">
      <a class="hotel-link" href="{prefix}{h['id']}/">
        {hotel_media(d, h)}
        <div class="hotel-body">
          <p class="where">{E(h['place'])}</p>
          <h3>{E(h['name'])}</h3>
          <ul class="tags">{tags}</ul>
          <p class="ideal">Ideal für {E(h.get('ideal', ''))}</p>
          <span class="more">Zum Hotel <span aria-hidden="true">→</span></span>
        </div>
      </a>
    </li>"""


# ---------------------------------------------------------------- Hotel-Register
# Jede Hotel-ID, die je veröffentlicht wurde, steht in _src/hotel_ids.txt ("<reiseziel>/<id>").
# Verschwindet ein Hotel aus content.py, bleibt seine Adresse als Weiterleitung aufs
# Reiseziel bestehen – Pins zeigen so nie ins Leere.
REGISTRY = os.path.join(HERE, "hotel_ids.txt")


def update_registry():
    known = set()
    if os.path.exists(REGISTRY):
        with open(REGISTRY, encoding="utf-8-sig") as f:
            known = {ln.strip() for ln in f if "/" in ln and not ln.lstrip().startswith("#")}
    current = {f"{d['slug']}/{h['id']}" for d in DESTINATIONS for h in d["hotels"]}
    ids = [h["id"] for d in DESTINATIONS for h in d["hotels"]]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        sys.exit(f"Fehler: Hotel-ID mehrfach vergeben: {', '.join(sorted(dupes))}")
    with open(REGISTRY, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Alle je veröffentlichten Hotel-Adressen. Nicht von Hand löschen.\n")
        f.write("".join(f"{x}\n" for x in sorted(known | current)))
    return sorted(known - current)


def build_removed(entry):
    slug, hid = entry.split("/", 1)
    dest = next((d for d in DESTINATIONS if d["slug"] == slug), None)
    target = f"{SITE['url']}/reiseziele/{slug}/" if dest else SITE["url"] + "/"
    write(f"reiseziele/{slug}/{hid}/index.html", f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>Weiterleitung | {SITE['name']}</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="{target}">
<meta http-equiv="refresh" content="0; url={target}">
</head>
<body>
<p>Dieses Hotel stellen wir nicht mehr vor. Weiter zu <a href="{target}">{E(dest['name']) if dest else SITE['name']}</a>.</p>
</body>
</html>
""")


def build_hotel(d, h):
    tags = "".join(f"<li>{E(t)}</li>" for t in h["tags"])
    hl = "".join(f"<li>{E(x)}</li>" for x in h.get("highlights", []))
    others = "".join(hotel_card(d, o, "../") for o in d["hotels"] if o["id"] != h["id"])
    image = (f'<img class="hotel-photo" src="{E(h["image"])}" alt="{E(h["name"])}" width="1280" height="800">'
             if h.get("image") else "")
    og = h.get("image") or (f"{SITE['url']}/bilder/{photo(d['slug'])}" if photo(d["slug"]) else "")
    path = f"reiseziele/{d['slug']}/{h['id']}/index.html"
    # Optional in content.py: "fits_if" / "not_if" = Listen mit kurzen Sätzen
    fit = ""
    if h.get("fits_if") or h.get("not_if"):
        yes = "".join(f"<li>{E(x)}</li>" for x in h.get("fits_if", []))
        no = "".join(f"<li>{E(x)}</li>" for x in h.get("not_if", []))
        fit = (f'<div class="fit">'
               + (f'<div><h3>Passt zu dir, wenn …</h3><ul>{yes}</ul></div>' if yes else "")
               + (f'<div class="no"><h3>Eher nicht, wenn …</h3><ul>{no}</ul></div>' if no else "")
               + "</div>")
    arts = [a for a in ARTICLES if any(i == h["id"] for i, _ in a["hotels"])]
    mentioned = ""
    if arts:
        mentioned = ("<h2>Im Ratgeber</h2><ul class=\"art-links\">"
                     + "".join(f'<li><a href="../../../ratgeber/{a["slug"]}/">{E(a["title"])}</a></li>' for a in arts)
                     + "</ul>")
    body = f"""
<section class="dest-hero hotel-hero{tile_class(d)}" style="{tile_style(d, '../../../')}">
  <p class="crumb"><a href="../../../">Start</a> <span aria-hidden="true">/</span> <a href="../">{d['name']}</a></p>
  <h1>{E(h['name'])}</h1>
  <p class="dest-sub">{E(h['place'])}</p>
</section>

<div class="cta-bar">
  {booking_button(h)}
  <p class="note">Aktuelle Preise und freie Zimmer siehst du direkt bei Booking.com.</p>
</div>

<div class="dest-body">
  <article class="prose">
    {image}
    <ul class="tags">{tags}</ul>
    <p>{E(h['text'])}</p>
    <h2>Das zeichnet das Hotel aus</h2>
    <ul class="highlights">{hl}</ul>
    {fit}
    {mentioned}
    <p class="note">Links zu Buchungsportalen können Affiliate-Links sein. Für dich ändert sich am Preis nichts.</p>
  </article>
  <aside class="facts" aria-label="Auf einen Blick">
    <h2>Auf einen Blick</h2>
    <h3>Lage</h3>
    <p>{E(h['place'])}</p>
    <h3>Ideal für</h3>
    <p>{E(h.get('ideal', ''))}</p>
    <h3>Anreise</h3>
    <p>{E(h.get('arrival', ''))}</p>
    <h3>Beste Reisezeit</h3>
    {months_bar(d['best'])}
    <h3>Flugzeit ab Deutschland</h3>
    <p class="mono">{d['flight']}</p>
    {booking_button(h, "Zum Hotel bei Booking.com")}
  </aside>
</div>

<section class="hotels" aria-labelledby="h-more">
  <div class="section-head">
    <h2 id="h-more">Weitere Hotels: {d['name']}</h2>
    <a class="more" href="../">Alles über {d['name']} →</a>
  </div>
  <ul class="hotel-list">{others}
  </ul>
</section>
"""
    first = h["text"].split(". ")[0].rstrip(".") + "."
    # Hotelseiten sind für Google ausgeblendet (dünner Inhalt), bis ein Hotel "index": True bekommt.
    write(path, page(path, f"{h['name']}, {h['place']} | {SITE['name']}",
                     f"{h['name']} ({h['place']}): {first}", body, og_image=og,
                     index=bool(h.get("index"))))


# ---------------------------------------------------------------- Ratgeber-Artikel
HOTELS = {h["id"]: (d, h) for d in DESTINATIONS for h in d["hotels"]}


def check_articles():
    slugs = [a["slug"] for a in ARTICLES]
    if len(slugs) != len(set(slugs)):
        sys.exit("Fehler: Artikel-Slug mehrfach vergeben.")
    for a in ARTICLES:
        for hid, _ in a["hotels"]:
            if hid not in HOTELS:
                sys.exit(f"Fehler: Artikel {a['slug']} nennt unbekanntes Hotel {hid}.")


def article_style(a, prefix):
    d = next((x for x in DESTINATIONS if x["slug"] == a.get("dest")), DESTINATIONS[0])
    return d, tile_style(d, prefix), tile_class(d)


def build_article(a):
    d0, style, cls = article_style(a, "../../")
    intro = "".join(f"<p>{p}</p>" for p in a["intro"])
    items = ""
    for n, (hid, note) in enumerate(a["hotels"], 1):
        d, h = HOTELS[hid]
        tags = "".join(f"<li>{E(t)}</li>" for t in h["tags"])
        items += f"""
    <li class="art-hotel" id="hotel-{hid}">
      <div class="art-media">{hotel_media(d, h)}<span class="num">{n}</span></div>
      <div class="art-body">
        <p class="where">{E(h['place'])}</p>
        <h2>{E(h['name'])}</h2>
        <ul class="tags">{tags}</ul>
        <p>{E(note or h['text'])}</p>
        <p class="ideal"><strong>Ideal für:</strong> {E(h.get('ideal', ''))}</p>
        <div class="art-actions">
          {booking_button(h, "Bei Booking.com ansehen")}
          <a class="btn-2" href="../../reiseziele/{d['slug']}/{hid}/">Mehr zum Hotel</a>
        </div>
      </div>
    </li>"""
    dests = []
    for hid, _ in a["hotels"]:
        d = HOTELS[hid][0]
        if d not in dests:
            dests.append(d)
    dest_links = " · ".join(f'<a href="../../reiseziele/{d["slug"]}/">{d["name"]}: beste Reisezeit und alle Hotels</a>'
                            for d in dests)
    outro = "".join(f"<p>{p}</p>" for p in a.get("outro", []))
    body = f"""
<section class="dest-hero art-hero{cls}" style="{style}">
  <p class="crumb"><a href="../../">Start</a> <span aria-hidden="true">/</span> <a href="../">Ratgeber</a></p>
  <h1>{E(a['title'])}</h1>
  <p class="dest-sub">{E(a['short'])}</p>
</section>

<article class="article">
  <div class="prose art-intro">
    {intro}
    <p class="note">Stand: {a.get('updated', SITE['updated'])}. Links zu Buchungsportalen können Affiliate-Links sein. Für dich ändert sich am Preis nichts.</p>
  </div>
  <ol class="art-list">{items}
  </ol>
  <div class="prose">
    {outro}
    <p>{dest_links}</p>
  </div>
</article>
"""
    og = f"{SITE['url']}/bilder/{photo(d0['slug'])}" if photo(d0["slug"]) else ""
    write(f"ratgeber/{a['slug']}/index.html", page(
        f"ratgeber/{a['slug']}/index.html", f"{a['title']} | {SITE['name']}", a["short"], body,
        "ratgeber", og_image=og))


def article_teasers(arts, prefix):
    out = ""
    for a in arts:
        d, style, cls = article_style(a, prefix)
        out += f"""
    <li><a class="art-teaser" href="{prefix}ratgeber/{a['slug']}/">
      <span class="tile{cls}" style="{style}" aria-hidden="true"></span>
      <span><strong>{E(a['title'])}</strong><br><small>{len(a['hotels'])} Hotels · {E(a['short'])}</small></span>
    </a></li>"""
    return f'<ul class="art-teasers">{out}\n  </ul>'


def build_article_index():
    body = f"""
<section class="plain">
  <h1>Ratgeber</h1>
  <p class="lead">Hotel-Listen zu bestimmten Urlaubsarten – zum Beispiel nur für Erwachsene, mit eigenem Pool oder besonders ruhig gelegen.</p>
  {article_teasers(ARTICLES, "../")}
</section>"""
    write("ratgeber/index.html", page("ratgeber/index.html", f"Ratgeber: Hotel-Listen | {SITE['name']}",
          "Hotel-Listen zu Urlaubsarten: Adults only, Pool-Villen, ruhige Lage und mehr.", body, "ratgeber"))


# ---------------------------------------------------------------- Reisezeit pro Monat
MONTH_SLUGS = ["januar", "februar", "maerz", "april", "mai", "juni", "juli",
               "august", "september", "oktober", "november", "dezember"]


def build_month(i):
    m, slug = MONTHS[i], MONTH_SLUGS[i]
    good = [d for d in DESTINATIONS if i + 1 in d["best"]]
    rest = [d for d in DESTINATIONS if i + 1 not in d["best"]]
    cards = ""
    for d in good:
        picks = "".join(f'<li><a href="../../reiseziele/{d["slug"]}/{h["id"]}/">{E(h["name"])}</a> <small>{E(h["place"])}</small></li>'
                        for h in d["hotels"][:3])
        cards += f"""
    <li class="month-dest">
      <a class="tile{tile_class(d)}" href="../../reiseziele/{d['slug']}/" style="{tile_style(d, '../../')}"><span>{d['name']}</span></a>
      <div>
        <h2><a href="../../reiseziele/{d['slug']}/">{d['name']}</a></h2>
        <p>{d['short']}</p>
        <p class="note mono">Flug {d['flight']} · beste Reisezeit:</p>
        {months_bar(d['best'])}
        <h3>Hotel-Tipps</h3>
        <ul class="month-picks">{picks}</ul>
      </div>
    </li>"""
    prev_i, next_i = (i - 1) % 12, (i + 1) % 12
    rest_txt = ", ".join(f'<a href="../../reiseziele/{d["slug"]}/">{d["name"]}</a>' for d in rest)
    lead = (f"Im {m} sind {len(good)} unserer Reiseziele in ihrer besten Reisezeit."
            if len(good) != 1 else f"Im {m} ist ein Reiseziel in seiner besten Reisezeit.")
    body = f"""
<section class="plain">
  <p class="plain-crumb"><a href="../../">Start</a> / <a href="../">Reisekalender</a></p>
  <h1>Wohin im {m}?</h1>
  <p class="lead">{lead} Hier findest du sie mit Flugzeit und ausgewählten Hotels.</p>
  <ul class="month-list">{cards}
  </ul>
  <p>Weniger ideal im {m}: {rest_txt or '–'}.</p>
  <p class="note">Die Reisezeiten sind Richtwerte für Sonne und Badewetter. Das Wetter kann von Jahr zu Jahr abweichen.</p>
  <nav class="month-nav" aria-label="Weitere Monate">
    <a href="../{MONTH_SLUGS[prev_i]}/">← {MONTHS[prev_i]}</a>
    <a href="../{MONTH_SLUGS[next_i]}/">{MONTHS[next_i]} →</a>
  </nav>
</section>"""
    names = ", ".join(d["name"] for d in good)
    write(f"reisekalender/{slug}/index.html", page(
        f"reisekalender/{slug}/index.html", f"Wohin im {m}? Reiseziele mit Sonne | {SITE['name']}",
        f"Wohin im {m}: {names} – beste Reisezeit, Flugzeit und ausgewählte Hotels.", body, "kalender"))


# ---------------------------------------------------------------- Startseite
def build_home():
    horizon = "".join(
        f'<a class="tile{tile_class(d)}" href="reiseziele/{d["slug"]}/" style="{tile_style(d, "")}">'
        f'<span>{d["name"]}</span></a>' for d in DESTINATIONS)
    rows = "".join(f"""
    <li class="dest">
      <a class="dest-link" href="reiseziele/{d['slug']}/">
        <span class="swatch" style="--sky:{d['sky']};--land:{d['land']}" aria-hidden="true"></span>
        <h3>{d['name']}</h3>
        <p>{d['short']}</p>
      </a>
      {months_bar(d['best'], compact=True)}
    </li>""" for d in DESTINATIONS)

    # Hotel-Auswahl: je Reiseziel das erste Hotel
    picks = "".join(f"""
      <li><a href="reiseziele/{d['slug']}/{d['hotels'][0]['id']}/">
        <span class="swatch small" style="--sky:{d['sky']};--land:{d['land']}" aria-hidden="true"></span>
        <span><strong>{E(d['hotels'][0]['name'])}</strong><br><small>{E(d['hotels'][0]['place'])} · {d['name']}</small></span>
      </a></li>""" for d in DESTINATIONS)

    body = f"""
<section class="hero">
  <div class="horizon">{horizon}</div>
  <div class="hero-text">
    <h1>Wohin geht die nächste Reise?</h1>
    <p class="lead">Wir stellen Reiseziele vor, zeigen dir die beste Reisezeit auf einen Blick und sammeln Hotels, die sich wirklich lohnen – von den Kanaren bis nach Thailand.</p>
  </div>
</section>

<section class="index" id="reiseziele" aria-labelledby="h-ziele">
  <div class="section-head">
    <h2 id="h-ziele">Reiseziele</h2>
    <p class="legend"><span class="m on" aria-hidden="true"></span> Beste Reisezeit</p>
  </div>
  <ul class="dest-list">{rows}
  </ul>
</section>

<section class="picks" aria-labelledby="h-picks">
  <div class="section-head">
    <h2 id="h-picks">Ausgewählte Hotels</h2>
    <a class="more" href="reisekalender/">Zum Reisekalender →</a>
  </div>
  <ul class="pick-list">{picks}
  </ul>
</section>

<section class="picks" aria-labelledby="h-art">
  <div class="section-head">
    <h2 id="h-art">Aus dem Ratgeber</h2>
    <a class="more" href="ratgeber/">Alle Hotel-Listen →</a>
  </div>
  {article_teasers(ARTICLES[:4], "")}
</section>

<section class="method">
  <h2>So wählen wir aus</h2>
  <div class="method-grid">
    <div><h3>Lage</h3><p>Strand, Ruhe, Ausflugsziele: Wir achten darauf, dass die Lage zum Reiseziel und zur Urlaubsart passt.</p></div>
    <div><h3>Ausstattung</h3><p>Pool, Spa, Kinderclub oder Adults only – jedes Hotel ist mit seinen wichtigsten Merkmalen beschrieben.</p></div>
    <div><h3>Ehrliche Angaben</h3><p>Wir schreiben nur, was sich belegen lässt. Preise nennen wir nicht, weil sie sich täglich ändern.</p></div>
  </div>
</section>
"""
    write("index.html", page("index.html",
          f"{SITE['name']} – {SITE['claim']}",
          "Reiseziele mit bester Reisezeit und ausgewählten Hotels: Kanaren, Mallorca, Karibik, Malediven, Ägypten und Thailand.",
          body, "home"))


# ---------------------------------------------------------------- Reiseziele
def build_destination(d):
    intro = "".join(f"<p>{p}</p>" for p in d["intro"])
    fits = "".join(f"<li>{E(f)}</li>" for f in d["fits"])
    tips = "".join(f"<li>{E(t)}</li>" for t in d["tips"])
    hotels = "".join(hotel_card(d, h, "") for h in d["hotels"])
    # Alte Sprungmarken (#hotel-<id>) auf die Hotelseite umleiten.
    ids = json.dumps([h["id"] for h in d["hotels"]])
    jump = ("<script>(function(){var m=location.hash.match(/^#hotel-([a-z0-9-]+)$/);"
            f"if(m&&{ids}.indexOf(m[1])>=0)location.replace(m[1]+'/');}})();</script>")
    others = "".join(
        f'<a class="tile{tile_class(o)}" href="../{o["slug"]}/" style="{tile_style(o, "../../")}"><span>{o["name"]}</span></a>'
        for o in DESTINATIONS if o["slug"] != d["slug"])
    credit = (f'<p class="photo-credit">Foto: {E(d["photo_credit"])}</p>'
              if photo(d["slug"]) and d.get("photo_credit") else "")
    og = f"{SITE['url']}/bilder/{photo(d['slug'])}" if photo(d["slug"]) else ""
    ids_here = {h["id"] for h in d["hotels"]}
    arts = [a for a in ARTICLES if any(i in ids_here for i, _ in a["hotels"])]
    art_block = (f'\n<section class="picks" aria-labelledby="h-art">\n  <h2 id="h-art">Ratgeber zu {d["name"]}</h2>\n  '
                 f'{article_teasers(arts, "../../")}\n</section>\n') if arts else ""
    body = f"""
<section class="dest-hero{tile_class(d)}" style="{tile_style(d, '../../')}">
  <p class="crumb"><a href="../../">Start</a> <span aria-hidden="true">/</span> Reiseziele</p>
  <h1>{d['name']}</h1>
  <p class="dest-sub">{d['short']}</p>
  {credit}
</section>

<div class="dest-body">
  <article class="prose">
    {intro}
    <h2>Gut zu wissen</h2>
    <ul class="tips">{tips}</ul>
  </article>
  <aside class="facts" aria-label="Auf einen Blick">
    <h2>Auf einen Blick</h2>
    <h3>Beste Reisezeit</h3>
    {months_bar(d['best'])}
    <h3>Flugzeit ab Deutschland</h3>
    <p class="mono">{d['flight']}</p>
    <h3>Passt gut für</h3>
    <ul class="fits">{fits}</ul>
  </aside>
</div>

<section class="hotels" aria-labelledby="h-hotels">
  <div class="section-head">
    <h2 id="h-hotels">Hotel-Tipps für {d['name']}</h2>
    <p class="note">Stand: {SITE['updated']}</p>
  </div>
  <ul class="hotel-list">{hotels}
  </ul>
  {jump}
</section>
{art_block}
<section class="others" aria-labelledby="h-others">
  <h2 id="h-others">Weitere Reiseziele</h2>
  <div class="horizon small">{others}</div>
</section>
"""
    write(f"reiseziele/{d['slug']}/index.html", page(
        f"reiseziele/{d['slug']}/index.html",
        f"{d['name']}: beste Reisezeit & Hotel-Tipps | {SITE['name']}",
        f"{d['name']} – {d['short']} Beste Reisezeit, Flugzeit und ausgewählte Hotels.",
        body, og_image=og))


# ---------------------------------------------------------------- Reisekalender
def build_calendar():
    head = "".join(f'<th scope="col"><a href="{MONTH_SLUGS[i]}/"><abbr title="Wohin im {m}?">{m[:3]}</abbr></a></th>'
                   for i, m in enumerate(MONTHS))
    rows = ""
    for d in DESTINATIONS:
        cells = "".join(
            f'<td class="{"on" if i + 1 in d["best"] else ""}">'
            f'<span class="sr">{"ideal" if i + 1 in d["best"] else "–"}</span></td>'
            for i in range(12))
        rows += f'<tr><th scope="row"><a href="../reiseziele/{d["slug"]}/">{d["name"]}</a></th>{cells}</tr>'

    by_month = ""
    for i, m in enumerate(MONTHS):
        ziele = [d for d in DESTINATIONS if i + 1 in d["best"]]
        links = ", ".join(f'<a href="../reiseziele/{d["slug"]}/">{d["name"]}</a>' for d in ziele) or "–"
        by_month += f'<li><strong><a href="{MONTH_SLUGS[i]}/">{m}</a>:</strong> {links}</li>'

    body = f"""
<section class="plain">
  <h1>Reisekalender</h1>
  <p class="lead">Welches Reiseziel passt in welchen Monat? Die markierten Monate sind die beste Reisezeit für Badeurlaub.</p>
  <div class="table-wrap">
    <table class="calendar">
      <caption class="sr">Beste Reisezeit nach Reiseziel und Monat</caption>
      <thead><tr><th scope="col">Reiseziel</th>{head}</tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
  <h2>Nach Monat</h2>
  <ul class="by-month">{by_month}</ul>
  <p class="note">Die Angaben sind Richtwerte für Sonne und Badewetter. Das Wetter kann von Jahr zu Jahr abweichen.</p>
</section>
"""
    write("reisekalender/index.html", page(
        "reisekalender/index.html",
        f"Reisekalender: Wohin in welchem Monat? | {SITE['name']}",
        "Beste Reisezeit für Kanaren, Mallorca, Karibik, Malediven, Ägypten und Thailand auf einen Blick.",
        body, "kalender"))


# ---------------------------------------------------------------- Textseiten
def build_static():
    about = f"""
<section class="plain prose">
  <h1>Über uns</h1>
  <p class="lead">{SITE['name']} hilft dir, das passende Reiseziel und ein gutes Hotel zu finden – ohne stundenlanges Vergleichen.</p>
  <p>Hinter {SITE['name']} steckt Steffen, Reisefan aus Norddeutschland. Die Idee: Reiseziele kurz und ehrlich vorstellen, die beste Reisezeit auf einen Blick zeigen und Hotels sammeln, bei denen Lage und Ausstattung zur Urlaubsart passen.</p>
  <h2>Wie wir auswählen</h2>
  <p>Wir stellen ausschließlich real existierende Hotels vor und beschreiben nur Merkmale, die sich belegen lassen. Preise nennen wir nicht, weil sie sich ständig ändern. Aktuelle Preise und Verfügbarkeit siehst du direkt beim Buchungsportal.</p>
  <h2>Wie sich die Seite finanziert</h2>
  <p>Links zu Buchungsportalen können Affiliate-Links sein. Buchst du darüber, erhalten wir eventuell eine Provision vom Partner. Für dich ändert sich am Preis nichts. So bleibt die Seite kostenlos und ohne Werbebanner. Die Provision hat keinen Einfluss darauf, welche Hotels wir vorstellen.</p>
  <h2>Kontakt</h2>
  <p><a href="mailto:info@urlaubshorizont.de">info@urlaubshorizont.de</a></p>
</section>"""
    write("ueber-uns/index.html", page("ueber-uns/index.html", f"Über uns | {SITE['name']}",
          f"Wer hinter {SITE['name']} steckt und wie die Hotel-Tipps entstehen.", about, "about"))

    imp = """
<section class="plain prose legal">
  <h1>Impressum</h1>
  <h2>Angaben gemäß § 5 DDG</h2>
  <p>Steffen Witte<br>Wilhelmstraße 25b<br>25336 Elmshorn<br>Deutschland</p>
  <h2>Kontakt</h2>
  <p>E-Mail: <a href="mailto:info@urlaubshorizont.de">info@urlaubshorizont.de</a></p>
  <h2>Umsatzsteuer</h2>
  <p>Gemäß § 19 UStG wird keine Umsatzsteuer berechnet.</p>
  <h2>Verantwortlich für den Inhalt</h2>
  <p>Steffen Witte, Anschrift wie oben</p>
  <h2>Haftung für Links</h2>
  <p>Diese Website enthält Links zu externen Websites Dritter, auf deren Inhalte wir keinen Einfluss haben. Für die Inhalte der verlinkten Seiten ist stets der jeweilige Anbieter verantwortlich.</p>
</section>"""
    write("impressum/index.html", page("impressum/index.html", f"Impressum | {SITE['name']}", "Impressum", imp))

    ds = f"""
<section class="plain prose legal">
  <h1>Datenschutzerklärung</h1>
  <h2>Verantwortlicher</h2>
  <p>Steffen Witte, Wilhelmstraße 25b, 25336 Elmshorn, E-Mail: <a href="mailto:info@urlaubshorizont.de">info@urlaubshorizont.de</a></p>
  <h2>Hosting</h2>
  <p>Diese Website wird bei GitHub Pages gehostet, einem Dienst der GitHub, Inc., USA. Beim Aufruf der Seiten verarbeitet GitHub technisch notwendige Daten, insbesondere die IP-Adresse, Datum und Uhrzeit des Zugriffs sowie Browserinformationen, um die Website auszuliefern und ihre Sicherheit zu gewährleisten. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO; unser berechtigtes Interesse liegt in einer sicheren und zuverlässigen Bereitstellung der Website. Dabei kann eine Übermittlung in die USA stattfinden. GitHub ist unter dem EU-US Data Privacy Framework zertifiziert; die Übermittlung stützt sich auf den Angemessenheitsbeschluss der EU-Kommission (Art. 45 DSGVO).</p>
  <h2>Keine Cookies, kein Tracking</h2>
  <p>Diese Website setzt selbst keine Cookies, verwendet keine Analyse- oder Trackingdienste und lädt keine Schriften oder Skripte von fremden Servern.</p>
  <h2>Links zu Buchungsportalen</h2>
  <p>Diese Website enthält Links zu Buchungsportalen, die Affiliate-Links sein können. Erst wenn du einen solchen Link anklickst, wirst du zur Website des Anbieters weitergeleitet. Dort kann der Anbieter beziehungsweise ein Partnernetzwerk Cookies oder ähnliche Technologien einsetzen, um eine Buchung zuzuordnen. Dafür ist der jeweilige Anbieter verantwortlich; es gelten dessen Datenschutzhinweise.</p>
  <h2>Pinterest</h2>
  <p>Wir verlinken gegebenenfalls auf unser Profil bei Pinterest. Es handelt sich um einen einfachen Link ohne eingebettete Inhalte. Daten werden erst übertragen, wenn du den Link anklickst.</p>
  <h2>Deine Rechte</h2>
  <p>Du hast das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit sowie Widerspruch gegen die Verarbeitung (Art. 15 bis 21 DSGVO). Außerdem kannst du dich bei einer Datenschutz-Aufsichtsbehörde beschweren.</p>
  <p>Stand: {SITE['updated']}</p>
</section>"""
    write("datenschutz/index.html", page("datenschutz/index.html", f"Datenschutz | {SITE['name']}", "Datenschutzerklärung", ds))

    notfound = """
<section class="plain">
  <h1>Hier geht's nicht weiter</h1>
  <p class="lead">Diese Seite gibt es nicht (mehr). Vielleicht findest du dein nächstes Reiseziel auf der Startseite.</p>
  <p><a class="btn" href="/">Zur Startseite</a></p>
</section>"""
    write("404.html", page("404.html", f"Seite nicht gefunden | {SITE['name']}", "Seite nicht gefunden", notfound))


# ---------------------------------------------------------------- Technik
def build_tech():
    # favicon.svg, apple-touch-icon.png und logo/ erzeugt _src/make_logo.py
    write("CNAME", SITE["domain"] + "\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE['url']}/sitemap.xml\n")
    urls = ["", "reisekalender/", "ueber-uns/", "impressum/", "datenschutz/"] + \
           [f"reiseziele/{d['slug']}/" for d in DESTINATIONS] + \
           [f"reiseziele/{d['slug']}/{h['id']}/" for d in DESTINATIONS for h in d["hotels"] if h.get("index")] +            ["ratgeber/"] + [f"ratgeber/{a['slug']}/" for a in ARTICLES] +            [f"reisekalender/{m}/" for m in MONTH_SLUGS]
    sm = "".join(f"  <url><loc>{SITE['url']}/{u}</loc></url>\n" for u in urls)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n'
          f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{sm}</urlset>\n')


if __name__ == "__main__":
    process_photos()
    check_articles()
    removed = update_registry()
    build_home()
    for d in DESTINATIONS:
        build_destination(d)
        for h in d["hotels"]:
            build_hotel(d, h)
    for entry in removed:
        build_removed(entry)
        print(f"Hinweis: {entry} ist nicht mehr in content.py – Adresse leitet aufs Reiseziel weiter.")
    build_calendar()
    for i in range(12):
        build_month(i)
    for a in ARTICLES:
        build_article(a)
    build_article_index()
    build_static()
    build_tech()
    print("Fertig:", OUT)
