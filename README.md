# urlaubshorizont.de

Statische Website für GitHub Pages: keine Cookies, kein Tracking, keine externen Schriften.

## Vor dem Livegang ausfüllen
1. `_src/content.py` → `pinterest` (Profil-Link), später `pinterest_verify` (Code zur Domain-Bestätigung)
2. `_src/build.py` → Platzhalter in eckigen Klammern: Über uns (Vorname, E-Mail), Impressum, Datenschutz
3. Impressum und Datenschutz rechtlich prüfen lassen, gelbe Hinweiskästen entfernen
4. Neu bauen: `python3 _src/build.py`

## Veröffentlichen
1. Öffentliches GitHub-Repository anlegen, den **Inhalt** dieses Ordners hochladen (inkl. `CNAME`)
2. Settings → Pages → Branch `main`, Ordner `/ (root)`; Custom Domain steht durch `CNAME` schon drin
3. DNS bei checkdomain: A-Einträge auf 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153;
   CNAME `www` → `DEINNAME.github.io`
4. Nach Ausstellung des Zertifikats „Enforce HTTPS“ aktivieren
5. Optional: `sitemap.xml` in der Google Search Console einreichen

## Fotos für die Reiseziele
1. Ein Foto pro Reiseziel nach `_src/fotos/` legen, benannt nach dem Reiseziel:
   `kanaren.jpg`, `mallorca.jpg`, `karibik.jpg`, `malediven.jpg`, `aegypten.jpg`, `thailand.jpg`
2. Einmalig `pip install pillow`, dann `python3 _src/build.py`
3. Der Generator verkleinert die Fotos auf max. 2000 px, entfernt alle Metadaten (GPS-Ort, Aufnahmedatum, Kamera)
   und legt sie unter `bilder/` ab. Nur dieser Ordner wird veröffentlicht, deine Originale bleiben privat.
- Querformat wirkt am besten, das Motiv sollte eher mittig liegen (der Rand wird je nach Bildschirm beschnitten).
- Gekaufte Bilder: Lizenz für Websites prüfen und Quelle bei Bedarf als `photo_credit` im Reiseziel eintragen.
- Fehlt ein Foto, erscheint automatisch die Farbfläche.

## Inhalte pflegen (auch für den Agenten)
- Alle Reiseziele und Hotels stehen in `_src/content.py`, Design in `_src/style.css`.
- Hotel-Link: Feld `booking` (Ländercode + Slug) erzeugt den direkten Link zur Booking.com-Hotelseite, noch ohne Affiliate-Tracking.
  Nach der Freigabe pro Hotel das Feld `link` mit dem CJ-Deeplink setzen; es hat Vorrang.
- Hotelbild: Feld `image` mit der Bild-URL aus dem Affiliate-Feed füllen. Ohne Bild erscheint die Farbfläche.
  Keine Hotelfotos von fremden Websites kopieren, die sind urheberrechtlich geschützt.
- Hotel-`id` nie ändern: Sie erzeugt die Sprungmarke `/reiseziele/<ziel>/#hotel-<id>` für Pins.
- Neues Reiseziel: Block in `DESTINATIONS` kopieren, anpassen, neu bauen. Seite, Navigation, Kalender und Sitemap entstehen automatisch.
- `_src/`, `_agent/`, `CLAUDE.md` und `README.md` werden von GitHub Pages nicht veröffentlicht (`_config.yml`). Keine `.nojekyll`-Datei anlegen.
- Für Claude Code: `CLAUDE.md` enthält Projektstand, Regeln und offene Entscheidungen, `_agent/PINS.md` die Pin-Pipeline.
