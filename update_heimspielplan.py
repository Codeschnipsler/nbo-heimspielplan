"""
Aktualisiert die Datendatei (heimspiele.json) fuer die NBO-Heimspielplan-Webseite.

Uebernimmt die Abruf-Logik aus save_newbasket_schedules_liga.py (REST-API +
ICS-Kalender von basketball-bund.net), ergaenzt sie um:
  - Heim/Auswaerts-Erkennung je Spiel
  - Filterung auf echte Heimspiele
  - Ausschluss von Spielen ohne benannten Gegner (Platzhalter/leer)
  - Export als schlankes JSON, das die Webseite per fetch() laedt

Gedacht fuer den woechentlichen Lauf per GitHub Actions (siehe
.github/workflows/update-heimspielplan.yml).
"""

from urllib.request import Request, urlopen
from urllib.parse import urlencode
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import json
import re

BASE = 'https://www.basketball-bund.net/'

# (Team-Kuerzel, Liga-/Wettbewerbs-ID, Modus)
ITEMS = [
    ('D1', '55746', 'internal'),
    ('D2', '500300', 'number'),
    ('D3', '500330', 'number'),
    ('U18', '5001256', 'number'),
    ('U16', '5001263', 'number'),
    ('U14.1', '5001273', 'number'),
    ('U14.2', '5001279', 'number'),
    ('U14.3', '520004', 'number'),
    ('U14.o', '509314', 'number'),
    ('U12.1', '5001286', 'number'),
    ('U12.2', '5001287', 'number'),
    ('U10', '5001560', 'number'),
]

# Kurzanzeige der Liga je Wettbewerbs-ID (unabhaengig vom exakten API-Namenstext)
LIGA_SHORT = {
    '55746': '2. Bundesliga Nord',
    '500300': 'Regionalliga',
    '500330': 'Landesliga 3',
    '5001256': 'Jugendoberliga 2',
    '5001263': '2. Regionalliga',
    '5001273': '2. Regionalliga',
    '5001279': 'Jugendoberliga 3',
    '520004': 'Kreisliga Gr. B',
    '509314': 'Kreisliga Essen',
    '5001286': 'Jugendoberliga 2',
    '5001287': 'Jugendoberliga 3',
    '5001560': 'Jugendoberliga 1',
}

TEAM_LABEL = {
    'D1': '1. Damen', 'D2': '2. Damen', 'D3': '3. Damen',
    'U18': 'U18', 'U16': 'U16',
    'U14.1': 'U14 I', 'U14.2': 'U14 II', 'U14.3': 'U14 III', 'U14.o': 'U14 o',
    'U12.1': 'U12 I', 'U12.2': 'U12 II', 'U10': 'U10',
}

OUT_PATH = Path(__file__).resolve().parent / 'heimspiele.json'
OUT_PATH_AWAY = Path(__file__).resolve().parent / 'auswaertsspiele.json'
OUT_PATH_RESULTS = Path(__file__).resolve().parent / 'ergebnisse.json'


def get(url):
    with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=45) as response:
        return response.read()


def unfold_ics(text):
    return re.sub(r'\n[ \t]', '', text.replace('\r\n', '\n'))


def parse_ics(data):
    text = unfold_ics(data.decode('utf-8-sig', errors='replace'))
    events = []
    for block in text.split('BEGIN:VEVENT')[1:]:
        block = block.split('END:VEVENT', 1)[0]
        event = {}
        for line in block.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.split(';', 1)[0]
                event[key] = value.replace('\\,', ',').replace('\\;', ';').replace('\\\\', '\\')
        if event.get('SUMMARY'):
            events.append(event)
    return events


def parse_teams(summary):
    """'Heim-Gast, CODE (SpNr. n)' -> Teilstring 'Heim-Gast' (oder None)."""
    m = re.match(r'^(.*),\s*([A-Za-z0-9\-]*)\s*\(SpNr\.\s*(\d+)\)\s*$', summary)
    return m.group(1) if m else None


def split_home_away(teams_part, own_name):
    if teams_part.startswith(own_name + '-'):
        return own_name, teams_part[len(own_name) + 1:], 'home'
    if teams_part.endswith('-' + own_name):
        return teams_part[:-(len(own_name) + 1)], own_name, 'away'
    return None, None, None


def dtstart_to_iso(value):
    # basketball-bund liefert DTSTART als UTC, z.B. 20260913T220000Z
    dt = datetime.strptime(value, '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
    return dt.isoformat()


def is_named_opponent(name):
    if not name or not name.strip():
        return False
    if 'platzhalter' in name.lower():
        return False
    return True


def fetch_team_events(team, identifier, mode):
    if mode == 'internal':
        liga_id = identifier
        ms_id = '463431'
        own_name = 'New Basket 92 Oberhausen e.V.'
    else:
        response = json.loads(get(f'{BASE}rest/competition/number/{identifier}/actual?rangeDays=1000'))
        if response.get('status') != '0':
            raise RuntimeError(f'{team}: REST status {response.get("status")}')
        league_data = response['data']['ligaData']
        liga_id = str(league_data['ligaId'])
        candidates = []
        for match in response['data'].get('matches', []):
            for side in ('homeTeam', 'guestTeam'):
                team_data = match.get(side) or {}
                name = team_data.get('teamname', '')
                if 'new basket' in name.lower():
                    candidates.append(team_data)
        if not candidates:
            raise RuntimeError(f'{team}: kein New-Basket-Team in Liga {identifier}')
        ms_id = str(candidates[0]['teamCompetitionId'])
        own_name = candidates[0]['teamname']

    calendar_url = BASE + 'servlet/KalenderDienst?' + urlencode({
        'typ': '2', 'liga_id': liga_id, 'ms_liga_id': ms_id, 'spt': '-1'
    })
    events = parse_ics(get(calendar_url))
    return events, own_name


def kickoff_to_iso(date_str, time_str):
    # kickoffDate/kickoffTime sind lokale Berliner Zeit, nicht UTC
    naive = datetime.strptime(f'{date_str} {time_str}', '%Y-%m-%d %H:%M')
    local = naive.replace(tzinfo=ZoneInfo('Europe/Berlin'))
    return local.astimezone(timezone.utc).isoformat()


def fetch_team_results(team, identifier, mode):
    if mode != 'number':
        # Fuer die 1. Damen liefert dieser REST-Endpunkt aktuell keine
        # brauchbare Antwort (siehe Diagnose) - daher hier ausgelassen.
        return []

    response = json.loads(get(f'{BASE}rest/competition/number/{identifier}/actual?rangeDays=1000'))
    if response.get('status') != '0':
        raise RuntimeError(f'{team}: REST status {response.get("status")} (Ergebnisse)')
    data = response.get('data') or {}
    matches = data.get('matches') or []

    results = []
    for match in matches:
        home = match.get('homeTeam') or {}
        guest = match.get('guestTeam') or {}
        home_name = home.get('teamname', '')
        guest_name = guest.get('teamname', '')

        if 'new basket' in home_name.lower():
            role, own_name, opponent = 'home', home_name, guest_name
        elif 'new basket' in guest_name.lower():
            role, own_name, opponent = 'away', guest_name, home_name
        else:
            continue

        if match.get('abgesagt'):
            continue
        result = match.get('result')
        if not result or ':' not in result:
            continue
        try:
            score_home, score_guest = (int(x) for x in result.split(':', 1))
        except ValueError:
            continue
        own_score, opp_score = (score_home, score_guest) if role == 'home' else (score_guest, score_home)

        try:
            iso = kickoff_to_iso(match.get('kickoffDate', ''), match.get('kickoffTime', ''))
        except ValueError:
            continue

        results.append({
            'liga': LIGA_SHORT.get(identifier, identifier),
            'team': TEAM_LABEL[team],
            'gegner': opponent.strip(),
            'heimAuswaerts': 'Heim' if role == 'home' else 'Auswärts',
            'eigenePunkte': own_score,
            'gegnerPunkte': opp_score,
            'sieg': own_score > opp_score,
            'datetime': iso,
        })
    return results


def main():
    home_games = []
    away_games = []
    results = []
    errors = []

    for team, identifier, mode in ITEMS:
        try:
            events, own_name = fetch_team_events(team, identifier, mode)
        except Exception as exc:  # weiter mit den anderen Teams, Fehler sammeln
            errors.append(f'{team}: {exc}')
            continue

        try:
            results.extend(fetch_team_results(team, identifier, mode))
        except Exception as exc:
            errors.append(f'{team} (Ergebnisse): {exc}')

        for event in events:
            summary = event.get('SUMMARY', '')
            teams_part = parse_teams(summary)
            if not teams_part:
                continue
            home, away, role = split_home_away(teams_part, own_name)
            if role is None:
                continue

            opponent = away if role == 'home' else home
            if not is_named_opponent(opponent):
                continue
            try:
                iso = dtstart_to_iso(event.get('DTSTART', ''))
            except ValueError:
                continue

            entry = {
                'liga': LIGA_SHORT.get(identifier, identifier),
                'team': TEAM_LABEL[team],
                'gegner': opponent.strip(),
                'ort': event.get('LOCATION', ''),
                'datetime': iso,
            }
            if role == 'home':
                home_games.append(entry)
            else:
                away_games.append(entry)

    home_games.sort(key=lambda g: g['datetime'])
    away_games.sort(key=lambda g: g['datetime'])
    results.sort(key=lambda g: g['datetime'], reverse=True)

    OUT_PATH.write_text(
        json.dumps(home_games, ensure_ascii=False, indent=1),
        encoding='utf-8',
    )
    OUT_PATH_AWAY.write_text(
        json.dumps(away_games, ensure_ascii=False, indent=1),
        encoding='utf-8',
    )
    OUT_PATH_RESULTS.write_text(
        json.dumps(results, ensure_ascii=False, indent=1),
        encoding='utf-8',
    )

    print(f'HEIMSPIELE={len(home_games)}')
    print(f'AUSWAERTSSPIELE={len(away_games)}')
    print(f'ERGEBNISSE={len(results)}')
    print(f'DATEIEN={OUT_PATH}, {OUT_PATH_AWAY}, {OUT_PATH_RESULTS}')
    if errors:
        print('FEHLER:')
        for line in errors:
            print(' -', line)
        # Ein Team-Fehler soll den woechentlichen Lauf nicht komplett scheitern lassen,
        # aber im Actions-Log sichtbar sein.


if __name__ == '__main__':
    main()
