"""Shared domain rules, independent of HTTP and Streamlit."""
from datetime import datetime, timedelta, timezone
from math import isfinite
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

WARSAW = ZoneInfo('Europe/Warsaw')
SESSION_NAMES = {'FirstPractice': 'FP1', 'SecondPractice': 'FP2', 'ThirdPractice': 'FP3',
                 'SprintQualifying': 'Kwalifikacje sprintu', 'Sprint': 'Sprint', 'Qualifying': 'Kwalifikacje'}

def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError, OverflowError):
        return default

def text(value, default='—'):
    return str(value) if isinstance(value, (str, int, float)) and value != '' else default

def parse_datetime(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.astimezone(timezone.utc) if dt.tzinfo is not None else None
    except (ValueError, OverflowError):
        return None

def session_datetime(payload):
    if not isinstance(payload, dict) or not payload.get('date') or not payload.get('time'):
        return None
    return parse_datetime(f"{payload['date']}T{payload['time']}")

def race_sessions(race):
    items = [(session_datetime(race.get(key)), label) for key, label in SESSION_NAMES.items() if key in race]
    items.append((session_datetime(race), 'Wyścig'))
    return sorted([(dt, label) for dt, label in items if dt], key=lambda x: x[0])

def unknown_sessions(race):
    items = [label for key, label in SESSION_NAMES.items() if key in race and not session_datetime(race.get(key))]
    return items + ([] if session_datetime(race) else ['Wyścig'])

def format_session_name(name):
    name = text(name, 'Sesja')
    return {'practice 1': 'FP1', 'practice 2': 'FP2', 'practice 3': 'FP3',
            'sprint qualifying': 'Kwalifikacje sprintu', 'sprint shootout': 'Kwalifikacje sprintu',
            'sprint': 'Sprint', 'qualifying': 'Kwalifikacje', 'race': 'Wyścig'}.get(name.strip().lower(), name)

def build_session_options(race, openf1_sessions):
    mapping = {}
    ordered = sorted(openf1_sessions, key=lambda x: parse_datetime(x.get('date_start')) or datetime.min.replace(tzinfo=timezone.utc))
    for session in ordered:
        mapping[format_session_name(session.get('session_name') or session.get('session_type'))] = session
    options = list(dict.fromkeys([label for _, label in race_sessions(race)] + unknown_sessions(race) + list(mapping)))
    return options, mapping

def effective_sessions(race, openf1_sessions):
    _, mapping = build_session_options(race, openf1_sessions)
    planned = dict((label, dt) for dt, label in race_sessions(race))
    for label, session in mapping.items():
        start = parse_datetime(session.get('date_start'))
        if start:
            planned[label] = start
    return sorted((dt, label) for label, dt in planned.items())

def countdown(target, now=None):
    seconds = max(0, int((target - (now or datetime.now(timezone.utc))).total_seconds()))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    return (f'{days} dni · ' if days else '') + f'{hours:02d} h · {seconds // 60:02d} min'

def session_state(label, dt, openf1_session=None, all_sessions=(), now=None):
    now = now or datetime.now(timezone.utc)
    metadata = openf1_session or {}
    start = parse_datetime(metadata.get('date_start')) or dt
    end = parse_datetime(metadata.get('date_end'))
    if not start:
        return 'BRAK GODZINY', 'Godzina startu nie została potwierdzona.'
    if start > now:
        future = [(sdt, name) for sdt, name in all_sessions if sdt > now]
        next_label = min(future)[1] if future else label
        return ('NASTĘPNA', f'Start za {countdown(start, now)}') if label == next_label else ('NADCHODZI', '')
    if end and end > start:
        if now < end:
            return 'TRWA', 'Według godzin OpenF1; opóźnienia mogą zmienić przebieg sesji.'
        return 'ZAKOŃCZONA', 'Według czasu zakończenia podanego przez OpenF1.'
    return 'NIEPOTWIERDZONA', 'Minął planowany start; brak potwierdzonej godziny zakończenia.'

def weekend_states(race, openf1_sessions, now=None):
    sessions = effective_sessions(race, openf1_sessions)
    options, mapping = build_session_options(race, openf1_sessions)
    times = dict((label, dt) for dt, label in sessions)
    return {label: session_state(label, times.get(label), mapping.get(label), sessions, now) for label in options}

def weekend_finished(states):
    return bool(states) and all(state == 'ZAKOŃCZONA' for state, _ in states.values())

def focus_race_index(schedule, now=None):
    now = now or datetime.now(timezone.utc)
    for i, race in enumerate(schedule):
        sessions = race_sessions(race)
        if sessions and sessions[0][0] <= now <= sessions[-1][0] + timedelta(hours=5):
            return i
    for i, race in enumerate(schedule):
        sessions = race_sessions(race)
        if sessions and sessions[0][0] > now:
            return i
    return max(0, len(schedule) - 1)

def find_next_session(schedule, now=None):
    now = now or datetime.now(timezone.utc)
    future = [(dt, label, race) for race in schedule for dt, label in race_sessions(race) if dt > now]
    return min(future, key=lambda x: x[0]) if future else None

def seconds_to_time(value):
    if not isfinite(value) or value < 0:
        return ''
    hours, remainder = divmod(round(value * 1000), 3600000)
    minutes, remainder = divmod(remainder, 60000)
    seconds, millis = divmod(remainder, 1000)
    prefix = f'{hours}:{minutes:02d}' if hours else str(minutes)
    return f'{prefix}:{seconds:02d}.{millis:03d}'

def position_label(value):
    value = text(value)
    return f'P{value}' if value.isdigit() else {'R': 'DNF', 'D': 'DSQ', 'E': 'EXC', 'W': 'DNS', 'F': 'DNQ', 'N': 'NC'}.get(value, value)

def safe_url(value):
    if not isinstance(value, str):
        return None
    try:
        url = urlsplit(value)
        return value if url.scheme in ('http', 'https') and url.netloc else None
    except ValueError:
        return None
