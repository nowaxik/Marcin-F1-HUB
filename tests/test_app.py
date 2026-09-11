from datetime import datetime, timedelta, timezone
from pathlib import Path
from copy import deepcopy
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import streamlit as st
from streamlit.testing.v1 import AppTest
import domain as d
import f1_api as api
from services import load_normalized_results, load_source
from ui import format_duration, format_gap

NOW = datetime.now(timezone.utc)
YEAR = NOW.year
START = NOW - timedelta(minutes=10)
END = NOW + timedelta(hours=1)
RACE = dict(season=str(YEAR), round='1', raceName='Test Grand Prix', date=START.date().isoformat(),
            time=START.strftime('%H:%M:%SZ'), FirstPractice={'date': (NOW - timedelta(days=2)).date().isoformat(), 'time': '10:00:00Z'},
            Circuit={'circuitName': 'Test Circuit', 'Location': {'locality': 'Test City', 'country': 'Poland'}})
SESSIONS = [dict(session_key=1, meeting_key=1, session_name='Race', date_start=START.isoformat(), date_end=END.isoformat()),
            dict(session_key=2, meeting_key=1, session_name='Practice 1', date_start=(NOW-timedelta(days=2)).isoformat(), date_end=(NOW-timedelta(days=2,hours=-1)).isoformat())]
DRIVER = dict(driverId='test', givenName='Test', familyName='Driver', code='TST', permanentNumber='44', nationality='Polish', url='https://example.org/driver')
RESULT = dict(position='1', Driver=DRIVER, Constructor={'name': 'Ferrari'}, Time={'time': '1:30:00.000'}, status='Finished', laps='50')

def fixture_http(url, **kwargs):
    if '/sessions?' in url:
        return SESSIONS
    if '/session_result?' in url:
        return [dict(driver_number=44, position=1, duration=91.234, number_of_laps=20)]
    if '/drivers?' in url:
        return [dict(driver_number=44, full_name='Test Driver', team_name='Ferrari')]
    if 'driverStandings' in url:
        return {'MRData': {'StandingsTable': {'StandingsLists': [{'DriverStandings': [dict(position='1', points='100', wins='2', Driver=DRIVER, Constructors=[{'name': 'Ferrari'}])]}]}}}
    if 'constructorStandings' in url:
        return {'MRData': {'StandingsTable': {'StandingsLists': [{'ConstructorStandings': [dict(position='1', points='100', Constructor={'name': 'Ferrari'})]}]}}}
    race = deepcopy(RACE)
    if '/results.' in url:
        race['Results'] = [RESULT]
    elif '/qualifying.' in url:
        race['QualifyingResults'] = [dict(RESULT, Q1='1:31.234')]
    elif '/sprint.' in url:
        race['SprintResults'] = [RESULT]
    return {'MRData': {'RaceTable': {'Races': [race]}}}

class DomainTests(unittest.TestCase):
    def test_live_race_never_completes_weekend(self):
        states = d.weekend_states(RACE, SESSIONS, NOW)
        self.assertEqual(states['Wyścig'][0], 'TRWA')
        self.assertFalse(d.weekend_finished(states))
    def test_start_without_end_is_unknown(self):
        self.assertEqual(d.session_state('Wyścig', START, now=NOW)[0], 'NIEPOTWIERDZONA')
    def test_end_boundary(self):
        self.assertEqual(d.session_state('Wyścig', START, SESSIONS[0], now=END)[0], 'ZAKOŃCZONA')
    def test_unknown_time_preserved(self):
        self.assertIsNone(d.session_datetime({'date': '2026-09-01'}))
        self.assertEqual(d.weekend_states({'date': '2026-09-01'}, [], NOW)['Wyścig'][0], 'BRAK GODZINY')
    def test_invalid_dates_do_not_crash(self):
        for value in ['invalid', '2026-09-01T13:00:00', None, [], {}]:
            self.assertIsNone(d.parse_datetime(value))
    def test_timezone_equivalence_and_dst(self):
        self.assertEqual(d.parse_datetime('2026-09-01T15:00:00+02:00'), d.parse_datetime('2026-09-01T13:00:00Z'))
        self.assertEqual(d.parse_datetime('2026-01-01T13:00:00Z').astimezone(d.WARSAW).hour, 14)
        self.assertEqual(d.parse_datetime('2026-07-01T13:00:00Z').astimezone(d.WARSAW).hour, 15)
    def test_formatting_boundary_and_nonfinite(self):
        self.assertEqual(format_duration(59.9999), '1:00.000')
        self.assertEqual(format_duration(3599.9999), '1:00:00.000')
        for value in [float('nan'), float('inf'), -1]:
            self.assertEqual(format_duration(value), '')
        self.assertEqual(format_gap(float('nan')), '')
    def test_qualification_segments_and_statuses(self):
        self.assertEqual(format_duration([91.234, None, 90.123]), 'Q1 1:31.234 · Q3 1:30.123')
        self.assertEqual(d.position_label('R'), 'DNF')
        self.assertEqual(d.position_label('3'), 'P3')
    def test_safe_link(self):
        self.assertIsNone(d.safe_url('javascript:alert(1)'))
        self.assertEqual(d.safe_url('https://example.org'), 'https://example.org')
    def test_latest_session_and_effective_schedule(self):
        delayed = dict(SESSIONS[0], session_key=3, date_start=(NOW+timedelta(hours=2)).isoformat())
        _, mapping = d.build_session_options(RACE, [SESSIONS[0], delayed])
        self.assertEqual(mapping['Wyścig']['session_key'], 3)
        self.assertEqual(d.weekend_states(RACE, [delayed], NOW)['Wyścig'][0], 'NASTĘPNA')

class ServiceTests(unittest.TestCase):
    def setUp(self):
        st.cache_data.clear()
    def test_jolpica_constructor_and_no_duplicate_status(self):
        with patch.object(api, 'get_session_results', return_value=[dict(RESULT, Time=None, status='+1 Lap')]):
            result = load_normalized_results(RACE, 'Wyścig', [], {})
        self.assertEqual(result.rows[0]['team'], 'Ferrari')
        self.assertIsNone(result.rows[0]['duration'])
        self.assertEqual(result.rows[0]['status'], '+1 Lap')
    def test_driver_failure_retains_practice_results(self):
        with patch.object(api, 'get_openf1_results', return_value=[dict(driver_number=44, position=1)]), patch.object(api, 'get_openf1_drivers', side_effect=api.APIError('metadata unavailable')):
            result = load_normalized_results(RACE, 'FP1', SESSIONS, {})
        self.assertEqual(result.rows[0]['name'], '#44')
        self.assertTrue(result.warnings)
    def test_empty_and_error_are_distinct(self):
        with patch.object(api, 'get_session_results', return_value=[]):
            self.assertEqual(load_normalized_results(RACE, 'Wyścig', [], {}).state, 'empty')
        with patch.object(api, 'get_session_results', side_effect=api.APIError('restricted', 'restricted')):
            self.assertEqual(load_normalized_results(RACE, 'Wyścig', [], {}).state, 'error')
    def test_last_good_snapshot_and_cooldown(self):
        saved = {}
        getter = Mock(return_value=[RACE])
        first = load_source(getter, (), saved, 'calendar', NOW)
        getter.side_effect = api.APIError('offline')
        second = load_source(getter, (), saved, 'calendar', NOW+timedelta(seconds=1))
        third = load_source(getter, (), saved, 'calendar', NOW+timedelta(seconds=30))
        self.assertEqual(second.rows, first.rows)
        self.assertEqual(second.fetched_at, first.fetched_at)
        self.assertEqual(third.state, 'stale')
        self.assertEqual(getter.call_count, 2)
    def test_bad_json_schema_is_api_error(self):
        for payload in [[], {'MRData': None}, {'MRData': {'RaceTable': {'Races': [None]}}}]:
            with patch.object(api, '_get_json', return_value=payload), self.assertRaises(api.APIError):
                api.get_schedule.__wrapped__(YEAR)
    def test_nullable_metadata(self):
        self.assertEqual(api._clean({'Driver': None, 'Constructor': {'name': None}}), {'Driver': {}, 'Constructor': {'name': ''}})
    def test_http_error_classification(self):
        for status, kind in [(401, 'restricted'), (403, 'restricted'), (429, 'rate_limit')]:
            client = Mock()
            client.get.return_value.status_code = status
            with patch.object(api.requests, 'Session') as session:
                session.return_value.__enter__.return_value = client
                with self.assertRaises(api.APIError) as cm:
                    api._get_json('https://example.org')
                self.assertEqual(cm.exception.kind, kind)
    def test_invalid_json_is_not_connection_error(self):
        client = Mock()
        client.get.return_value.status_code = 200
        client.get.return_value.json.side_effect = ValueError('bad json')
        with patch.object(api.requests, 'Session') as session:
            session.return_value.__enter__.return_value = client
            with self.assertRaises(api.APIError) as cm:
                api._get_json('https://example.org')
            self.assertEqual(cm.exception.kind, 'invalid_data')

class ScreenTests(unittest.TestCase):
    def setUp(self):
        st.cache_data.clear()
    def test_all_six_screens(self):
        with patch.object(api, '_get_json', side_effect=fixture_http):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=20).run()
            self.assertFalse(app.exception)
            for page in ['Weekend', 'Kalendarz', 'Wyniki', 'Klasyfikacje', 'Kierowcy', 'Start']:
                app.radio[0].set_value(page).run()
                self.assertFalse(app.exception, page)
                if page == 'Weekend':
                    self.assertFalse(app.success)
                    self.assertTrue(any('TRWA' in item.value for item in app.markdown))
                if page == 'Kalendarz':
                    for mode in ['Cały sezon', 'Zakończone', 'Niepotwierdzone', 'Najbliższe']:
                        app.radio[1].set_value(mode).run()
                        self.assertFalse(app.exception, mode)
                if page == 'Wyniki':
                    self.assertTrue(any('Test Driver' in item.value for item in app.markdown))
    def test_standings_failure_keeps_calendar(self):
        def partial(url, **kwargs):
            if 'Standings' in url:
                raise api.APIError('standings offline')
            return fixture_http(url)
        with patch.object(api, '_get_json', side_effect=partial):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=20).run()
            self.assertFalse(app.exception)
            app.radio[0].set_value('Weekend').run()
            self.assertFalse(app.exception)
            self.assertTrue(any('Test Grand Prix' in item.value for item in app.markdown))
    def test_all_sources_down(self):
        with patch.object(api, '_get_json', side_effect=api.APIError('offline')):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=20).run()
            for page in ['Start', 'Weekend', 'Kalendarz', 'Wyniki', 'Klasyfikacje', 'Kierowcy']:
                app.radio[0].set_value(page).run()
                self.assertFalse(app.exception, page)

    def test_missing_times_in_screens(self):
        def missing(url, **kwargs):
            data = fixture_http(url)
            if '/sessions?' in url:
                return []
            if isinstance(data, dict) and 'RaceTable' in data['MRData']:
                race = data['MRData']['RaceTable']['Races'][0]
                race['time'] = None
                race['FirstPractice']['time'] = None
            return data
        with patch.object(api, '_get_json', side_effect=missing):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=20).run()
            for page in ['Weekend', 'Kalendarz', 'Wyniki']:
                app.radio[0].set_value(page).run()
                self.assertFalse(app.exception, page)
            app.radio[0].set_value('Weekend').run()
            self.assertTrue(any('Godzina nieznana' in item.value for item in app.markdown))

    def test_season_switch_requests_selected_year(self):
        with patch.object(api, '_get_json', side_effect=fixture_http) as http:
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=20).run()
            app.selectbox[0].set_value(YEAR-1).run()
            self.assertFalse(app.exception)
            self.assertTrue(any(f'/{YEAR-1}.json' in call.args[0] for call in http.call_args_list))

if __name__ == '__main__':
    unittest.main(verbosity=2)
