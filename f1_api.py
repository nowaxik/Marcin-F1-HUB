"""Validated HTTP boundary with per-endpoint cached snapshots."""
from datetime import datetime, timedelta, timezone
import logging
from urllib.parse import quote
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st
from domain import parse_datetime, session_datetime

JOLPICA = 'https://api.jolpi.ca/ergast/f1'
OPENF1 = 'https://api.openf1.org/v1'
log = logging.getLogger(__name__)

class APIError(RuntimeError):
    def __init__(self, message, kind='unavailable'):
        super().__init__(message)
        self.kind = kind

class DataRows(list):
    def __init__(self, rows):
        super().__init__(rows)
        self.fetched_at = datetime.now(timezone.utc)

def _get_json(url, timeout=8):
    retry = Retry(total=1, connect=1, read=0, status=1, backoff_factor=0.3,
                  status_forcelist=(502, 503, 504), allowed_methods={'GET'},
                  respect_retry_after_header=False, raise_on_status=False)
    try:
        with requests.Session() as client:
            client.mount('https://', HTTPAdapter(max_retries=retry))
            response = client.get(url, timeout=(4, timeout), headers={'User-Agent': 'MarcinF1Hub/2.2'})
            if response.status_code in (401, 403):
                raise APIError('Dostawca ogranicza dostęp do tych danych.', 'restricted')
            if response.status_code == 429:
                raise APIError('Osiągnięto limit zapytań dostawcy. Spróbuj ponownie później.', 'rate_limit')
            response.raise_for_status()
            try:
                return response.json()
            except ValueError as exc:
                raise APIError('Dostawca zwrócił nieprawidłowy JSON.', 'invalid_data') from exc
    except requests.RequestException as exc:
        log.warning('HTTP request failed: %s (%s)', url, type(exc).__name__)
        raise APIError('Nie udało się połączyć ze źródłem danych.') from exc

def _object(value):
    if not isinstance(value, dict):
        raise APIError('Nieprawidłowa struktura danych dostawcy.', 'invalid_data')
    return value

def _rows(value):
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise APIError('Nieprawidłowa lista rekordów dostawcy.', 'invalid_data')
    return value

def _clean(value):
    if isinstance(value, list):
        return [_clean(item) for item in value]
    if not isinstance(value, dict):
        return value
    cleaned = {}
    for key, item in value.items():
        if key in {'Driver', 'Constructor', 'Circuit', 'Location', 'Time'}:
            cleaned[key] = _clean(_object({} if item is None else item))
        elif key in {'Constructors', 'Results', 'QualifyingResults', 'SprintResults'}:
            cleaned[key] = _clean(_rows(item if item is not None else []))
        else:
            cleaned[key] = _clean(item)
    strings = {'name', 'givenName', 'familyName', 'nationality', 'code', 'permanentNumber',
               'circuitName', 'locality', 'country', 'raceName', 'full_name', 'broadcast_name',
               'name_acronym', 'team_name', 'status', 'positionText'}
    for key in strings & cleaned.keys():
        item = cleaned[key]
        if item is None:
            cleaned[key] = ''
        elif isinstance(item, (str, int, float)):
            cleaned[key] = str(item)
        else:
            raise APIError('Nieprawidłowe pole tekstowe dostawcy.', 'invalid_data')
    return cleaned

def _jolpica(path, table, key):
    data = _object(_get_json(f'{JOLPICA}/{path}.json?limit=100'))
    root = _object(data.get('MRData'))
    return _clean(_rows(_object(root.get(table)).get(key)))

@st.cache_data(ttl=300, show_spinner=False)
def get_schedule(season):
    return DataRows(sorted(_jolpica(str(season), 'RaceTable', 'Races'), key=lambda x: str(x.get('date') or '9999')))

@st.cache_data(ttl=300, show_spinner=False)
def get_driver_standings(season):
    rows = _jolpica(f'{season}/driverStandings', 'StandingsTable', 'StandingsLists')
    return DataRows(_clean(_rows(rows[0].get('DriverStandings'))) if rows else [])

@st.cache_data(ttl=300, show_spinner=False)
def get_constructor_standings(season):
    rows = _jolpica(f'{season}/constructorStandings', 'StandingsTable', 'StandingsLists')
    return DataRows(_clean(_rows(rows[0].get('ConstructorStandings'))) if rows else [])

@st.cache_data(ttl=300, show_spinner=False)
def get_driver_race_results(season, driver_id):
    if not driver_id:
        return DataRows([])
    return DataRows(_jolpica(f'{season}/drivers/{quote(str(driver_id), safe="")}/results', 'RaceTable', 'Races'))

@st.cache_data(ttl=180, show_spinner=False)
def get_session_results(season, round_no, session):
    mapping = {'race': ('results', 'Results'), 'qualifying': ('qualifying', 'QualifyingResults'), 'sprint': ('sprint', 'SprintResults')}
    if session not in mapping:
        return DataRows([])
    suffix, key = mapping[session]
    races = _jolpica(f'{season}/{round_no}/{suffix}', 'RaceTable', 'Races')
    return DataRows(_rows(races[0].get(key)) if races else [])

@st.cache_data(ttl=600, show_spinner=False)
def get_openf1_sessions(season):
    rows = _clean(_rows(_get_json(f'{OPENF1}/sessions?year={int(season)}')))
    for row in rows:
        for key in ('session_key', 'meeting_key'):
            if not isinstance(row.get(key), (int, str)) or not str(row[key]).isdigit():
                raise APIError('Nieprawidłowy identyfikator sesji.', 'invalid_data')
    return DataRows(rows)

@st.cache_data(ttl=180, show_spinner=False)
def get_openf1_results(session_key):
    return DataRows(_clean(_rows(_get_json(f'{OPENF1}/session_result?session_key={int(session_key)}'))))

@st.cache_data(ttl=600, show_spinner=False)
def get_openf1_drivers(session_key):
    return DataRows(_clean(_rows(_get_json(f'{OPENF1}/drivers?session_key={int(session_key)}'))))

def match_openf1_sessions_to_race(sessions, race):
    race_start = session_datetime(race)
    if not race_start:
        try:
            race_start = datetime.fromisoformat(race.get('date', '')).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return []
    meetings = {}
    for session in sessions:
        start = parse_datetime(session.get('date_start'))
        if start and race_start - timedelta(days=4) <= start <= race_start + timedelta(hours=36):
            meetings.setdefault(session.get('meeting_key'), []).append(session)
    if not meetings:
        return []
    def distance(items):
        races = [x for x in items if str(x.get('session_name')).lower() == 'race']
        return (0 if races else 1, min(abs((parse_datetime(x['date_start']) - race_start).total_seconds()) for x in (races or items)))
    return sorted(min(meetings.values(), key=distance), key=lambda x: parse_datetime(x['date_start']))
