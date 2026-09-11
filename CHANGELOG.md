# 2.2 — 11.09.2026

Wydanie naprawcze po audycie 2.1.

| Ustalenie audytu | Poprawka |
|---|---|
| Start sesji uznawany za koniec | Wspólne statusy; koniec zależny od `date_end`, nie od samego startu |
| Awaria jednej klasyfikacji usuwa wszystko | Niezależne źródła i ostatnia poprawna kopia w sesji |
| Brak zespołów w wynikach Jolpica | Adapter odczytuje `Constructor` |
| Nieruchome odliczanie | Fragment Streamlit odświeżany co 30 s |
| Utrata wyników przy błędzie opisów | Osobne pobieranie wyników i opisów kierowców |
| Awaria przedstawiana jako brak publikacji | Osobne stany i komunikaty dla błędów, limitów oraz pustych wyników |
| Niepełne daty i zgadywanie północy | Wspólny parser UTC, brak godziny pozostaje jawny |
| Brak walidacji struktury | Walidacja obiektów/list i normalizacja pól nullable |
| Ryzyko startu na Windows | `tzdata`, Python 3.12 i przypięte zależności |
| Zaokrąglenie `0:60.000` | Podział czasu po zaokrągleniu całkowitej liczby milisekund |

Dodatkowo: wybór sezonu 2023–rok bieżący, jawne czasy pobrania, retry z limitem, poprawione DNF/DSQ, wiele zespołów w sezonie, filtr niepotwierdzonych weekendów, bezpieczne protokoły linków, nagłówki HTML i układ kart na wąskich ekranach. Szczegóły i ograniczenia w README.
