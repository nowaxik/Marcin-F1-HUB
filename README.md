# Marcin F1 Hub

Mobilna mini-aplikacja F1 przeznaczona do podlinkowania z profilu X.

## Funkcje MVP

- automatyczne pobieranie aktualnej klasyfikacji kierowców,
- wykrywanie najbliższej sesji weekendu F1,
- odliczanie do sesji,
- sekcja własnych newsów,
- bezpośredni przycisk do profilu X,
- układ zoptymalizowany pod telefon.

## Uruchomienie

1. Zainstaluj Python 3.11+.
2. W terminalu przejdź do katalogu projektu.
3. Utwórz środowisko wirtualne (opcjonalnie).
4. Zainstaluj zależności:

```bash
pip install -r requirements.txt
```

5. Uruchom:

```bash
streamlit run app.py
```

## Edycja newsów

Edytuj:

```text
data/news.json
```

Każdy wpis może zawierać:

```json
{
  "title": "Tytuł",
  "description": "Krótki opis",
  "url": "https://..."
}
```

## Następne etapy

- automatyczne pobieranie postów z X API,
- pełny kalendarz sezonu,
- wyniki sesji,
- klasyfikacja konstruktorów,
- panel administratora do dodawania newsów,
- własna domena i publikacja online,
- wersja PWA / instalacja na ekranie telefonu.
