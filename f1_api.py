from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import quote

import requests
import streamlit as st


JOLPICA = "https://api.jolpi.ca/ergast/f1"
OPENF1 = "https://api.openf1.org/v1"


class APIError(RuntimeError):
    pass


def _get_json(url: str, timeout: int = 12) -> Any:
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "MarcinF1Hub/2.0"},
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise APIError(f"Problem z połączeniem z API ({exc})") from exc
    except ValueError as exc:
        raise APIError("API zwróciło nieprawidłowe dane JSON.") from exc


@st.cache_data(ttl=300, show_spinner=False)
def get_schedule(season: int) -> list[dict]:
    data = _get_json(f"{JOLPICA}/{season}.json?limit=100")
    return data.get("MRData", {}).get("RaceTable", {}).get("Races", [])


@st.cache_data(ttl=300, show_spinner=False)
def get_driver_standings(season: int) -> list[dict]:
    data = _get_json(f"{JOLPICA}/{season}/driverStandings.json?limit=100")
    lists = data.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
    return lists[0].get("DriverStandings", []) if lists else []


@st.cache_data(ttl=300, show_spinner=False)
def get_constructor_standings(season: int) -> list[dict]:
    data = _get_json(f"{JOLPICA}/{season}/constructorStandings.json?limit=100")
    lists = data.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
    return lists[0].get("ConstructorStandings", []) if lists else []


@st.cache_data(ttl=300, show_spinner=False)
def get_driver_race_results(season: int, driver_id: str) -> list[dict]:
    if not driver_id:
        return []
    data = _get_json(
        f"{JOLPICA}/{season}/drivers/{quote(driver_id)}/results.json?limit=100"
    )
    return data.get("MRData", {}).get("RaceTable", {}).get("Races", [])


@st.cache_data(ttl=180, show_spinner=False)
def get_session_results(season: int, round_no: int, session: str) -> list[dict]:
    session = session.lower().strip()
    if session == "race":
        suffix = "results"
        key = "Results"
    elif session == "qualifying":
        suffix = "qualifying"
        key = "QualifyingResults"
    elif session == "sprint":
        suffix = "sprint"
        key = "SprintResults"
    else:
        return []

    data = _get_json(
        f"{JOLPICA}/{season}/{round_no}/{suffix}.json?limit=100"
    )
    races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
    return races[0].get(key, []) if races else []


@st.cache_data(ttl=600, show_spinner=False)
def get_openf1_sessions(season: int) -> list[dict]:
    data = _get_json(f"{OPENF1}/sessions?year={season}", timeout=15)
    return data if isinstance(data, list) else []


@st.cache_data(ttl=180, show_spinner=False)
def get_openf1_results(session_key: int | str) -> list[dict]:
    data = _get_json(f"{OPENF1}/session_result?session_key={session_key}", timeout=15)
    return data if isinstance(data, list) else []


@st.cache_data(ttl=600, show_spinner=False)
def get_openf1_drivers(session_key: int | str) -> list[dict]:
    data = _get_json(f"{OPENF1}/drivers?session_key={session_key}", timeout=15)
    return data if isinstance(data, list) else []


def _parse_iso(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def match_openf1_sessions_to_race(
    sessions: list[dict], race: dict
) -> list[dict]:
    """
    Dopasowanie po oknie czasowym wokół daty wyścigu.
    To jest odporniejsze niż porównywanie nazw państw/circuitów,
    które różnią się między dostawcami danych.
    """
    race_date = race.get("date")
    if not race_date:
        return []

    try:
        race_day = datetime.fromisoformat(race_date).replace(tzinfo=timezone.utc)
    except ValueError:
        return []

    start = race_day - timedelta(days=4)
    end = race_day + timedelta(days=1, hours=12)

    matched = []
    for session in sessions:
        dt = _parse_iso(session.get("date_start"))
        if dt and start <= dt <= end:
            matched.append(session)

    # Jeśli w oknie znalazły się dwa meetingi, wybierz ten najbliższy dacie wyścigu.
    if not matched:
        return []

    by_meeting: dict[Any, list[dict]] = {}
    for item in matched:
        by_meeting.setdefault(item.get("meeting_key"), []).append(item)

    if len(by_meeting) == 1:
        chosen = matched
    else:
        def distance(items):
            starts = [_parse_iso(x.get("date_start")) for x in items]
            starts = [x for x in starts if x]
            if not starts:
                return 10**12
            return min(abs((x - race_day).total_seconds()) for x in starts)

        chosen = min(by_meeting.values(), key=distance)

    return sorted(
        chosen,
        key=lambda x: _parse_iso(x.get("date_start")) or datetime.max.replace(tzinfo=timezone.utc),
    )
