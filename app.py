import streamlit as st
import requests
from datetime import datetime, timezone
from pathlib import Path
import json

st.set_page_config(
    page_title="Marcin F1 Hub",
    page_icon="🏎️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

X_PROFILE = "https://x.com/MarcinNov"
STANDINGS_URL = "https://api.jolpi.ca/ergast/f1/current/driverStandings.json"
NEXT_RACE_URL = "https://api.jolpi.ca/ergast/f1/current/next.json"

BASE_DIR = Path(__file__).resolve().parent
NEWS_FILE = BASE_DIR / "data" / "news.json"

st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at top right, rgba(235, 35, 46, .16), transparent 30%),
                linear-gradient(180deg, #0b0d10 0%, #11151a 100%);
            color: #f4f5f7;
        }

        .block-container {
            max-width: 720px;
            padding-top: 1.2rem;
            padding-bottom: 4rem;
        }

        h1, h2, h3, p, span, div {
            font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .hero {
            padding: 1.4rem 1.3rem;
            border: 1px solid rgba(255,255,255,.08);
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(255,255,255,.08), rgba(255,255,255,.025));
            box-shadow: 0 16px 50px rgba(0,0,0,.28);
            margin-bottom: 1rem;
        }

        .eyebrow {
            color: #ff4550;
            font-weight: 800;
            font-size: .82rem;
            letter-spacing: .12em;
            text-transform: uppercase;
        }

        .hero-title {
            font-size: 2.15rem;
            line-height: 1.0;
            font-weight: 900;
            margin: .25rem 0 .5rem;
        }

        .muted {
            color: #a9b0b8;
        }

        .session-card {
            border-radius: 20px;
            padding: 1rem 1.1rem;
            background: #171b20;
            border: 1px solid rgba(255,255,255,.07);
            margin: .6rem 0 1rem;
        }

        .countdown {
            font-size: 2rem;
            font-weight: 900;
            letter-spacing: -.03em;
            margin-top: .25rem;
        }

        .card {
            padding: .9rem 1rem;
            border-radius: 16px;
            background: rgba(255,255,255,.045);
            border: 1px solid rgba(255,255,255,.07);
            margin-bottom: .55rem;
        }

        .position {
            display: inline-block;
            min-width: 2rem;
            color: #ff4550;
            font-weight: 900;
        }

        .driver {
            font-weight: 800;
        }

        .team {
            color: #9aa2aa;
            font-size: .86rem;
        }

        .points {
            float: right;
            font-weight: 900;
        }

        .section-title {
            font-size: 1.15rem;
            font-weight: 900;
            margin: 1.4rem 0 .7rem;
        }

        .footer {
            text-align: center;
            color: #737b84;
            font-size: .78rem;
            margin-top: 2rem;
        }

        div[data-testid="stButton"] > button,
        div[data-testid="stLinkButton"] > a {
            border-radius: 999px !important;
            font-weight: 800 !important;
            min-height: 48px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_json(url: str):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def parse_iso_utc(date_string: str, time_string: str | None):
    if not date_string:
        return None
    time_string = time_string or "00:00:00Z"
    return datetime.fromisoformat(
        f"{date_string}T{time_string.replace('Z', '+00:00')}"
    )


def get_next_session(race: dict):
    sessions = []

    mapping = [
        ("FirstPractice", "FP1"),
        ("SecondPractice", "FP2"),
        ("ThirdPractice", "FP3"),
        ("SprintQualifying", "Kwalifikacje sprintu"),
        ("Sprint", "Sprint"),
        ("Qualifying", "Kwalifikacje"),
    ]

    for api_key, label in mapping:
        payload = race.get(api_key)
        if payload:
            dt = parse_iso_utc(payload.get("date"), payload.get("time"))
            if dt:
                sessions.append((dt, label))

    race_dt = parse_iso_utc(race.get("date"), race.get("time"))
    if race_dt:
        sessions.append((race_dt, "Wyścig"))

    now = datetime.now(timezone.utc)
    future = sorted((dt, label) for dt, label in sessions if dt > now)

    if future:
        return future[0]

    return None


def format_countdown(target: datetime):
    now = datetime.now(timezone.utc)
    seconds = max(0, int((target - now).total_seconds()))

    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, _ = divmod(seconds, 60)

    if days:
        return f"{days} dni · {hours:02d} h · {minutes:02d} min"
    return f"{hours:02d} h · {minutes:02d} min"


def load_news():
    if not NEWS_FILE.exists():
        return []
    try:
        return json.loads(NEWS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">Formula 1 · centrum kibica</div>
        <div class="hero-title">MARCIN F1 HUB</div>
        <div class="muted">Najważniejsze informacje, sesje i klasyfikacja w jednym miejscu.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Najbliższa sesja ---
try:
    race_data = fetch_json(NEXT_RACE_URL)
    races = race_data["MRData"]["RaceTable"]["Races"]
    race = races[0] if races else None

    if race:
        next_session = get_next_session(race)
        gp_name = race.get("raceName", "Grand Prix")
        circuit = race.get("Circuit", {}).get("circuitName", "")
        locality = race.get("Circuit", {}).get("Location", {}).get("locality", "")

        st.markdown('<div class="section-title">🏁 Najbliższa sesja</div>', unsafe_allow_html=True)

        if next_session:
            target, session_name = next_session
            st.markdown(
                f"""
                <div class="session-card">
                    <div class="eyebrow">{gp_name}</div>
                    <div style="font-size:1.25rem;font-weight:900;margin-top:.25rem;">{session_name}</div>
                    <div class="countdown">{format_countdown(target)}</div>
                    <div class="muted">{circuit} · {locality}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info(f"Weekend {gp_name} został zakończony.")
except Exception:
    st.warning("Nie udało się teraz pobrać terminarza F1. Spróbuj odświeżyć stronę.")

# --- Link do X ---
st.link_button("𝕏  Przejdź do mojego profilu", X_PROFILE, use_container_width=True)

# --- Newsy ---
news = load_news()
st.markdown('<div class="section-title">🔥 Najnowsze</div>', unsafe_allow_html=True)

if news:
    for item in news[:5]:
        title = item.get("title", "")
        description = item.get("description", "")
        url = item.get("url", "")
        st.markdown(
            f"""
            <div class="card">
                <div style="font-weight:900;">{title}</div>
                <div class="team" style="margin-top:.25rem;">{description}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if url:
            st.link_button("Czytaj / zobacz post", url, use_container_width=True)
else:
    st.caption("Tu pojawią się Twoje najnowsze newsy i posty.")

# --- Klasyfikacja ---
st.markdown('<div class="section-title">🏆 Klasyfikacja kierowców</div>', unsafe_allow_html=True)

try:
    standings_data = fetch_json(STANDINGS_URL)
    standings_lists = standings_data["MRData"]["StandingsTable"]["StandingsLists"]
    standings = standings_lists[0]["DriverStandings"] if standings_lists else []

    for row in standings[:10]:
        driver = row["Driver"]
        constructors = row.get("Constructors", [])
        team = constructors[0]["name"] if constructors else "—"
        name = f'{driver["givenName"]} {driver["familyName"]}'
        st.markdown(
            f"""
            <div class="card">
                <span class="position">{row["position"]}.</span>
                <span class="driver">{name}</span>
                <span class="points">{row["points"]} pkt</span>
                <div class="team" style="margin-left:2.25rem;">{team}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("Pokaż pełną klasyfikację"):
        for row in standings[10:]:
            driver = row["Driver"]
            constructors = row.get("Constructors", [])
            team = constructors[0]["name"] if constructors else "—"
            name = f'{driver["givenName"]} {driver["familyName"]}'
            st.write(f'**{row["position"]}. {name}** — {row["points"]} pkt · {team}')

except Exception:
    st.warning("Nie udało się teraz pobrać klasyfikacji kierowców.")

st.markdown(
    """
    <div class="footer">
        Marcin F1 Hub · dane sportowe odświeżane automatycznie
    </div>
    """,
    unsafe_allow_html=True,
)
