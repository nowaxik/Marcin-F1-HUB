from datetime import datetime, timezone
from html import escape
from zoneinfo import ZoneInfo

import streamlit as st

from f1_api import (
    APIError,
    get_constructor_standings,
    get_driver_race_results,
    get_driver_standings,
    get_openf1_drivers,
    get_openf1_results,
    get_openf1_sessions,
    get_schedule,
    get_session_results,
    match_openf1_sessions_to_race,
)
from ui import (
    apply_styles,
    driver_row_html,
    format_duration,
    format_gap,
    format_local_datetime,
    format_session_name,
    render_empty,
    render_error,
    render_hero,
    render_metric_cards,
    render_section_title,
    render_session_card,
    status_badge,
)

st.set_page_config(
    page_title="Marcin F1 Hub",
    page_icon="🏎️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

apply_styles()

SEASON = datetime.now().year
WARSAW = ZoneInfo("Europe/Warsaw")
X_PROFILE = "https://x.com/MarcinNov"


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def session_datetime(payload):
    if not payload:
        return None
    date = payload.get("date")
    time = payload.get("time") or "00:00:00Z"
    if not date:
        return None
    return datetime.fromisoformat(f"{date}T{time.replace('Z', '+00:00')}")


def race_sessions(race):
    mapping = [
        ("FirstPractice", "FP1"),
        ("SecondPractice", "FP2"),
        ("ThirdPractice", "FP3"),
        ("SprintQualifying", "Kwalifikacje sprintu"),
        ("Sprint", "Sprint"),
        ("Qualifying", "Kwalifikacje"),
    ]
    items = []
    for key, label in mapping:
        payload = race.get(key)
        if payload:
            dt = session_datetime(payload)
            if dt:
                items.append((dt, label))
    race_dt = session_datetime({"date": race.get("date"), "time": race.get("time")})
    if race_dt:
        items.append((race_dt, "Wyścig"))
    return sorted(items, key=lambda x: x[0])


def find_next_session(schedule):
    now = datetime.now(timezone.utc)
    upcoming = []
    for race in schedule:
        for dt, label in race_sessions(race):
            if dt > now:
                upcoming.append((dt, label, race))
    return min(upcoming, key=lambda x: x[0]) if upcoming else None


def countdown(target):
    seconds = max(0, int((target - datetime.now(timezone.utc)).total_seconds()))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, _ = divmod(seconds, 60)
    if days:
        return f"{days} dni · {hours:02d} h · {minutes:02d} min"
    return f"{hours:02d} h · {minutes:02d} min"


@st.cache_data(ttl=300, show_spinner=False)
def load_core():
    return get_schedule(SEASON), get_driver_standings(SEASON), get_constructor_standings(SEASON)


try:
    schedule, driver_standings, constructor_standings = load_core()
except APIError as exc:
    schedule, driver_standings, constructor_standings = [], [], []
    st.error(f"Nie udało się pobrać podstawowych danych F1: {exc}")


render_hero(
    kicker=f"FORMULA 1 · SEZON {SEASON}",
    title="MARCIN F1 HUB",
    subtitle="Kalendarz, wyniki, klasyfikacje i forma kierowców — w jednym miejscu.",
)

nav = st.radio(
    "Nawigacja",
    ["Start", "Kalendarz", "Wyniki", "Klasyfikacje", "Kierowcy"],
    horizontal=True,
    label_visibility="collapsed",
)

# ============================================================
# START
# ============================================================
if nav == "Start":
    next_item = find_next_session(schedule) if schedule else None

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

    if driver_standings and constructor_standings:
        leader = driver_standings[0]
        constructor_leader = constructor_standings[0]
        driver = leader.get("Driver", {})
        render_metric_cards(
            [
                (
                    "Lider kierowców",
                    f"{driver.get('givenName', '')} {driver.get('familyName', '')}",
                    f"{leader.get('points', '0')} pkt",
                ),
                (
                    "Lider konstruktorów",
                    constructor_leader.get("Constructor", {}).get("name", "—"),
                    f"{constructor_leader.get('points', '0')} pkt",
                ),
            ]
        )

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
            <strong>F1 Hub 2.0</strong><br>
            Dane sportowe są pobierane automatycznie. Wyniki sesji mogą pojawić się
            kilka minut po publikacji oficjalnych rezultatów.
        </div>
        """,
        unsafe_allow_html=True,
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
            ["Najbliższe", "Cały sezon", "Zakończone"],
            horizontal=True,
        )

        selected = []
        for race in schedule:
            race_dt = session_datetime({"date": race.get("date"), "time": race.get("time")})
            if not race_dt:
                continue
            if filter_mode == "Najbliższe" and race_dt >= now:
                selected.append(race)
            elif filter_mode == "Zakończone" and race_dt < now:
                selected.append(race)
            elif filter_mode == "Cały sezon":
                selected.append(race)

        if filter_mode == "Najbliższe":
            selected = selected[:6]
        elif filter_mode == "Zakończone":
            selected = list(reversed(selected))

        for race in selected:
            race_dt = session_datetime({"date": race.get("date"), "time": race.get("time")})
            location = race.get("Circuit", {}).get("Location", {})
            state = "NADCHODZI" if race_dt and race_dt >= now else "ZAKOŃCZONE"
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
                for dt, label in race_sessions(race):
                    st.markdown(
                        f"""
                        <div class="session-line">
                            <span>{escape(label)}</span>
                            <strong>{format_local_datetime(dt)}</strong>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

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
        round_no = safe_int(race.get("round"))

        # Najpierw próbujemy OpenF1, bo obsługuje FP, sprint, kwalifikacje i wyścig.
        openf1_sessions = []
        try:
            season_sessions = get_openf1_sessions(SEASON)
            openf1_sessions = match_openf1_sessions_to_race(season_sessions, race)
        except APIError:
            openf1_sessions = []

        session_names = []
        session_map = {}
        for sess in openf1_sessions:
            raw_name = sess.get("session_name") or sess.get("session_type") or "Sesja"
            pretty = format_session_name(raw_name)
            # zachowaj unikalność
            display = pretty
            counter = 2
            while display in session_map:
                display = f"{pretty} {counter}"
                counter += 1
            session_map[display] = sess
            session_names.append(display)

        # Fallback na stabilne endpointy wyścig / kwalifikacje / sprint.
        legacy_names = ["Kwalifikacje", "Sprint", "Wyścig"]
        for name in legacy_names:
            if name not in session_names:
                session_names.append(name)
                session_map[name] = None

        selected_session = st.selectbox("Sesja", session_names)
        selected_openf1 = session_map.get(selected_session)

        results = []
        source = None

        if selected_openf1 and selected_openf1.get("session_key"):
            try:
                session_key = selected_openf1["session_key"]
                raw_results = get_openf1_results(session_key)
                drivers = get_openf1_drivers(session_key)
                drivers_by_number = {
                    safe_int(d.get("driver_number")): d for d in drivers
                }
                for row in raw_results:
                    d = drivers_by_number.get(safe_int(row.get("driver_number")), {})
                    results.append(
                        {
                            "position": row.get("position"),
                            "name": d.get("full_name") or d.get("broadcast_name") or f"#{row.get('driver_number')}",
                            "code": d.get("name_acronym", ""),
                            "team": d.get("team_name", "—"),
                            "duration": row.get("duration"),
                            "gap": row.get("gap_to_leader"),
                            "laps": row.get("number_of_laps"),
                            "status": (
                                "DSQ" if row.get("dsq")
                                else "DNS" if row.get("dns")
                                else "DNF" if row.get("dnf")
                                else ""
                            ),
                        }
                    )
                source = "OpenF1"
            except APIError:
                results = []

        if not results:
            legacy_key = {
                "Kwalifikacje": "qualifying",
                "Sprint": "sprint",
                "Wyścig": "race",
            }.get(selected_session)

            if legacy_key:
                try:
                    rows = get_session_results(SEASON, round_no, legacy_key)
                    for row in rows:
                        driver = row.get("Driver", {})
                        constructors = row.get("Constructors", [])
                        team = constructors[0].get("name", "—") if constructors else "—"

                        if legacy_key == "qualifying":
                            duration = [row.get("Q1"), row.get("Q2"), row.get("Q3")]
                            gap = None
                            laps = None
                            status = ""
                        else:
                            time_obj = row.get("Time") or {}
                            duration = time_obj.get("time") or row.get("status")
                            gap = None
                            laps = row.get("laps")
                            status = row.get("status", "")

                        results.append(
                            {
                                "position": row.get("position"),
                                "name": f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip(),
                                "code": driver.get("code", ""),
                                "team": team,
                                "duration": duration,
                                "gap": gap,
                                "laps": laps,
                                "status": status,
                            }
                        )
                    source = "Jolpica"
                except APIError:
                    results = []

        if not results:
            render_empty(
                "Dla tej sesji nie ma jeszcze dostępnych rezultatów. "
                "Jeżeli sesja właśnie się zakończyła, spróbuj ponownie za kilka minut."
            )
        else:
            st.caption(f"Źródło danych: {source}")
            for row in sorted(results, key=lambda r: safe_int(r.get("position"), 999)):
                pos = row.get("position") or "—"
                duration = format_duration(row.get("duration"))
                gap = format_gap(row.get("gap"))
                laps = row.get("laps")
                status = row.get("status") or ""

                detail_parts = [row.get("team", "—")]
                if duration:
                    detail_parts.append(duration)
                if gap:
                    detail_parts.append(gap)
                if laps not in (None, ""):
                    detail_parts.append(f"{laps} okr.")
                if status and status not in ("Finished", ""):
                    detail_parts.append(str(status))

                st.markdown(
                    f"""
                    <div class="result-row">
                        <div class="result-pos">{escape(str(pos))}</div>
                        <div class="result-main">
                            <div class="result-name">{escape(row.get('name', '—'))}</div>
                            <div class="result-detail">{escape(' · '.join(detail_parts))}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

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
        team = constructors[0].get("name", "—") if constructors else "—"

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

        render_section_title("📈 Ostatnie 5 wyścigów")
        try:
            races = get_driver_race_results(SEASON, driver.get("driverId"))
        except APIError as exc:
            races = []
            render_error(str(exc))

        recent = races[-5:]
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
                        <div class="form-position">P{escape(str(position))}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown(
                f"""
                <div class="form-strip">
                    <span>FORMA</span>
                    <strong>{' · '.join('P' + escape(str(x)) for x in form)}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if driver.get("url"):
            st.link_button(
                "Więcej o kierowcy",
                driver["url"],
                use_container_width=True,
            )

st.markdown(
    """
    <div class="footer">
        Marcin F1 Hub 2.0 · dane: Jolpica / OpenF1 · godziny: Europe/Warsaw
    </div>
    """,
    unsafe_allow_html=True,
)
