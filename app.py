from datetime import datetime, timezone
from html import escape
import streamlit as st
from f1_api import (get_schedule, get_driver_standings, get_constructor_standings,
                    get_driver_race_results, get_openf1_sessions, match_openf1_sessions_to_race)
from domain import (WARSAW, safe_int, text, session_datetime, race_sessions,
                    countdown, focus_race_index, build_session_options,
                    effective_sessions, weekend_states, weekend_finished, position_label, safe_url)
from services import load_source, load_normalized_results
from ui import (apply_styles, driver_row_html, format_duration, format_gap,
                format_local_datetime, render_empty, render_error, render_hero,
                render_metric_cards, render_section_title, render_session_card,
                render_weekend_header, render_weekend_session, render_podium_cards, status_badge)

st.set_page_config(page_title="Marcin F1 Hub 2.2", page_icon="🏎️", layout="centered", initial_sidebar_state="collapsed")
apply_styles()
X_PROFILE = "https://x.com/MarcinNov"
current_year = datetime.now(WARSAW).year
season = st.selectbox("Sezon", list(range(current_year, 2022, -1)), key="season")
render_hero(kicker=f"FORMULA 1 · SEZON {season}", title="MARCIN F1 HUB", subtitle="Kalendarz, wyniki, klasyfikacje i forma kierowców — w jednym miejscu.")
nav = st.radio("Nawigacja", ["Start", "Weekend", "Kalendarz", "Wyniki", "Klasyfikacje", "Kierowcy"], horizontal=True, label_visibility="collapsed")
if "saved_sources" not in st.session_state:
    st.session_state.saved_sources = {}

def read_data(label, getter, *args):
    result = load_source(getter, args, st.session_state.saved_sources, (getter.__name__, *args))
    for warning in result.warnings:
        st.warning(f"{label}: {warning}" + (" Pokazuję ostatnie poprawnie pobrane dane." if result.rows else ""))
    if result.fetched_at:
        st.session_state.source_info.append(f"{label} · pobrano {result.fetched_at.astimezone(WARSAW).strftime('%d.%m.%Y %H:%M:%S')}")
    return result.rows

def show_result_status(result):
    for warning in dict.fromkeys(result.warnings):
        st.warning(warning)
    if result.state == "stale":
        st.info("Pokazuję ostatnie poprawnie pobrane wyniki; odświeżenie źródła nie powiodło się.")
    if result.fetched_at:
        st.caption(f"Wyniki pobrano {result.fetched_at.astimezone(WARSAW).strftime('%d.%m.%Y %H:%M:%S')}")

def render_result_rows(results, limit=None):
    rows = results[:limit] if limit else results
    for row in rows:
        pos = row.get("position") or "—"
        duration = format_duration(row.get("duration"))
        gap = format_gap(row.get("gap"))
        laps = row.get("laps")
        status = row.get("status") or ""

        detail_parts = [text(row.get("team"))]
        if duration:
            detail_parts.append(duration)
        if gap:
            detail_parts.append(gap)
        if laps not in (None, ""):
            detail_parts.append(f"{laps} okr.")
        if status and status not in ("Finished", ""):
            detail_parts.append(str(status))

        st.markdown(
            (
                '<div class="result-row">'
                f'<div class="result-pos">{escape(str(pos))}</div>'
                '<div class="result-main">'
                f'<div class="result-name">{escape(text(row.get("name")))}</div>'
                f'<div class="result-detail">{escape(" · ".join(detail_parts))}</div>'
                '</div>'
                '</div>'
            ),
            unsafe_allow_html=True,
        )


@st.fragment(run_every="30s")
def render_page(nav, SEASON):
    saved = st.session_state.saved_sources
    st.session_state.source_info = []
    schedule = read_data("Kalendarz", get_schedule, SEASON) if nav in ("Start", "Weekend", "Kalendarz", "Wyniki") else []
    driver_standings = read_data("Klasyfikacja kierowców", get_driver_standings, SEASON) if nav in ("Start", "Weekend", "Klasyfikacje", "Kierowcy") else []
    constructor_standings = read_data("Klasyfikacja konstruktorów", get_constructor_standings, SEASON) if nav in ("Start", "Weekend", "Klasyfikacje") else []
    season_openf1 = read_data("Sesje OpenF1", get_openf1_sessions, SEASON) if schedule else []
    if st.session_state.source_info:
        with st.expander("Aktualność danych"):
            for info in st.session_state.source_info:
                st.caption(info)
    # ============================================================
    # START
    # ============================================================
    if nav == "Start":
        now = datetime.now(timezone.utc)
        future = [(dt, label, race) for race in schedule
                  for dt, label in effective_sessions(race, match_openf1_sessions_to_race(season_openf1, race)) if dt > now]
        next_item = min(future, key=lambda item: item[0]) if future else None

        if next_item:
            target, session_name, race = next_item
            location = race.get("Circuit", {}).get("Location", {})
            render_section_title("🏁 Najbliższa sesja")
            render_session_card(
                gp=race.get("raceName", "Grand Prix"),
                session=session_name,
                countdown=countdown(target),
                details=(
                    f"{race.get('Circuit', {}).get('circuitName', '')} · "
                    f"{location.get('locality', '')} · "
                    f"{format_local_datetime(target)}"
                ),
            )

        else:
            render_empty("Brak kolejnych sesji z potwierdzoną godziną w wybranym sezonie.")

        if schedule:
            current = schedule[focus_race_index(schedule)]
            matched = match_openf1_sessions_to_race(season_openf1, current)
            for label, (state, note) in weekend_states(current, matched).items():
                if state == "TRWA":
                    st.info(f"{current.get('raceName', 'Grand Prix')} · {label} · TRWA. {note}")

        leader_cards = []
        if driver_standings:
            leader = driver_standings[0]
            driver = leader.get("Driver", {})
            leader_cards.append(("Lider kierowców", f"{driver.get('givenName', '')} {driver.get('familyName', '')}", f"{leader.get('points', '0')} pkt"))
        if constructor_standings:
            leader = constructor_standings[0]
            leader_cards.append(("Lider konstruktorów", leader.get("Constructor", {}).get("name", "—"), f"{leader.get('points', '0')} pkt"))
        if leader_cards:
            render_metric_cards(leader_cards)

        render_section_title("🔥 Szybki podgląd klasyfikacji")
        if driver_standings:
            for row in driver_standings[:5]:
                st.markdown(driver_row_html(row), unsafe_allow_html=True)
        else:
            render_empty("Klasyfikacja nie jest teraz dostępna.")

        st.link_button("𝕏  Przejdź do mojego profilu", X_PROFILE, use_container_width=True)

        st.markdown(
            """
            <div class="info-box">
                <strong>F1 Hub 2.2</strong><br>
                Dane sportowe są pobierane automatycznie. Wyniki sesji mogą pojawić się
                z opóźnieniem zależnym od dostawcy. Widok odświeża się co 30 sekund.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ============================================================
    # WEEKEND CENTER
    # ============================================================
    elif nav == "Weekend":
        render_section_title("🏎️ Weekend Center")

        if not schedule:
            render_empty("Nie można otworzyć Weekend Center bez kalendarza.")
        else:
            labels = [
                f"R{race.get('round')} · {race.get('raceName')}"
                for race in schedule
            ]
            selected_label = st.selectbox(
                "Wybierz Grand Prix",
                labels,
                index=focus_race_index(schedule),
                key=f"weekend_race_{SEASON}",
            )
            race = schedule[labels.index(selected_label)]
            sessions = race_sessions(race)
            location = race.get("Circuit", {}).get("Location", {})
            circuit = race.get("Circuit", {}).get("circuitName", "—")
            locality = location.get("locality", "")
            country = location.get("country", "")
            place = ", ".join(x for x in [locality, country] if x)

            if sessions:
                start_local = sessions[0][0].astimezone(WARSAW)
                end_local = sessions[-1][0].astimezone(WARSAW)
                if start_local.date() == end_local.date():
                    date_range = start_local.strftime("%d.%m.%Y")
                else:
                    date_range = (
                        f"{start_local.strftime('%d.%m')} – "
                        f"{end_local.strftime('%d.%m.%Y')}"
                    )
            else:
                date_range = "—"

            render_weekend_header(
                race.get("round", "—"),
                race.get("raceName", "Grand Prix"),
                circuit,
                place,
                date_range,
            )

            openf1_sessions = match_openf1_sessions_to_race(season_openf1, race)
            sessions = effective_sessions(race, openf1_sessions)

            _, openf1_map = build_session_options(race, openf1_sessions)
            now = datetime.now(timezone.utc)
            states = weekend_states(race, openf1_sessions, now)
            completed = sum(1 for state, _ in states.values() if state == "ZAKOŃCZONA")
            total = len(states)
            progress = completed / total if total else 0

            st.markdown(
                (
                    '<div class="weekend-progress-head">'
                    f'<span>Postęp weekendu</span><span>{completed}/{total} sesji</span>'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )
            st.progress(progress)

            next_sessions = [(dt, label) for dt, label in sessions if dt > now]
            if next_sessions:
                next_dt, next_label = min(next_sessions, key=lambda item: item[0])
                render_session_card(
                    gp="NASTĘPNA SESJA",
                    session=next_label,
                    countdown=countdown(next_dt),
                    details=format_local_datetime(next_dt),
                )
            elif weekend_finished(states):
                st.success("Weekend został zakończony według danych OpenF1.")
            elif sessions:
                st.info("Brak następnej sesji w planie. Zakończenie weekendu nie jest jeszcze potwierdzone.")

            render_section_title("🗓️ Harmonogram weekendu")

            polish_days = {
                0: "Poniedziałek",
                1: "Wtorek",
                2: "Środa",
                3: "Czwartek",
                4: "Piątek",
                5: "Sobota",
                6: "Niedziela",
            }

            for dt, label in sessions:
                openf1_session = openf1_map.get(label)
                state, note = states[label]
                local = dt.astimezone(WARSAW)
                render_weekend_session(
                    label=label,
                    dt_text=local.strftime("%d.%m · %H:%M"),
                    day_text=polish_days.get(local.weekday(), ""),
                    state=state,
                    note=note,
                )

            for label, (state, note) in states.items():
                if state == "BRAK GODZINY":
                    render_weekend_session(label, "Godzina nieznana", "—", state, note)

            render_section_title("⏱️ Szybkie wyniki")
            finished_labels = [label for label, (state, _) in states.items() if state == "ZAKOŃCZONA"]
            if not finished_labels:
                render_empty("Brak sesji z potwierdzoną godziną zakończenia. Wyniki można sprawdzić w sekcji Wyniki.")
            else:
                quick_session = st.selectbox(
                    "Sesja do podglądu",
                    list(reversed(finished_labels)),
                    key=f"weekend_quick_results_{SEASON}_{race.get('round')}",
                )
                quick = load_normalized_results(race, quick_session, openf1_sessions, saved)
                show_result_status(quick)
                quick_results, quick_source = quick.rows, quick.source

                if not quick_results:
                    if quick.state == "empty":
                        render_empty("Dostawca nie opublikował jeszcze wyników tej sesji.")
                else:
                    st.caption(f"Top 5 · źródło: {quick_source}")
                    render_result_rows(quick_results, limit=5)

            render_section_title("🏆 Aktualna klasyfikacja wybranego sezonu")
            standings_drivers_tab, standings_teams_tab = st.tabs(
                ["Top 3 kierowców", "Top 3 konstruktorów"]
            )

            with standings_drivers_tab:
                podium = []
                for row in driver_standings[:3]:
                    driver = row.get("Driver", {})
                    podium.append(
                        (
                            row.get("position", "—"),
                            f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                            row.get("points", "0"),
                        )
                    )
                if podium:
                    render_podium_cards(podium)
                else:
                    render_empty("Klasyfikacja kierowców nie jest dostępna.")

            with standings_teams_tab:
                podium = []
                for row in constructor_standings[:3]:
                    constructor = row.get("Constructor", {})
                    podium.append(
                        (
                            row.get("position", "—"),
                            constructor.get("name", "—"),
                            row.get("points", "0"),
                        )
                    )
                if podium:
                    render_podium_cards(podium)
                else:
                    render_empty("Klasyfikacja konstruktorów nie jest dostępna.")

            render_metric_cards(
                [
                    ("Runda", f"{race.get('round', '—')}/{len(schedule)}", "sezon"),
                    ("Tor", circuit, place or "—"),
                    ("Sesje", str(total), f"{completed} zakończonych"),
                ],
                columns=3,
            )

    # ============================================================
    # KALENDARZ
    # ============================================================
    elif nav == "Kalendarz":
        render_section_title(f"📅 Kalendarz sezonu {SEASON}")

        if not schedule:
            render_empty("Kalendarz nie jest teraz dostępny.")
        else:
            now = datetime.now(timezone.utc)
            filter_mode = st.radio(
                "Pokaż",
                ["Najbliższe", "Cały sezon", "Zakończone", "Niepotwierdzone"],
                horizontal=True,
            )

            selected = []
            for race in schedule:
                race_dt = session_datetime({"date": race.get("date"), "time": race.get("time")})
                matched = match_openf1_sessions_to_race(season_openf1, race)
                states = weekend_states(race, matched, now)
                finished = weekend_finished(states)
                uncertain = any(state in ("NIEPOTWIERDZONA", "BRAK GODZINY") for state, _ in states.values())
                if filter_mode == "Cały sezon" or (filter_mode == "Zakończone" and finished):
                    selected.append(race)
                elif filter_mode == "Najbliższe" and not finished and (race_dt is None or race_dt >= now or any(state == "TRWA" for state, _ in states.values())):
                    selected.append(race)
                elif filter_mode == "Niepotwierdzone" and uncertain:
                    selected.append(race)

            if filter_mode == "Najbliższe":
                selected = selected[:6]
            elif filter_mode == "Zakończone":
                selected = list(reversed(selected))

            if not selected:
                render_empty("Brak weekendów spełniających wybrany filtr.")

            for race in selected:
                race_dt = session_datetime({"date": race.get("date"), "time": race.get("time")})
                location = race.get("Circuit", {}).get("Location", {})
                matched = match_openf1_sessions_to_race(season_openf1, race)
                states = weekend_states(race, matched, now)
                state = "ZAKOŃCZONE" if weekend_finished(states) else "TRWA" if any(s == "TRWA" for s, _ in states.values()) else "NADCHODZI" if race_dt and race_dt > now else "NIEPOTWIERDZONE"
                title = (
                    f"R{race.get('round', '?')} · {race.get('raceName', 'Grand Prix')} "
                    f"— {format_local_datetime(race_dt, short=True) if race_dt else ''}"
                )
                with st.expander(title):
                    st.markdown(
                        f"""
                        <div class="calendar-head">
                            <span>{status_badge(state)}</span>
                            <strong>{escape(race.get('Circuit', {}).get('circuitName', ''))}</strong>
                            <span class="muted">{escape(location.get('locality', ''))}, {escape(location.get('country', ''))}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    for label, (session_status, note) in states.items():
                        dt = dict((label, dt) for dt, label in effective_sessions(race, matched)).get(label)
                        render_weekend_session(label, format_local_datetime(dt) if dt else "Godzina nieznana", "", session_status, note)

    # ============================================================
    # WYNIKI
    # ============================================================
    elif nav == "Wyniki":
        render_section_title("⏱️ Wyniki sesji")

        if not schedule:
            render_empty("Nie można wybrać weekendu bez danych kalendarza.")
        else:
            now = datetime.now(timezone.utc)
            completed_or_current = []
            for race in schedule:
                first_dt = race_sessions(race)[0][0] if race_sessions(race) else None
                if first_dt and first_dt <= now:
                    completed_or_current.append(race)

            default_index = max(0, len(completed_or_current) - 1)
            race_options = schedule
            labels = [
                f"R{race.get('round')} · {race.get('raceName')}"
                for race in race_options
            ]

            selected_label = st.selectbox(
                "Weekend Grand Prix",
                labels,
                index=min(default_index, len(labels) - 1),
            )
            race = race_options[labels.index(selected_label)]

            # OpenF1 zapewnia wyniki wszystkich typów sesji; Jolpica jest fallbackiem.
            openf1_sessions = match_openf1_sessions_to_race(season_openf1, race)

            session_names, _ = build_session_options(race, openf1_sessions)
            states = weekend_states(race, openf1_sessions)
            finished = [label for label, (state, _) in states.items() if state == "ZAKOŃCZONA"]
            default_session = session_names.index(finished[-1]) if finished else 0
            selected_session = st.selectbox("Sesja", session_names, index=default_session, key=f"result_session_{SEASON}_{race.get('round')}")
            result = load_normalized_results(race, selected_session, openf1_sessions, saved)
            show_result_status(result)
            results, source = result.rows, result.source

            if not results:
                if result.state == "empty":
                    render_empty("Dostawca nie opublikował jeszcze wyników tej sesji.")
            else:
                st.caption(f"Źródło danych: {source}")
                render_result_rows(results)


    # ============================================================
    # KLASYFIKACJE
    # ============================================================
    elif nav == "Klasyfikacje":
        render_section_title("🏆 Klasyfikacje mistrzostw")

        tab_drivers, tab_teams = st.tabs(["Kierowcy", "Konstruktorzy"])

        with tab_drivers:
            if not driver_standings:
                render_empty("Klasyfikacja kierowców nie jest dostępna.")
            for row in driver_standings:
                st.markdown(driver_row_html(row, full=True), unsafe_allow_html=True)

        with tab_teams:
            if not constructor_standings:
                render_empty("Klasyfikacja konstruktorów nie jest dostępna.")
            for row in constructor_standings:
                constructor = row.get("Constructor", {})
                st.markdown(
                    f"""
                    <div class="standing-row">
                        <div class="standing-pos">{escape(str(row.get('position', '—')))}</div>
                        <div class="standing-main">
                            <div class="standing-name">{escape(constructor.get('name', '—'))}</div>
                            <div class="standing-team">{escape(constructor.get('nationality', ''))}</div>
                        </div>
                        <div class="standing-points">
                            {escape(str(row.get('points', '0')))}<small> pkt</small>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # ============================================================
    # KIEROWCY
    # ============================================================
    elif nav == "Kierowcy":
        render_section_title("👤 Kierowcy")

        if not driver_standings:
            render_empty("Lista kierowców nie jest dostępna.")
        else:
            driver_labels = []
            by_label = {}
            for row in driver_standings:
                d = row.get("Driver", {})
                label = f"{d.get('givenName', '')} {d.get('familyName', '')}"
                driver_labels.append(label)
                by_label[label] = row

            selected = st.selectbox("Wybierz kierowcę", driver_labels)
            standing = by_label[selected]
            driver = standing.get("Driver", {})
            constructors = standing.get("Constructors", [])
            team = " / ".join(c.get("name") or "—" for c in constructors) or "—"

            st.markdown(
                f"""
                <div class="driver-profile">
                    <div class="eyebrow">{escape(driver.get('code', ''))} · #{escape(driver.get('permanentNumber', '—'))}</div>
                    <div class="profile-name">{escape(selected)}</div>
                    <div class="muted">{escape(team)} · {escape(driver.get('nationality', ''))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            render_metric_cards(
                [
                    ("Pozycja", f"P{standing.get('position', '—')}", "mistrzostwa"),
                    ("Punkty", str(standing.get("points", "0")), "pkt"),
                    ("Zwycięstwa", str(standing.get("wins", "0")), "w sezonie"),
                ],
                columns=3,
            )

            render_section_title("📈 Ostatnie 5 startów kierowcy")
            races = read_data("Wyniki kierowcy", get_driver_race_results, SEASON, driver.get("driverId"))
            if st.session_state.source_info:
                st.caption(st.session_state.source_info[-1])

            recent = sorted(races, key=lambda race: safe_int(race.get("round")))[-5:]
            if not recent:
                render_empty("Brak wyników wyścigowych dla tego kierowcy.")
            else:
                form = []
                for race in recent:
                    result_rows = race.get("Results", [])
                    result = result_rows[0] if result_rows else {}
                    position = result.get("positionText") or result.get("position") or "—"
                    form.append(position)

                    st.markdown(
                        f"""
                        <div class="form-row">
                            <div>
                                <strong>{escape(race.get('raceName', 'Grand Prix'))}</strong>
                                <div class="muted">R{escape(str(race.get('round', '')))}</div>
                            </div>
                            <div class="form-position">{escape(position_label(position))}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                st.markdown(
                    f"""
                    <div class="form-strip">
                        <span>FORMA</span>
                        <strong>{' · '.join(escape(position_label(x)) for x in form)}</strong>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if safe_url(driver.get("url")):
                st.link_button(
                    "Więcej o kierowcy",
                    safe_url(driver["url"]),
                    use_container_width=True,
                )

    st.markdown(
        """
        <div class="footer">
            Marcin F1 Hub 2.2 · dane: Jolpica / OpenF1 · godziny: Europe/Warsaw
        </div>
        """,
        unsafe_allow_html=True,
    )

render_page(nav, season)
