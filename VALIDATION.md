# Weryfikacja wydania 2.2

Data: 11.09.2026. Środowisko: Windows, Python 3.12, Streamlit 1.63.0, requests 2.34.2, tzdata 2026.3.

- 23 testy automatyczne: zaliczone. Zawierają testy reguł, HTTP z kontrolowanymi odpowiedziami oraz AppTest z prawdziwego Streamlit.
- Wszystkie sześć ekranów przechodzi testy normalnych danych i niedostępnych źródeł bez nieobsłużonych wyjątków.
- Dodatkowe próby: brak godzin, zmiana sezonu, awaria klasyfikacji przy działającym kalendarzu, zachowanie ostatniej poprawnej kopii i odstęp między ponowieniami.
- `pip check`: brak konfliktów zależności.
- Uruchomiono prawdziwy serwer Streamlit i otwarto go w przeglądarce. Ekrany Start, Weekend i Wyniki poprawnie pobrały i wyświetliły dane Jolpica/OpenF1, w tym wyniki treningu i opisy kierowców.
- Kontrola wizualna na desktopie i przy szerokości 390 px. Na ekranach Start, Weekend oraz Wyniki nie stwierdzono poziomego przepełnienia strony; pomiar mobilny `scrollWidth == clientWidth == 390` dla Weekend i Wyniki. Sprawdzono łamanie tekstu harmonogramu i wielkość semantycznych nagłówków.

Nie przeprowadzono testu obciążeniowego, pełnego audytu WCAG, testów wszystkich przeglądarek, wdrożenia w chmurze ani niezależnej weryfikacji sportowej wyników. Poprawność działania przy awariach HTTP i niepełnych danych jest weryfikowana na kontrolowanych scenariuszach; dostępność zewnętrznych API może się zmieniać.

Ostrzeżenia o braku `ScriptRunContext` podczas testów jednostkowych wynikają z uruchamiania helperów cache poza serwerem Streamlit. Nie są niepowodzeniem testów.
