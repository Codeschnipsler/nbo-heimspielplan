"""
Einmaliges Diagnose-Skript: zeigt die rohe Struktur eines Spiels aus der
basketball-bund.net REST-API, damit wir sehen, wie das Ergebnis-Feld heisst.

Aufruf: python diagnose_ergebnisse.py
Ausgabe einfach hier zurueckmelden (z.B. als Log-Ausschnitt).
"""

from urllib.request import Request, urlopen
import json

BASE = 'https://www.basketball-bund.net/'

# 1. Damen laeuft ueber liga_id 55746 (bei uns intern gefuehrt) -
# wir rufen trotzdem den regulaeren REST-Endpunkt ab, nur fuer die Diagnose.
IDENTIFIER = '55746'


def get(url):
    with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=45) as response:
        return response.read()


def main():
    url = f'{BASE}rest/competition/number/{IDENTIFIER}/actual?rangeDays=1000'
    response = json.loads(get(url))
    matches = response.get('data', {}).get('matches', [])
    print(f'Anzahl Spiele in der Antwort: {len(matches)}')

    # Ein bereits gespieltes Spiel suchen (falls erkennbar), sonst einfach das erste
    sample = None
    for m in matches:
        # irgendein Hinweis auf ein Ergebnis-Feld, unabhaengig vom genauen Namen
        keys_lower = ' '.join(k.lower() for k in m.keys())
        if any(hint in keys_lower for hint in ['result', 'punkte', 'score', 'ergebnis']):
            sample = m
            break
    if sample is None:
        sample = matches[0] if matches else None

    if sample is None:
        print('Keine Spiele in der Antwort gefunden.')
        return

    print('--- Alle Schluessel eines Beispiel-Spiels ---')
    print(list(sample.keys()))
    print('--- Komplettes Beispiel-Spiel (JSON) ---')
    print(json.dumps(sample, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
