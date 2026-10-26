"""Website-Check für urlaubshorizont.de (nur Python-Standardbibliothek).

Prüft:
  1. Alle Pflichtseiten: Start, Reisekalender, Textseiten, jedes Reiseziel,
     jede je veröffentlichte Hotel-Adresse aus _src/hotel_ids.txt (Pin-Ziele!)
  2. Jede Hotelseite zeigt den Hotelnamen und einen Booking-Button
  3. Alle internen Links und Bilder auf allen Seiten (alle Seiten werden durchlaufen)
  4. Ratgeber-Artikel nennen nur vorhandene Hotels und verlinken deren Hotelseiten;
     Sitemap enthält nur Hotelseiten mit index=True
  5. Alle Adressen aus sitemap.xml
  6. Unbekannte Adressen liefern 404, http leitet auf https, www auf die Hauptdomain
  7. HTTPS-Zertifikat ist noch mindestens 14 Tage gültig

Booking.com-Links werden NICHT abgerufen: Booking blockt automatische Abrufe.
Das übernimmt nach der CJ-Freigabe der Feed-Abgleich.

Aufruf:
  python _src/check_site.py                       # Live-Website
  python _src/check_site.py --dir .               # lokal gebaute Dateien (ohne Schritt 6/7)
  python _src/check_site.py --report bericht.md   # zusätzlich Bericht als Markdown
Exit-Code 1, wenn Fehler gefunden wurden.
"""
import argparse
import datetime as dt
import os
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from content import SITE, DESTINATIONS  # noqa: E402

UA = "urlaubshorizont-website-check/1.0 (+https://urlaubshorizont.de)"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


OPENER = urllib.request.build_opener(NoRedirect)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.refresh = [], None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.links.append(("Link", a["href"], a.get("rel") or ""))
        elif tag in ("img", "script") and a.get("src"):
            self.links.append(("Bild" if tag == "img" else "Skript", a["src"], ""))
        elif tag == "link" and a.get("href") and a.get("rel") in ("icon", "stylesheet"):
            self.links.append(("Datei", a["href"], ""))
        elif tag == "meta" and (a.get("http-equiv") or "").lower() == "refresh":
            self.refresh = a.get("content", "").split("url=", 1)[-1].strip()


class Checker:
    def __init__(self, base, local_dir=None):
        self.base = base.rstrip("/") + "/"
        self.host = urllib.parse.urlparse(self.base).netloc
        self.dir = local_dir
        self.cache = {}
        self.errors, self.notes = [], []

    # -- Abruf ------------------------------------------------------------
    def fetch(self, url, follow=True):
        """-> (status, body, final_url, location)"""
        key = (url, follow)
        if key in self.cache:
            return self.cache[key]
        if self.dir:
            res = self._fetch_local(url)
        else:
            res = self._fetch_http(url, follow)
        self.cache[key] = res
        return res

    def _fetch_local(self, url):
        path = urllib.parse.unquote(urllib.parse.urlparse(url).path).lstrip("/")
        f = os.path.join(self.dir, path)
        if os.path.isdir(f):
            if not url.endswith("/"):
                return 301, "", url, url + "/"
            f = os.path.join(f, "index.html")
        if not os.path.isfile(f):
            return 404, "", url, None
        with open(f, encoding="utf-8", errors="replace") as fh:
            return 200, fh.read() if f.endswith((".html", ".xml", ".txt")) else "", url, None

    def _fetch_http(self, url, follow):
        for hop in range(6):
            for attempt in range(3):
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": UA})
                    with OPENER.open(req, timeout=20) as r:
                        ctype = r.headers.get("Content-Type", "")
                        body = r.read().decode("utf-8", "replace") if ("html" in ctype or "xml" in ctype) else ""
                        return r.status, body, url, None
                except urllib.error.HTTPError as e:
                    if e.code in (301, 302, 307, 308):
                        loc = urllib.parse.urljoin(url, e.headers.get("Location", ""))
                        if not follow:
                            return e.code, "", url, loc
                        url = loc
                        break
                    if e.code >= 500 and attempt < 2:
                        time.sleep(3)
                        continue
                    return e.code, "", url, None
                except (urllib.error.URLError, socket.timeout, ConnectionError) as e:
                    if attempt < 2:
                        time.sleep(3)
                        continue
                    return 0, str(getattr(e, "reason", e)), url, None
        return 0, "zu viele Weiterleitungen", url, None

    # -- Hilfen -----------------------------------------------------------
    def url(self, path):
        return urllib.parse.urljoin(self.base, path)

    def short(self, url):
        return url.replace(self.base, "/") if url.startswith(self.base) else url

    def err(self, msg):
        self.errors.append(msg)

    def expect_page(self, path, what):
        status, body, final, _ = self.fetch(self.url(path))
        if status != 200:
            self.err(f"{what} nicht erreichbar: `{self.short(self.url(path))}` (Status {status or body})")
            return None
        return body

    # -- Prüfungen --------------------------------------------------------
    def check_required(self):
        pages = {"": "Startseite", "reisekalender/": "Reisekalender", "ueber-uns/": "Über uns",
                 "impressum/": "Impressum", "datenschutz/": "Datenschutz"}
        for d in DESTINATIONS:
            pages[f"reiseziele/{d['slug']}/"] = f"Reiseziel {d['name']}"
        bodies = {p: self.expect_page(p, w) for p, w in pages.items()}

        live = {f"{d['slug']}/{h['id']}": (d, h) for d in DESTINATIONS for h in d["hotels"]}
        registry = os.path.join(HERE, "hotel_ids.txt")
        known = set(live)
        if os.path.exists(registry):
            with open(registry, encoding="utf-8-sig") as f:
                known |= {ln.strip() for ln in f if "/" in ln and not ln.lstrip().startswith("#")}
        missing_in_registry = set(live) - known
        if missing_in_registry:
            self.err("Hotel nicht im Register `_src/hotel_ids.txt` (Build nicht gelaufen?): "
                     + ", ".join(sorted(missing_in_registry)))

        for entry in sorted(known):
            path = f"reiseziele/{entry}/"
            if entry in live:
                d, h = live[entry]
                body = self.expect_page(path, f"Hotelseite {h['name']}")
                if body is None:
                    continue
                if h["name"].replace("&", "&amp;") not in body:
                    self.err(f"Hotelseite `/{path}` zeigt den Hotelnamen nicht an")
                if 'rel="sponsored nofollow noopener"' not in body:
                    self.err(f"Hotelseite `/{path}` hat keinen Buchungs-Button")
                bodies[path] = body
            else:
                body = self.expect_page(path, f"Weiterleitung für entferntes Hotel {entry}")
                if body is not None and 'http-equiv="refresh"' not in body:
                    self.err(f"`/{path}` sollte aufs Reiseziel weiterleiten, tut es aber nicht")
                else:
                    self.notes.append(f"`/{path}` leitet weiter (Hotel entfernt)")
        return {p: b for p, b in bodies.items() if b}

    def check_links(self, bodies):
        """Durchläuft alle internen Seiten (ausgehend von den Pflichtseiten) und prüft
        jeden internen Link, jedes Bild und jede Datei."""
        seen = {}          # Ziel -> (Art, erste Fundstelle)
        external = set()
        queue = [(self.url(p), b) for p, b in bodies.items()]
        crawled = {u for u, _ in queue}
        while queue:
            page_url, body = queue.pop(0)
            path = self.short(page_url)
            p = Links()
            p.feed(body)
            import re
            p.links += [("Schrift/Datei", u, "") for u in re.findall(r'url\("(/[^"]+)"\)', body)]
            for kind, href, rel in p.links:
                if href.startswith(("mailto:", "tel:", "javascript:", "#")):
                    continue
                target = urllib.parse.urljoin(page_url, href).split("#")[0]
                netloc = urllib.parse.urlparse(target).netloc
                if netloc != self.host:
                    external.add(target)
                    if "booking.com" in netloc and "sponsored" not in rel:
                        self.err(f"Booking-Link ohne rel=sponsored auf `{path}`")
                    continue
                if target in seen:
                    continue
                seen[target] = (kind, path)
                status, tbody, _, _ = self.fetch(target)
                if status != 200:
                    self.err(f"{kind} kaputt auf `{path}`: `{self.short(target)}` (Status {status or tbody})")
                elif kind == "Link" and target not in crawled and (target.endswith("/") or target.endswith(".html")):
                    crawled.add(target)
                    queue.append((target, tbody))
        self.crawled = crawled
        self.notes.append(f"{len(crawled)} Seiten durchlaufen, {len(seen)} interne Adressen geprüft, "
                          f"{len(external)} externe Links (Booking) nicht abgerufen")

    def check_rules(self):
        """Inhaltliche Regeln: Ratgeber-Artikel und Hotelseiten."""
        try:
            from content import ARTICLES
        except ImportError:
            ARTICLES = []
        live = {h["id"]: d for d in DESTINATIONS for h in d["hotels"]}
        for a in ARTICLES:
            path = f"ratgeber/{a['slug']}/"
            body = self.expect_page(path, f"Ratgeber-Artikel {a['title']}")
            for hid, _ in a["hotels"]:
                if hid not in live:
                    self.err(f"Artikel `/{path}` nennt Hotel `{hid}`, das nicht mehr auf der Website ist")
                elif body is not None and f"/{live[hid]['slug']}/{hid}/" not in body:
                    self.err(f"Artikel `/{path}` verlinkt die Hotelseite von `{hid}` nicht")
        st, sm, _, _ = self.fetch(self.url("sitemap.xml"))
        for d in DESTINATIONS:
            for h in d["hotels"]:
                in_sm = f"/reiseziele/{d['slug']}/{h['id']}/<" in sm
                if bool(h.get("index")) != in_sm:
                    self.err(f"Hotel `{h['id']}`: Sitemap passt nicht zur Einstellung index={bool(h.get('index'))}")

    def check_sitemap(self):
        status, body, _, _ = self.fetch(self.url("sitemap.xml"))
        if status != 200:
            self.err(f"sitemap.xml nicht erreichbar (Status {status})")
            return
        import re
        locs = re.findall(r"<loc>([^<]+)</loc>", body)
        for loc in locs:
            if self.dir:
                loc = self.url(urllib.parse.urlparse(loc).path.lstrip("/"))
            st, b, _, _ = self.fetch(loc)
            if st != 200:
                self.err(f"Adresse aus sitemap.xml nicht erreichbar: `{self.short(loc)}` (Status {st or b})")
        self.notes.append(f"{len(locs)} Adressen in sitemap.xml")

    def check_server(self):
        st, _, _, _ = self.fetch(self.url("diese-seite-gibt-es-nicht-4711/"))
        if st != 404:
            self.err(f"Unbekannte Adresse liefert Status {st} statt 404")
        if self.dir:
            return
        domain = self.host
        for src, want in ((f"http://{domain}/", f"https://{domain}/"),
                          (f"https://www.{domain}/", f"https://{domain}/")):
            st, _, _, loc = self.fetch(src, follow=False)
            if st not in (301, 308) or loc != want:
                self.err(f"`{src}` sollte auf `{want}` weiterleiten (Status {st}, Ziel {loc})")
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=15) as s:
                with ctx.wrap_socket(s, server_hostname=domain) as tls:
                    cert = tls.getpeercert()
            end = dt.datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            days = (end - dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)).days
            if days < 14:
                self.err(f"HTTPS-Zertifikat läuft in {days} Tagen ab ({end:%d.%m.%Y})")
            else:
                self.notes.append(f"HTTPS-Zertifikat gültig bis {end:%d.%m.%Y}")
        except Exception as e:  # noqa: BLE001
            self.err(f"HTTPS-Zertifikat nicht prüfbar: {e}")

    def run(self):
        bodies = self.check_required()
        self.check_links(bodies)
        self.check_rules()
        self.check_sitemap()
        self.check_server()
        return not self.errors

    def report(self):
        when = dt.datetime.now().strftime("%d.%m.%Y %H:%M")
        src = f"lokaler Ordner `{self.dir}`" if self.dir else self.base
        lines = [f"Geprüft: {src} am {when}", ""]
        if self.errors:
            lines += [f"**{len(self.errors)} Problem(e) gefunden:**", ""]
            lines += [f"- [ ] {e}" for e in self.errors]
        else:
            lines += ["**Alles in Ordnung.**"]
        lines += ["", "<details><summary>Details</summary>", ""]
        lines += [f"- {n}" for n in self.notes] + ["", "</details>"]
        return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=SITE["url"])
    ap.add_argument("--dir", help="lokal gebaute Website prüfen statt live")
    ap.add_argument("--report", help="Bericht zusätzlich in diese Datei schreiben")
    a = ap.parse_args()
    c = Checker(a.base, os.path.abspath(a.dir) if a.dir else None)
    ok = c.run()
    text = c.report()
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(text)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
