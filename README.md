# Marcin F1 Hub 2.2

Centrum informacji F1 w Pythonie i Streamlit: Start, Weekend Center, Kalendarz, Wyniki, Klasyfikacje i Kierowcy. Wersja 2.2 poprawia wiarygodność statusów sesji i odporność na błędy źródeł. Zachowuje ciemny interfejs poprzedniej wersji.

## Uruchomienie na Windows

Wymagany Python 3.12 i połączenie z internetem. Otwórz PowerShell w wypakowanym folderze zawierającym `app.py`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Otwórz `http://localhost:8501`. Nie trzeba aktywować środowiska PowerShell ani zmieniać ExecutionPolicy. Kolejne uruchomienia wymagają tylko ostatniego polecenia. Serwer zatrzymasz przez Ctrl+C.

## Linux / macOS

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m streamlit run app.py
```

`requirements.txt` przypina bezpośrednie zależności, a `requirements-lock.txt` zapisuje pełny zestaw użyty w testach na Pythonie 3.12. `tzdata` zapewnia bazę stref czasowych także na Windows. Przed inną wersją Pythona lub zmianą zależności uruchom testy.

## Co zmieniono

- Wspólny model statusów we wszystkich ekranach; rozpoczęcie wyścigu nie kończy już weekendu.
- Przy braku końca sesji: status „NIEPOTWIERDZONA”; przy braku poprawnej godziny: „BRAK GODZINY”. Aplikacja nie podstawia północy.
- Kalendarz zachowuje dostępność przy awarii klasyfikacji; pobierane są dane potrzebne aktualnemu ekranowi.
- Wyniki pozostają dostępne przy awarii opisów kierowców; wówczas wyświetlany jest numer zawodnika.
- Poprawione zespoły w zapasowych wynikach Jolpica oraz brak powielania statusu w miejscu czasu.
- Błędy API, ograniczenia dostępu i limity zapytań mają komunikaty inne niż brak publikacji wyników.
- Ostatnie poprawne odpowiedzi są zachowywane w bieżącej sesji użytkownika i jawnie oznaczane przy błędzie odświeżania. Ponowna próba po błędzie następuje najwcześniej po 60 sekundach.
- Odświeżanie otwartego widoku co 30 sekund, szczegóły czasu pobrania w „Aktualność danych”.
- Wybór sezonu od 2023 roku, domyślnie rok bieżący; profile pokazują ostatnie pięć startów kierowcy i czytelne DNF/DSQ.
- Poprawione zaokrąglanie czasu, obsługa pustych danych, linki http/https, semantyczne nagłówki i układ małych ekranów.

## Ważne zasady interpretacji danych

„TRWA” i „ZAKOŃCZONA” wynikają z dat startu i końca opublikowanych przez OpenF1. Nie są niezależnym potwierdzeniem od sędziów; opóźnienia i korekty dostawcy mogą zmienić status. Przy braku godziny końca aplikacja pozostaje ostrożna — także dawna sesja może być niepotwierdzona. Wyniki można wtedy sprawdzić ręcznie na ekranie Wyniki.

Postęp weekendu liczy wyłącznie sesje z zakończeniem według OpenF1. Bez danych tego źródła nie jest zgadywany. Klasyfikacje w Weekend Center przedstawiają aktualny stan wybranego sezonu, nie stan po wybranej rundzie.

Odświeżanie ekranu co 30 sekund nie oznacza pobierania wszystkich danych co 30 sekund. Cache API ma TTL 180 sekund dla wyników, 300 dla kalendarza i klasyfikacji oraz 600 dla sesji i metadanych kierowców. Czas pobrania dotyczy odpowiedzi dostawcy, a nie czasu ostatniej sportowej aktualizacji. Puste wyniki też podlegają cache.

Ostatnia poprawna kopia jest przechowywana w pamięci sesji, nie na dysku. Nowa sesja przeglądarki lub restart procesu nie gwarantują zachowania tej kopii. Błędy są ponawiane z przerwą, bez zapętlania żądań. Jedno żądanie HTTP może być ponowione przy wybranych przejściowych błędach serwera; nie ma automatycznych ponowień dla 401, 403 i 429 w tym samym wywołaniu.

Dane publiczne pochodzą z [Jolpica](https://github.com/jolpica/jolpica-f1) i [OpenF1](https://openf1.org/). Dostęp do sesji live może być ograniczony przez dostawcę. Aplikacja nie obiecuje wyników po określonej liczbie minut i nie dodaje płatnej integracji live.

## Testy

W folderze aplikacji na Windows:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Na Linux/macOS użyj `.venv/bin/python`. Testy nie wymagają internetu. Obejmują logikę sesji, daty, formatowanie, walidację odpowiedzi, zachowanie danych przy awariach oraz sześć ekranów uruchomionych w prawdziwym Streamlit AppTest z kontrolowanymi odpowiedziami HTTP. Wynik weryfikacji wydania znajduje się w `VALIDATION.md`.

## Struktura

```text
app.py                  ekrany i okresowe odświeżanie
domain.py               wspólne reguły dat, statusów i formatowania
f1_api.py               zapytania, walidacja i cache API
services.py             normalizacja wyników i częściowe awarie
ui.py                   style i komponenty
tests/test_app.py       testy regresyjne i ekranów
.streamlit/config.toml  ciemny motyw i wyłączone statystyki użycia
requirements.txt        przypięte bezpośrednie zależności
requirements-lock.txt   pełny zestaw zależności z testów
```

`data/news.json` pozostaje nieaktywnym przykładem na przyszłość. Wersja 2.2 nie ma panelu redakcyjnego ani publikacji postów w X; przycisk X prowadzi do profilu autora.

## Wdrożenie

W Streamlit Community Cloud wskaż `app.py` jako plik startowy oraz Python 3.12 w konfiguracji wdrożenia. Zachowaj cały folder aplikacji, w tym `domain.py`, `services.py`, `f1_api.py` i `ui.py`. Udostępniona paczka nie została automatycznie opublikowana ani wdrożona na zewnętrzny hosting.
