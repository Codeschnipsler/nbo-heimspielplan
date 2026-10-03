"""
Erzeugt das NBO-Heimspiel-Poster (PNG) aus heimspiele.json.

Inhalt des Posters:
  - Oben: die naechsten ZWEI Heimspiele der 1. Damen, gross hervorgehoben.
  - Darunter: je EINE Zeile pro anderer Mannschaft mit deren naechstem
    Heimspiel (Mannschaft / Gegner / Uhrzeit).

Ablauf:
  1. heimspiele.json einlesen (von update_heimspielplan.py erzeugt).
  2. Passende Spiele auswaehlen und in poster_template.html einsetzen.
  3. Die ausgefuellte HTML-Datei mit Playwright (Chromium) als PNG
     rendern (1080x1350 - Instagram-Hochformat, auch als Story/Feed
     verwendbar).

Ausgabe: poster.png (im selben Verzeichnis)

Abhaengigkeit: playwright (muss vor dem Lauf installiert sein, siehe
Workflow: `pip install playwright` + `playwright install --with-deps chromium`).
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent
HEIMSPIELE_PATH = BASE_DIR / 'heimspiele.json'
TEMPLATE_PATH = BASE_DIR / 'poster_template.html'
RENDERED_HTML_PATH = BASE_DIR / '_poster_rendered.html'
OUT_PNG_PATH = BASE_DIR / 'poster.png'

D1_TEAM = '1. Damen'

# Reihenfolge, in der die "weiteren" Mannschaften aufgelistet werden,
# falls sie ein anstehendes Heimspiel haben.
TEAM_ORDER = [
    '2. Damen', '3. Damen', 'U18', 'U16',
    'U14 I', 'U14 II', 'U14 III', 'U14 o',
    'U12 I', 'U12 II', 'U10',
]

BERLIN = ZoneInfo('Europe/Berlin')

WEEKDAYS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']


def load_games():
    games = json.loads(HEIMSPIELE_PATH.read_text(encoding='utf-8'))
    now = datetime.now(timezone.utc)
    upcoming = []
    for g in games:
        try:
            dt = datetime.fromisoformat(g['datetime'])
        except ValueError:
            continue
        if dt >= now:
            g = dict(g)
            g['_dt'] = dt
            upcoming.append(g)
    upcoming.sort(key=lambda g: g['_dt'])
    return upcoming


def fmt_datum(dt_utc):
    local = dt_utc.astimezone(BERLIN)
    wd = WEEKDAYS[local.weekday()]
    return f"{wd}, {local.day:02d}.{local.month:02d}.{local.year}"


def fmt_zeit(dt_utc):
    local = dt_utc.astimezone(BERLIN)
    return f"{local.hour:02d}:{local.minute:02d}"


def ort_kurz(ort):
    if not ort:
        return ''
    return ort.split(',')[0].strip()


def fmt_datum_kurz(dt_utc):
    local = dt_utc.astimezone(BERLIN)
    wd = WEEKDAYS[local.weekday()]
    return f"{wd}, {local.day:02d}.{local.month:02d}."


def build_d1_card(game, index):
    datum = fmt_datum(game['_dt'])
    zeit = fmt_zeit(game['_dt'])
    ort = ort_kurz(game.get('ort', ''))
    badge = 'NÄCHSTES SPIEL' if index == 0 else 'DANACH'
    return f"""
      <div class="d1-card">
        <div class="badge">{badge}</div>
        <div class="vs"><span class="own">New Basket '92</span> vs. {game['gegner']}</div>
        <div class="meta">
          <div class="meta-row"><span class="date-big">{datum}</span></div>
          <div class="meta-row muted"><span class="time-small">{zeit} Uhr &middot; Tip-Off</span></div>
          <div class="meta-row muted">{ort}</div>
        </div>
      </div>
    """


def build_row(team_label, game):
    datum = fmt_datum_kurz(game['_dt'])
    zeit = fmt_zeit(game['_dt'])
    return f"""
      <div class="row">
        <div class="team">{team_label}</div>
        <div class="when">
          <div class="datum-big">{datum}</div>
          <div class="zeit-small">{zeit} Uhr</div>
        </div>
        <div class="gegner">{game['gegner']}</div>
      </div>
    """


def main():
    upcoming = load_games()

    d1_games = [g for g in upcoming if g['team'] == D1_TEAM][:2]
    cards_html = ''.join(build_d1_card(g, i) for i, g in enumerate(d1_games))
    if not cards_html:
        cards_html = '<div class="d1-card"><div class="vs">Aktuell keine Termine</div></div>'

    rows_html = ''
    for team_label in TEAM_ORDER:
        next_game = next((g for g in upcoming if g['team'] == team_label), None)
        if next_game:
            rows_html += build_row(team_label, next_game)

    stand = datetime.now(BERLIN).strftime('Stand: %d.%m.%Y')

    html = TEMPLATE_PATH.read_text(encoding='utf-8')
    html = html.replace('<!--D1CARD1-->\n      <!--D1CARD2-->', cards_html)
    html = html.replace('<!--ROWS-->', rows_html)
    html = html.replace('<!--STAND-->', stand)

    RENDERED_HTML_PATH.write_text(html, encoding='utf-8')

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1080, 'height': 1350})
        page.goto(f'file://{RENDERED_HTML_PATH}')
        page.wait_for_timeout(300)  # Google Fonts laden lassen
        page.screenshot(path=str(OUT_PNG_PATH))
        browser.close()

    print(f'POSTER_ERZEUGT={OUT_PNG_PATH.name}')
    print(f'D1_SPIELE={len(d1_games)}')
    print(f'WEITERE_ZEILEN={rows_html.count(chr(60)+"div class="+chr(34)+"row"+chr(34)+chr(62))}')


if __name__ == '__main__':
    main()
