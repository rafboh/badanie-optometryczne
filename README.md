# Arkusz Badania Optometrycznego

Aplikacja webowa do prowadzenia i archiwizowania pełnych badań optometrycznych, zgodna ze **Standardem Badania Optometrycznego PTOO (aktualizacja 2025)**.

## Funkcje

- **Formularz 10-sekcyjny** — kompletny arkusz badania: wywiad, ostrość wzroku, refrakcja przedmiotowa i podmiotowa, widzenie bliskie, lampa szczelinowa, jakość widzenia, diagnoza i zalecenia
- **Autouzupełnianie** — rozwijane listy dla ostrości wzroku, wartości sferycznych, cylindrycznych, osi, pryzmatów, skal Efrona
- **Zapis automatyczny** — co 90 sekund oraz ręcznie (przycisk / Ctrl+S)
- **Archiwum badań** — lista pacjentów z wyszukiwarką, paginacja, edycja, usuwanie
- **Raport PDF/print** — wyświetla tylko wypełnione sekcje, optymalny układ do druku
- **Eksport TXT** — sformatowany raport tekstowy do pobrania jako `.txt`

## Technologia

| Warstwa | Technologia |
|---------|-------------|
| Backend | Python 3 + Flask |
| Baza danych | SQLite (jeden plik `optometry.db`) |
| Frontend | HTML5 + CSS3 + Vanilla JS (bez frameworków) |
| Szablony | Jinja2 |

## Wymagania

- Python 3.8+
- Google Chrome (zalecany)

## Uruchomienie (Windows)

### Metoda 1 — podwójne kliknięcie

Uruchom `start.bat`. Skrypt zainstaluje Flask (jeśli brak) i otworzy aplikację w Chrome.

### Metoda 2 — terminal

```bash
pip install flask
python app.py
```

Następnie otwórz: `http://localhost:5000`

## Struktura projektu

```
├── app.py                          # Serwer Flask, logika, generator TXT
├── requirements.txt                # Zależności Python
├── start.bat                       # Starter Windows
├── optometry.db                    # Baza SQLite (tworzona automatycznie)
├── static/
│   └── style.css                   # Style (ekran + druk)
└── templates/
    ├── base.html                   # Szablon bazowy
    ├── index.html                  # Lista badań
    ├── form.html                   # Formularz badania (10 sekcji)
    └── report.html                 # Raport do druku / PDF
```

## Sekcje formularza

| # | Sekcja |
|---|--------|
| 1 | Dane osobowe pacjenta |
| 2 | Wywiad (skargi, korekcja, choroby) |
| 3 | Badania wstępne (VA, binokularność, IOP, pola widzenia…) |
| 4 | Refrakcja przedmiotowa (FOF, autorefraktometria, keratometria, VA obj.) |
| 5 | Refrakcja podmiotowa – dal (monokularna, obuoczna, wergencje) |
| 6 | Widzenie bliskie (akomodacja, Add, wergencje bliskie) |
| 7 | Lampa szczelinowa (przedni i tylny odcinek) |
| 8 | Jakość widzenia (kontrast, olśnienie, HOA, VAS) |
| 9 | Diagnoza i zalecenia (korekcja końcowa, skierowania) |
| 10 | Podpisy |

## Dane

Wszystkie badania przechowywane są lokalnie w pliku `optometry.db` (SQLite). Aplikacja nie wysyła danych do zewnętrznych serwerów.

## Licencja

MIT
