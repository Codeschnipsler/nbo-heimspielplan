# nbo-heimspielplan

Heim- und Auswärtsspiele, Ergebnisse und Tabellen von New Basket '92 Oberhausen
in der Saison 2026/27 – automatisch von basketball-bund.net abgerufen und als
Webseite, Daten (JSON) und Poster bereitgestellt.

## Seiten

**Webseite**

- [Heimspielplan](https://codeschnipsler.github.io/nbo-heimspielplan/index.html)
- [Auswärtsspiele](https://codeschnipsler.github.io/nbo-heimspielplan/auswaerts.html)
- [Ergebnisse](https://codeschnipsler.github.io/nbo-heimspielplan/ergebnisse.html)
- [Tabellen](https://codeschnipsler.github.io/nbo-heimspielplan/tabellen.html)

**Tools**

- [Halle-Overlay](https://codeschnipsler.github.io/nbo-heimspielplan/overlay-roi.html)
- [Overlay-Simulation](https://codeschnipsler.github.io/nbo-heimspielplan/Simulation.html)
- [Spiel-Intro-Generator](https://codeschnipsler.github.io/nbo-heimspielplan/nbo_spiel_intro_generator.html)
- [Spiel-Intro-Generator Auswärtsspiele](https://codeschnipsler.github.io/nbo-heimspielplan/nbo_spiel_intro_generator_auswaerts.html)

**Poster**

- [Poster Instagram-Format](https://codeschnipsler.github.io/nbo-heimspielplan/poster.png)
- [Poster A3-Druck](https://codeschnipsler.github.io/nbo-heimspielplan/poster_a3.png)

Let's go NBO

## Ordnerstruktur

```
/                    Webseite, Poster und Tools (Adressen bitte nicht ändern,
                     sie sind in Overlays/Tools und anderen NBO-Seiten fest verlinkt)
  index.html           Heimspiele
  auswaerts.html       Auswärtsspiele
  ergebnisse.html      Ergebnisse
  tabellen.html        Tabellen
  poster.png           Poster Instagram-Format (automatisch erzeugt)
  poster_a3.png        Poster A3-Druck (automatisch erzeugt)
  overlay-roi.html,
  Simulation.html,
  nbo_spiel_intro_generator*.html   Tools (fest verlinkt, bleiben hier)

data/                Daten als JSON (siehe unten), öffentlich unter
                     https://codeschnipsler.github.io/nbo-heimspielplan/data/<datei>.json

scripts/             Python-Skripte, laufen per GitHub Actions
  update_heimspielplan.py   holt Spielplan, Ergebnisse, Tabellen -> data/*.json
  generate_poster.py        erzeugt poster.png
  generate_poster_a3.py     erzeugt poster_a3.png

poster/              Vorlagen und Bilder für die Poster
  poster_template*.html, court-photo*.jpg, logo-nbo-3d.png, event-ball.png
  special_event.txt    Text für den „Special Event“-Kreis (leer = kein Kreis)

img/                 Bilder der Webseite und Spieltags-Banner fürs Overlay
  D1_Spieltag_ohne_Sponsor.png   Banner 1. Damen ohne Sponsor
  D1_Spieltag_Sponsor.png        Banner mit Sponsor – nur an Sponsor-Spieltagen hochladen
  D1_Spieltag_Sponsor_dummy.png  Dummy-Version des Sponsor-Banners
  Jugend_Spieltag.png            Banner für alle anderen Teams
```

## Daten (JSON, im Ordner `data/`)

| Datei | Inhalt | Quelle |
|---|---|---|
| `heimspiele.json` | anstehende Heimspiele | automatisch |
| `auswaertsspiele.json` | anstehende Auswärtsspiele | automatisch |
| `ergebnisse.json` | letzte Ergebnisse | automatisch |
| `tabellen.json` | Ligatabellen | automatisch |
| `NBO_overview.json` | Gesamtübersicht für andere NBO-Aktivitäten | automatisch |
| `zusatzspiele.json` | Test-/Zusatzspiele (z. B. über `Simulation.html` gepflegt) | von Hand |
| `Kurznamen.json` | Kurznamen der Gegner fürs Scoreboard | von Hand |

## Automatische Abläufe (GitHub Actions)

| Workflow | Wann | Was |
|---|---|---|
| Heimspielplan aktualisieren | Mo + Fr früh, Sa + So alle 3 Std. | `scripts/update_heimspielplan.py`, committet die JSON-Dateien |
| Heimspiel-Poster aktualisieren | montags früh | `scripts/generate_poster*.py`, committet `poster.png` und `poster_a3.png` |

Beide lassen sich unter *Actions* auch von Hand starten („Run workflow“).

## Lokal ausführen

```
python scripts/update_heimspielplan.py
pip install playwright
playwright install chromium
python scripts/generate_poster.py
python scripts/generate_poster_a3.py
```
