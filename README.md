# Marcin F1 Hub 2.1

Etap 1 rozwoju aplikacji F1 przeznaczonej do udostępniania z profilu X.

## Co zawiera wersja 2.1

- ekran startowy z najbliższą sesją i odliczaniem,
- pełny kalendarz sezonu,
- godziny przeliczone na strefę `Europe/Warsaw`,
- wyniki sesji:
  - FP1,
  - FP2,
  - FP3,
  - kwalifikacje sprintu,
  - sprint,
  - kwalifikacje,
  - wyścig,
- fallback wyników wyścigu / sprintu / kwalifikacji do Jolpica,
- klasyfikacja kierowców,
- klasyfikacja konstruktorów,
- strony kierowców,
- forma kierowcy z ostatnich 5 wyścigów,
- mobilny ciemny interfejs.


## Weekend Center

Nowa sekcja łączy cały weekend Grand Prix na jednym ekranie:

- automatycznie wybiera aktualną albo najbliższą rundę,
- pokazuje postęp weekendu,
- wyróżnia najbliższą sesję i odlicza do jej startu,
- prezentuje harmonogram wszystkich sesji,
- oznacza sesje jako zakończone, nadchodzące, następne lub trwające,
- pokazuje szybki podgląd Top 5 wyników zakończonych sesji,
- pokazuje Top 3 klasyfikacji kierowców i konstruktorów,
- podsumowuje numer rundy, tor oraz liczbę zakończonych sesji.

## Źródła danych

Aplikacja korzysta z:

- Jolpica / Ergast-compatible API — kalendarz, klasyfikacje, wyniki wyścigów,
- OpenF1 — wyniki poszczególnych sesji.

OpenF1 udostępnia dane historyczne bez logowania. Dane aktualnie trwającej sesji mogą podlegać ograniczeniom dostawcy, dlatego aplikacja ma obsługę braku danych i fallback.

## Uruchomienie lokalne

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

Następnie otwórz:

```text
http://localhost:8501
```

## Publikacja na Streamlit Community Cloud

Wgraj do GitHuba cały katalog projektu, ustaw plik startowy:

```text
app.py
```

i wdroż repozytorium w Streamlit Community Cloud.

## Struktura

```text
marcin_f1_hub_2/
├── app.py
├── f1_api.py
├── ui.py
├── requirements.txt
├── README.md
└── data/
    └── news.json
```

## Następny etap

Po ustabilizowaniu Etapu 1 można przejść do Content Center:
panel redakcyjny, własne newsy, integracja z X oraz generowanie treści.


## Poprawka 2.0.1

- poprawione renderowanie kart statystyk na stronie Start i Kierowcy,
- druga i trzecia karta nie są już interpretowane przez Markdown jako kod HTML.
