# Raport analizy Marcin F1 Hub 2.1

Data: 11.09.2026. Analizowana paczka: `Marcin F1 Hub ver. 2.1.zip`.

**Ocena: aplikacja jest czytelnym, niewielkim prototypem centrum informacji F1. Najpilniejsze poprawki dotyczą wiarygodności statusów sesji i odporności na awarie API. Przed szerszym udostępnieniem warto usunąć opisane poniżej błędy.**

Przeczytałem cały kod wersji 2.1: 826 linii `app.py`, 162 linii `f1_api.py` i 697 linii `ui.py` — łącznie 1685 linii, w tym CSS, komentarze i puste linie. Przejrzałem również README, zależności i `data/news.json`. Raport grupuje kolejne linie w spójne fragmenty, zamiast powtarzać osobny komentarz do każdej pustej linii czy deklaracji CSS.

Źródła wypakowano do `audit-v2.1/marcin_f1_hub_2`; ich zawartość nie została zmieniona. Nie porównywałem wersji 1.0 i 2.0. Numery linii poniżej dotyczą wypakowanej wersji 2.1.

## Co aplikacja robi i jak jest zbudowana

To aplikacja Python/Streamlit, której interfejs jest generowany po stronie serwera. Własny HTML i CSS nadają wygląd kartom, tabelom i harmonogramowi. Nie ma osobnego frontendu JavaScript, bazy danych ani panelu administracyjnego.

Przepływ danych: Jolpica dostarcza kalendarz i klasyfikacje; OpenF1 dostarcza sesje oraz wyniki; przy braku wyników OpenF1 program próbuje Jolpica dla wyścigu, sprintu i kwalifikacji. Dane są normalizowane w `load_normalized_results`, a następnie wyświetlane wspólną funkcją.

| Element | Odpowiedzialność | Ocena |
|---|---|---|
| `app.py` | Uruchomienie, daty, wybór rund, normalizacja i sześć ekranów | Czytelny dla małego projektu, lecz miesza zbyt wiele obowiązków |
| `f1_api.py` | HTTP, cache i dopasowanie weekendów | Dobry początek wydzielonej warstwy danych |
| `ui.py` | Style, komponenty i formatowanie | Komponenty są wielokrotnie wykorzystywane; formatery wymagają zabezpieczeń |
| `requirements.txt` | Streamlit i requests | Prosty zestaw, brak powtarzalnego zestawu wersji i jawnego wymagania Python |
| `data/news.json` | Jeden przykładowy wpis | Żaden fragment kodu go nie odczytuje |

## Ustalenia według ważności

Priorytet P1 oznacza istotny błąd danych lub dostępności, P2 — funkcjonalność lub odporność wymagającą poprawy, P3 — drobniejszy problem. Nie wykryłem problemu uzasadniającego kategorię krytyczną w przejrzanym kodzie; nie jest to certyfikacja bezpieczeństwa.

### 1. P1 — rozpoczęcie sesji jest traktowane jako jej zakończenie

**Lokalizacja:** `app.py:263–280`, `457–481`, `508`, `596–611`.

`completed` liczy sesje, których czas startu już minął. Analogicznie budowana jest lista zakończonych sesji do podglądu wyników. Gdy rozpocznie się ostatnia sesja, nie ma już przyszłych startów i kod wyświetla „Weekend został zakończony”. W tym samym czasie `session_state` może poprawnie pokazać „TRWA”, jeśli OpenF1 poda daty początku i końca. Interfejs przeczy wtedy sam sobie.

Bez metadanych OpenF1 każda rozpoczęta sesja dostaje „ZAKOŃCZONA”, nawet minutę po starcie. W kalendarzu wyścig również przechodzi do zakończonych zaraz po rozpoczęciu.

**Potwierdzenie:** próba dla sesji rozpoczętej 10 minut wcześniej i kończącej się za godzinę pokazała `TRWA` z OpenF1, `ZAKOŃCZONA` bez OpenF1 oraz ukończony postęp i warunek komunikatu o końcu weekendu.

**Naprawa:** jeden wspólny model stanu sesji używany w harmonogramie, filtrach, postępie i wyborze wyników. Koniec ustalać na podstawie wiarygodnego czasu końca/statusu; bez niego pokazać niepewność, zamiast ogłaszać zakończenie. Planowany czas końca nie gwarantuje faktycznego końca przy opóźnieniach.

### 2. P1 — awaria jednej klasyfikacji usuwa wszystkie dane podstawowe

**Lokalizacja:** `app.py:316–325`.

`load_core()` kolejno pobiera kalendarz i dwie klasyfikacje. Wyjątek z dowolnego zapytania powoduje przypisanie trzech pustych list. Poprawnie pobrany kalendarz znika więc również przy awarii samej klasyfikacji konstruktorów. Blokuje to Weekend, Kalendarz i Wyniki, choć ich podstawowe dane mogą działać.

**Potwierdzenie:** kontrolowana awaria klasyfikacji kierowców przerywa całe `load_core()`; blok obsługi w aplikacji zeruje cały zestaw.

**Naprawa:** pobierać i obsługiwać każde źródło niezależnie. Wyświetlać błąd konkretnej sekcji oraz, jeśli dostępne, ostatnie poprawne dane z oznaczeniem czasu pobrania.

### 3. P2 — fallback Jolpica gubi nazwę zespołu

**Lokalizacja:** `app.py:224–226`.

Kod szuka `Constructors`, czyli listy używanej w klasyfikacji kierowców. Wynik pojedynczego kierowcy zawiera obiekt `Constructor`. Skutkiem jest „—” zamiast zespołu w zapasowych wynikach.

**Potwierdzenie:** rekord z `Constructor: {name: Ferrari}` został znormalizowany do zespołu „—”. Pole potwierdza [dokumentacja wyników Jolpica](https://github.com/jolpica/jolpica-f1/blob/main/docs/endpoints/results.md).

**Naprawa:** odczytywać `row.get("Constructor") or {}` w adapterze wyników. Obecne odczyty listy `Constructors` w klasyfikacjach mają inne zastosowanie i nie powinny być mechanicznie zamieniane.

### 4. P2 — odliczanie i statusy nie aktualizują się samoczynnie

**Lokalizacja:** `app.py:108–115`, `344–360`, `455–519`; brak mechanizmu cyklicznego uruchamiania w całym projekcie.

Odliczanie to tekst obliczony przy wykonaniu skryptu. Otwarta strona nie aktualizuje go tylko dlatego, że upłynęła minuta. TTL cache określa ważność danych przy kolejnym wywołaniu; nie uruchamia samodzielnie kodu ani nie odświeża ekranu.

**Naprawa:** wydzielić fragment odświeżany okresowo, np. z `st.fragment(run_every=...)`, oraz zachować cache pobierania danych. Mechanizm opisuje [dokumentacja Streamlit](https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment). Nie ma potrzeby odpytywania wszystkich API co sekundę.

### 5. P2 — awaria metadanych kierowców usuwa dostępne wyniki

**Lokalizacja:** `app.py:179–211`.

Zapytania o wyniki i o kierowców są w jednym `try`. Jeśli wyniki przyjdą poprawnie, ale drugie zapytanie zawiedzie, lista wyników zostaje wyzerowana. Dla treningów i kwalifikacji sprintu nie istnieje fallback Jolpica, więc ekran pozostaje pusty.

**Potwierdzenie:** poprawny wynik FP1 i wyjątek przy pobieraniu kierowców dały `([], None)`.

**Naprawa:** oddzielić obsługę błędów. Zachować wynik i pokazać numer kierowcy, korzystając z już istniejącej alternatywy `#numer`; metadane uzupełnić później.

### 6. P2 — awaria źródła jest przedstawiana jako brak opublikowanych rezultatów

**Lokalizacja:** `app.py:210–257`, `449–453`, `521–524`, `670–687`.

Błędy HTTP, ograniczenie dostępu, limit zapytań i rzeczywisty brak danych kończą się podobnym pustym wynikiem. Użytkownik dostaje sugestię, aby poczekać na publikację rezultatów, także wtedy, gdy problemem jest połączenie.

**Naprawa:** zwracać wraz z wynikami jawny stan: dostępne, brak publikacji, źródło niedostępne, dostęp ograniczony. Zachować szczegóły do diagnostyki, a użytkownikowi pokazać krótki komunikat.

### 7. P2 — parsowanie dat zakłada kompletny i poprawny format

**Lokalizacja:** `app.py:66–73`, `119–125`; `f1_api.py:104–110`, `125–161`.

Brak godziny jest zamieniany na północ UTC. To wymyślona godzina startu, która może błędnie przesuwać sesję do zakończonych. Niepoprawna data w `session_datetime` powoduje nieobsłużony `ValueError`. Data bez strefy przechodzi parsowanie, lecz może spowodować `TypeError` podczas porównania z czasem UTC.

**Potwierdzenie:** brak godziny dał `00:00 UTC`; niepoprawna data wywołała `ValueError`; porównanie godziny bez strefy z bieżącym czasem — `TypeError`. To próby odporności na niepełne dane, nie dowód, że dostawca obecnie zwraca takie rekordy.

**Naprawa:** jeden parser dat z walidacją, jawną polityką strefy i oddzielnym stanem „godzina nieznana”. Pomijać niepoprawny rekord z diagnostyką zamiast przerywać cały widok.

### 8. P2 — JSON jest przyjmowany bez wystarczającej walidacji struktury

**Lokalizacja:** `f1_api.py:35–101`; `app.py:188–207`, `223–254`, `292–308`.

Poprawny składniowo JSON nie musi odpowiadać oczekiwanemu schematowi. Jolpica jest od razu traktowana jak słownik; OpenF1 sprawdza jedynie, czy odpowiedź jest listą. `null` zamiast słownika albo tekst zamiast rekordu mogą spowodować wyjątki inne niż `APIError`. `dict.get(key, default)` nie zastępuje jawnego `null` wartością domyślną.

**Potwierdzenie:** lista zamiast obiektu Jolpica powoduje `AttributeError`. Nie potwierdzono występowania takiej odpowiedzi na żywo.

**Naprawa:** walidować odpowiedzi na granicy API, normalizować brakujące wartości i wymagać określonych typów w dalszej części programu.

### 9. P2 — uruchomienie na Windows zależy od dostępności bazy stref czasowych

**Lokalizacja:** `app.py:48`, `ui.py:7`, `requirements.txt:1–2`.

`ZoneInfo("Europe/Warsaw")` jest wykonywane przy ładowaniu modułów. Projekt nie deklaruje `tzdata`. Na systemie bez bazy IANA i bez tego pakietu aplikacja nie wystartuje. To ryzyko środowiskowe, nie stwierdzona awaria tego komputera: dostępny runtime audytu zawiera `tzdata`.

[Dokumentacja Python](https://docs.python.org/3/library/zoneinfo.html#data-sources) zaleca zależność od `tzdata` dla zgodności między platformami, w szczególności Windows.

**Naprawa:** zadeklarować `tzdata` i wersję Pythona. Składnia adnotacji w projekcie wymaga co najmniej Python 3.10; docelową wersję należy dobrać także do wybranej wersji Streamlit.

### 10. P3 — błędne zaokrąglanie czasu na granicy minuty

**Lokalizacja:** `ui.py:643–652`.

Sekundy są formatowane po oddzielnym obliczeniu minut. `59.9999` daje `0:60.000`, zamiast `1:00.000`. Dodatkowo `NaN` powoduje wyjątek.

**Naprawa:** sprawdzać skończoność wartości, zaokrąglać całość do milisekund i dopiero później dzielić na godziny, minuty i sekundy. Priorytet niski: nie wykazano, że zwykłe dane dostawcy wywołują ten przypadek.

## Pełna mapa przeglądu kodu

Zakresy obejmują cały kod; rozdzielające puste linie i komentarze przynależą do sąsiednich fragmentów.

### `app.py` — 826 linii, 13 funkcji

| Linie | Działanie i uwagi |
|---|---|
| 1–36 | Importy. Warstwy API i UI są wydzielone; logiczna zależność aplikacji od obu jest czytelna. |
| 38–49 | Konfiguracja strony, CSS, sezon i strefa. Sezon jest zawsze bieżącym rokiem serwera; brak przeglądania archiwum i wyboru ostatniego zakończonego sezonu. |
| 52–63 | Konwersje liczb. `safe_float` jest nieużywana; `safe_int` nie obsługuje `OverflowError` dla nieskończoności, co jest dodatkowym przypadkiem brzegowym. |
| 66–95 | Budowanie planu sesji i sortowanie. Czytelne mapowanie nazw; problemy niepełnych dat opisano w ustaleniu 7. |
| 98–105 | Najbliższa przyszła sesja. Funkcja zgodna z nazwą, ale ekran Start nie eksponuje sesji właśnie trwającej. |
| 108–115 | Odliczanie w dniach, godzinach, minutach. Nieujemny wynik; bez samoczynnego odświeżania. |
| 119–125 | Drugi parser dat. Warto połączyć go z parserem w API. |
| 128–150 | Wybór aktualnego lub następnego weekendu. Pięć godzin po starcie wyścigu to heurystyka; zależy od kolejności kalendarza. |
| 153–169 | Łączenie planowanych nazw z OpenF1. Zduplikowane nazwy sesji zachowują pierwszy rekord; brak uzasadnienia wyboru przy powtórzeniu sesji. |
| 172–260 | Normalizacja wyników, fallback i sortowanie. Najważniejszy fragment integracji; ustalenia 3, 5, 6 i 8. Pole `code` jest pobierane, ale nie jest wyświetlane przez renderer. |
| 263–280 | Ustalanie statusu. Brak wiarygodnej obsługi końca sesji bez OpenF1; ustalenie 1. |
| 283–313 | Wspólne renderowanie wyników. Dynamiczne teksty są escapowane. W fallbacku status typu `+1 Lap` może trafić jednocześnie do czasu i statusu, a więc zostać wyświetlony dwa razy. |
| 316–325 | Pobieranie wszystkich danych podstawowych przed wyborem widoku. Zbędne sprzężenie dostępności; ustalenie 2. |
| 328–339 | Nagłówek i sześć zakładek realizowanych przez radio. Prosta nawigacja; brak adresów URL wskazujących bezpośrednio rundę, sesję lub kierowcę. |
| 341–399 | Start: sesja, liderzy, Top 5, link X. Brak wyraźnego komunikatu końca sezonu, gdy nie ma kolejnej sesji. Liderzy wyświetlają się dopiero, gdy dostępne są obie klasyfikacje. |
| 401–447 | Weekend: selektor rundy, daty lokalne, nagłówek. Poprawne formatowanie zakresu dni, przy założeniu poprawnych danych wejściowych. |
| 449–481 | Dane OpenF1, postęp i następna sesja. Ustalenia 1 i 6. |
| 483–505 | Harmonogram z polskimi dniami tygodnia. Jasna prezentacja stanów; logika statusu wymaga poprawy. |
| 507–527 | Szybkie Top 5. Lista „zakończonych” obejmuje sesje rozpoczęte; ustalenie 1. |
| 529–573 | Top 3 klasyfikacji i karty weekendu. Przy starej rundzie prezentuje aktualne klasyfikacje sezonu, a nie stan po tej rundzie; warto podpisać to jednoznacznie. |
| 575–636 | Kalendarz, filtry, rozwijane sesje. „Najbliższe” ograniczono do sześciu rund. Brak informacji przy pustym wyniku filtrowania; statusy oparte tylko na starcie. |
| 638–690 | Wyniki: wybór weekendu i sesji. Domyślna sesja to pierwsza na liście, zwykle FP1; lepsza byłaby ostatnia zakończona. `round_no` z linii 667 pozostaje nieużywane. |
| 693–726 | Klasyfikacje. Escapowanie danych jest konsekwentne; widoki poprawnie obsługują puste listy. |
| 728–769 | Profil kierowcy. Lista pochodzi z klasyfikacji, więc przy jej braku profile są niedostępne. Pierwszy konstruktor z listy nie jest gwarancją aktualnego zespołu po transferze. |
| 771–810 | Ostatnie pięć startów kierowcy. To pięć ostatnich zwróconych wyników, niekoniecznie pięć ostatnich rund sezonu. `positionText` typu `R` dostaje prefiks `P`, dając nieczytelne `PR`; przyda się mapowanie statusów. |
| 812–817 | Zewnętrzny link do kierowcy. Warto dopuścić wyłącznie protokoły http/https na granicy adaptera danych; nie stwierdzono wykorzystania złośliwego URL. |
| 819–826 | Statyczna stopka z wersją i źródłami. Przydałby się czas aktualizacji danych. |

### `f1_api.py` — 162 linie, 11 funkcji

| Linie | Działanie i uwagi |
|---|---|
| 1–12 | Importy i stałe dostawców. HTTPS, stałe hosty i mała powierzchnia konfiguracji. |
| 15–16 | Wspólny typ wyjątku API — dobry punkt wyjścia do rozróżnienia błędów. |
| 19–31 | Pobranie HTTP, status odpowiedzi, JSON, timeout. Brak ponowień, rozróżnienia 429 i diagnostyki. User-Agent nadal wskazuje 2.0. Przy współczesnym requests błąd JSON może wpadać w pierwszy `except` ze względu na hierarchię wyjątków; do osobnego sprawdzenia po instalacji zależności. |
| 34–37 | Cache kalendarza na 300 s. Limit 100 wystarcza dla pojedynczego obecnego sezonu; brak walidacji obiektu. |
| 40–44 | Klasyfikacja kierowców; prawidłowe użycie pierwszej listy dla zapytania sezonowego. |
| 47–51 | Klasyfikacja konstruktorów; analogiczna implementacja. |
| 54–61 | Wyniki jednego kierowcy, pomijanie pustego ID, kodowanie parametru ścieżki. Limit 100 jest adekwatny dla pojedynczego sezonu. |
| 64–83 | Trzy rodzaje zapasowych wyników; poprawne różnicowanie kluczy Results, QualifyingResults, SprintResults. Brak fallbacku treningów jest świadomym ograniczeniem funkcji. |
| 86–89 | Roczna lista sesji OpenF1, cache 600 s. Zmiana planu może nie pojawić się od razu. |
| 92–95 | Wyniki sesji, cache 180 s. Pusta odpowiedź również pozostaje w cache do wygaśnięcia. |
| 98–101 | Kierowcy sesji, cache 600 s. Dodatkowe zapytanie potrzebne do opisów. |
| 104–110 | Parser ISO. Obsługuje część błędnych napisów, ale nie weryfikuje obecności strefy ani typu wejścia. |
| 113–138 | Dopasowanie sesji do okna od czterech dni przed datą wyścigu do półtora dnia po niej. Unika problemów różnego nazewnictwa torów, lecz nie potwierdza tożsamości zawodów. |
| 139–162 | Grupowanie meetingów, wybór po bliskości i sortowanie. Odległość liczona od północy dnia wyścigu, nie faktycznego startu. Preferowanie meetingu z sesją Race blisko planowanego startu zwiększyłoby pewność; nie potwierdzono błędnego dopasowania realnego weekendu. |

### `ui.py` — 697 linii, 17 funkcji

| Linie | Działanie i uwagi |
|---|---|
| 1–7 | Importy i strefa. Duplikacja konfiguracji strefy z `app.py`; ryzyko opisane w ustaleniu 9. |
| 10–36 | Wstrzyknięcie CSS, kolory, tło i szerokość kontenera. `--bg`, `--panel`, `--panel2` nie są dalej używane. Selektory wewnętrznego DOM Streamlit wymagają kontroli po aktualizacjach frameworka. |
| 38–94 | Nagłówek i karta odliczania. Elastyczne rozmiary fontów; deklarowane duże wagi zależą od możliwości użytej czcionki. |
| 96–139 | Wiersze wyników i punktów. `min-width: 0` i łamanie długich szczegółów pomagają na małym ekranie. |
| 141–177 | Karty metryk. Dwie lub trzy kolumny; długie wartości mogą się łamać. |
| 180–278 | Weekend Center: nagłówek, harmonogram, wyróżnienia. Oprócz koloru są tekstowe nazwy statusów — korzystne dla czytelności. |
| 280–313 | Karty podium. W kodzie nie ma osobnego rozwiązania na bardzo wąskie ekrany; konieczna próba w przeglądarce. |
| 315–382 | Kalendarz, odznaki, profil i forma. Dane tabelaryczne są przedstawiane jako divy, bez semantyki tabeli. |
| 384–415 | Komunikaty, stopka i przyciski. Dobra minimalna wysokość przycisków; widoczność i kontrast należy sprawdzić na renderze. |
| 417–475 | Media query do 640 px. Harmonogram zmienia układ; metryki i podium zachowują trzy kolumny. To obserwacja kodu, nie potwierdzony błąd wizualny. |
| 478–506 | Hero, tytuły sekcji, karta sesji. Teksty escapowane. Główne tytuły to divy zamiast h1/h2, co osłabia semantykę dokumentu. |
| 509–526 | Wiersz klasyfikacji. Poprawne escapowanie; wybór pierwszego zespołu ma ograniczenie przy zmianie zespołu. |
| 529–549 | Karty metryk. Kompaktowy HTML realizuje opisaną w README poprawkę renderowania; brak pustych wierszy pomiędzy kartami. |
| 553–562 | Nagłówek weekendu. Wartości zamieniane na tekst i escapowane. |
| 565–589 | Karta sesji. Klasy CSS dobierane z zamkniętego zestawu, a tekst escapowany. |
| 592–602 | Podium Top 3. Funkcja ogranicza liczbę elementów i zabezpiecza tekst. |
| 605–616 | Puste stany, błędy i odznaki. Poprawne escapowanie; helper odznaki rozpoznaje dokładnie „ZAKOŃCZONE”, co odpowiada obecnemu wywołaniu. |
| 619–625 | Format lokalnej daty. Konwersja do Warszawy jest prawidłowym podejściem, jeżeli wejście ma określoną strefę. |
| 628–640 | Nazwy sesji. Obsługuje zarówno Sprint Qualifying, jak i Sprint Shootout. |
| 643–652 | Sekundy do czasu. Błąd granicy minuty i brak walidacji liczb; ustalenie 10. |
| 655–674 | Czas skalarny lub lista Q1–Q3. Poprawnie zachowuje numery segmentów przy brakującej wartości Q2. |
| 677–697 | Strata do lidera. Dla listy bierze ostatnią dostępną wartość bez etykiety segmentu; obok Q1–Q3 może być niejasne, czego dotyczy strata. Końcowe rozgałęzienie dla tekstu z `+` niczego nie zmienia. |

### Pliki towarzyszące

README opisuje rzeczywiste główne widoki i sposób uruchomienia. Stwierdzenie o odliczaniu wymaga doprecyzowania lub dodania automatycznego odświeżania. Brakuje wersji Python, instrukcji diagnozowania API i informacji o znanych ograniczeniach.

`requirements.txt` ma szerokie zakresy `streamlit>=1.40,<2` i `requests>=2.32,<3`. To nie oznacza automatycznie błędu, ale kolejne instalacje mogą używać innych wersji. Dla powtarzalnych wdrożeń warto zapisać przetestowany zestaw zależności.

`data/news.json` zawiera poprawny przykładowy wpis, nadal oznaczony wersją 2.0. Aktualna aplikacja go nie wczytuje; obecność pliku nie oznacza działającej sekcji newsów ani integracji z X. X jest obecnie wyłącznie linkiem do profilu.

W paczce nie ma testów, konfiguracji CI ani osobnej konfiguracji wdrożenia.

## Wydajność i aktualność danych

Cache o czasie 180–600 sekund ogranicza liczbę wywołań i jest sensownym początkiem. Zagnieżdżony cache `load_core()` i poszczególnych getterów komplikuje jednak ustalanie świeżości; cache agregatu korzysta dodatkowo z globalnego `SEASON`, zamiast przyjmować sezon jako argument.

Zimne wejście pobiera trzy źródła Jolpica sekwencyjnie. Widok wyników może następnie pobrać listę sesji, wyniki i kierowców OpenF1, a przy problemie jeszcze fallback. Timeout 12/15 s ogranicza pojedyncze oczekiwania sieciowe, ale nie stanowi globalnego limitu czasu renderowania. Użytkownik może czekać długo na serię wolnych odpowiedzi. Warto mierzyć czas pobierania i wykonywać tylko zapytania potrzebne danemu widokowi.

OpenF1 opisuje bezpłatny dostęp historyczny oraz ograniczenia dostępu live; okno live obejmuje również czas po sesji. Dlatego obietnica rezultatów „kilka minut” po publikacji nie powinna być traktowana jako gwarancja. Dostawca podaje także limity zapytań, istotne przy częstym przełączaniu sesji bez trafień w cache. [Źródło: OpenF1](https://openf1.org/).

## Bezpieczeństwo i dostępność

W przejrzanej paczce nie znalazłem wpisanych haseł, tokenów, wykonywania poleceń z danych użytkownika ani zapisu do bazy. Wywołania HTTP używają HTTPS, a teksty w autorskim HTML są konsekwentnie escapowane. Samo `unsafe_allow_html=True` nie dowodzi podatności XSS; kontrolowane sprawdzenie tekstu `<script>` wykazało jego zamianę na bezpieczny zapis tekstowy.

Pozostaje zależność od prawidłowych danych z API i od aktualnych bibliotek. Nie przeprowadzałem skanowania podatności zainstalowanych pakietów, testów penetracyjnych ani infrastruktury hostingu. Nie można na podstawie tego przeglądu potwierdzić bezpieczeństwa produkcyjnego wdrożenia.

W interfejsie warto użyć semantycznych nagłówków i zapewnić czytelną prezentację wyników dla czytników ekranu. Nie oceniałem wyglądu, obsługi klawiatury, kontrastu ani responsywności na działającym renderze; obecność media queries nie zastępuje takiego sprawdzenia.

## Weryfikacja wykonana w audycie

1. Wszystkie trzy oryginalne moduły przechodzą parsowanie i kompilację składni Python.
2. Wykonano 15 kontrolowanych prób funkcji i warunków: statusy sesji, postęp, normalizacja zespołu, daty, formatowanie czasu, awarie źródeł, struktura JSON i escapowanie HTML.
3. Funkcje pobrano z oryginalnego kodu przez AST. HTTP i Streamlit zastąpiono kontrolowanymi atrapami; warunek postępu odtworzono z kodu widoku. Wyniki prób dokumentują także oczekiwane wyjątki i wykryte błędy — nie oznaczają 15 zaliczonych testów poprawności produktu.
4. Zweryfikowano dokumentację Jolpica, OpenF1, Python ZoneInfo i mechanizmu odświeżania Streamlit.

Skrypt: `audit-v2.1/check_logic.py`. Surowe wyniki: `audit-v2.1/check-results.json`.

**Granice weryfikacji:** dostępny interpreter audytu nie zawiera Streamlit ani requests. Nie instalowałem zależności, nie uruchamiałem całej aplikacji ani nie pobierałem przez nią bieżących rezultatów. Nie potwierdzam integracji end-to-end, aktualnych wyników sportowych ani wyglądu w przeglądarce.

## Zalecana kolejność prac

1. Poprawić wspólny model początku i końca sesji oraz niezależne pobieranie danych podstawowych.
2. Naprawić `Constructor`, zachować wyniki przy błędzie metadanych i odróżnić awarię od braku publikacji.
3. Dodać okresowe odświeżanie widocznych statusów, czas ostatniej aktualizacji i wiarygodne komunikaty dostępności.
4. Uporządkować parsery dat, schematy odpowiedzi, zależności i docelową wersję Python.
5. Wprowadzić testy regresyjne opisanych przypadków oraz sprawdzić sześć widoków na desktopie i telefonie z rzeczywistym Streamlit.
6. Następnie wydzielić logikę sesji i adaptery wyników z `app.py`; dopiero na stabilnej podstawie rozwijać newsy i dodatkowe funkcje.

Nie ma obecnie potrzeby przepisywania całego projektu na inny framework. Największą poprawę jakości dają niewielkie, konkretne zmiany w logice danych i statusów.
