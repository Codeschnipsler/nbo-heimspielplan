"""
Erzeugt die A3-Druckversion des NBO-Heimspiel-Posters (300dpi, 3508x4961px)
im selben Look wie das Instagram-Poster (poster.png).

Nutzt dieselbe Datenauswahl wie generate_poster.py, aber ein eigenes,
auf A3-Hochformat skaliertes Template (poster_template_a3.html) und ein
hochskaliertes Hintergrundfoto (court-photo-a3.jpg), damit bei der
groesseren Druckflaeche nichts verpixelt wirkt.

Ausgabe: poster_a3.png (3508x4961px, 300dpi A3-Hochformat)
"""

from pathlib import Path

from generate_poster import (
    BASE_DIR,
    D1_TEAM,
    TEAM_ORDER,
    load_games,
    build_d1_card,
    build_row,
)
from datetime import datetime
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo('Europe/Berlin')

TEMPLATE_PATH = BASE_DIR / 'poster_template_a3.html'
RENDERED_HTML_PATH = BASE_DIR / '_poster_a3_rendered.html'
OUT_PNG_PATH = BASE_DIR / 'poster_a3.png'

A3_WIDTH = 3508
A3_HEIGHT = 4961


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
        page = browser.new_page(viewport={'width': A3_WIDTH, 'height': A3_HEIGHT})
        page.goto(f'file://{RENDERED_HTML_PATH}')
        page.wait_for_timeout(400)  # Google Fonts laden lassen
        page.screenshot(path=str(OUT_PNG_PATH))
        browser.close()

    print(f'POSTER_A3_ERZEUGT={OUT_PNG_PATH.name}')
    print(f'D1_SPIELE={len(d1_games)}')
    print(f'WEITERE_ZEILEN={rows_html.count(chr(60)+"div class="+chr(34)+"row"+chr(34)+chr(62))}')


if __name__ == '__main__':
    main()
