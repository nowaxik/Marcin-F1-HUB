"""Partial failures retain usable data and carry explicit diagnostics."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import f1_api as api
from domain import build_session_options, safe_int, text

@dataclass
class LoadResult:
    rows: list = field(default_factory=list)
    source: str | None = None
    fetched_at: datetime | None = None
    warnings: list[str] = field(default_factory=list)
    state: str = 'empty'

def load_source(getter, args, saved, key, now=None):
    """Per-user last good snapshot and 60-second retry cooldown, no hidden disk writes."""
    now = now or datetime.now(timezone.utc)
    previous = saved.get(key)
    if previous and previous.get('error') and (now - previous['attempt']).total_seconds() < 60:
        rows = previous['rows']
        return LoadResult(rows, fetched_at=previous['fetched_at'], warnings=[previous['error']], state='stale' if rows else 'error')
    try:
        rows = getter(*args)
        fetched_at = getattr(rows, 'fetched_at', now)
        saved[key] = dict(rows=rows, fetched_at=fetched_at, attempt=now, error=None)
        return LoadResult(rows, fetched_at=fetched_at, state='ready' if rows else 'empty')
    except api.APIError as exc:
        rows = previous['rows'] if previous else []
        stamp = previous['fetched_at'] if previous else None
        saved[key] = dict(rows=rows, fetched_at=stamp, attempt=now, error=str(exc))
        return LoadResult(rows, fetched_at=stamp, warnings=[str(exc)], state='stale' if rows else exc.kind)

def load_normalized_results(race, selected_session, openf1_sessions, saved):
    _, mapping = build_session_options(race, openf1_sessions)
    session = mapping.get(selected_session)
    result = LoadResult()
    if session and session.get('session_key'):
        key = session['session_key']
        raw = load_source(api.get_openf1_results, (key,), saved, ('results', key))
        result.warnings.extend(raw.warnings)
        if raw.rows:
            drivers = load_source(api.get_openf1_drivers, (key,), saved, ('drivers', key))
            result.warnings.extend('Opisy kierowców: ' + warning for warning in drivers.warnings)
            by_number = {safe_int(d.get('driver_number')): d for d in drivers.rows}
            for row in raw.rows:
                d = by_number.get(safe_int(row.get('driver_number')), {})
                result.rows.append(dict(position=row.get('position'),
                    name=text(d.get('full_name') or d.get('broadcast_name'), f"#{row.get('driver_number')}"),
                    team=text(d.get('team_name')), duration=row.get('duration'), gap=row.get('gap_to_leader'),
                    laps=row.get('number_of_laps'), status='DSQ' if row.get('dsq') else 'DNS' if row.get('dns') else 'DNF' if row.get('dnf') else ''))
            result.source, result.fetched_at = 'OpenF1', raw.fetched_at
            result.state = raw.state
    if not result.rows:
        legacy = {'Kwalifikacje': 'qualifying', 'Sprint': 'sprint', 'Wyścig': 'race'}.get(selected_session)
        if legacy:
            season = safe_int(race.get('season'), datetime.now(timezone.utc).year)
            round_no = safe_int(race.get('round'))
            raw = load_source(api.get_session_results, (season, round_no, legacy), saved, ('legacy', season, round_no, legacy))
            result.warnings.extend(raw.warnings)
            for row in raw.rows:
                driver = row.get('Driver') or {}
                time = row.get('Time') or {}
                result.rows.append(dict(position=row.get('position'), name=(text(driver.get('givenName'), '') + ' ' + text(driver.get('familyName'), '')).strip() or '—',
                    team=text((row.get('Constructor') or {}).get('name')),
                    duration=[row.get('Q1'), row.get('Q2'), row.get('Q3')] if legacy == 'qualifying' else time.get('time'),
                    gap=None, laps=row.get('laps'), status='' if legacy == 'qualifying' else text(row.get('status'), '')))
            if raw.rows:
                result.source, result.fetched_at, result.state = 'Jolpica', raw.fetched_at, raw.state
    if not result.rows:
        result.state = 'error' if result.warnings else 'empty'
        if not session and selected_session not in ('Wyścig', 'Sprint', 'Kwalifikacje'):
            result.state = 'unavailable'
            result.warnings.append('Brak danych sesji OpenF1 potrzebnych do wyszukania wyników. Spróbuj ponownie później.')
    result.rows.sort(key=lambda row: safe_int(row.get('position'), 999))
    return result
