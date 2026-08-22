from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

import streamlit as st

WARSAW = ZoneInfo("Europe/Warsaw")


def apply_styles():
    st.markdown(
        """
        <style>
            :root {
                --bg: #0b0d10;
                --panel: #15191e;
                --panel2: #1b2026;
                --text: #f4f6f8;
                --muted: #98a1aa;
                --accent: #ff3847;
            }

            .stApp {
                background:
                    radial-gradient(circle at 90% 0%, rgba(255,56,71,.18), transparent 27rem),
                    linear-gradient(180deg, #090b0e 0%, #0e1216 100%);
                color: var(--text);
            }

            .block-container {
                max-width: 790px;
                padding-top: 1.1rem;
                padding-bottom: 4rem;
            }

            [data-testid="stHeader"] { background: transparent; }

            .hero {
                padding: 1.45rem 1.35rem;
                margin-bottom: 1rem;
                border: 1px solid rgba(255,255,255,.08);
                border-radius: 24px;
                background: linear-gradient(135deg, rgba(255,255,255,.09), rgba(255,255,255,.025));
                box-shadow: 0 20px 55px rgba(0,0,0,.25);
            }

            .eyebrow {
                color: var(--accent);
                font-size: .76rem;
                font-weight: 900;
                letter-spacing: .13em;
                text-transform: uppercase;
            }

            .hero-title {
                margin: .25rem 0 .45rem;
                font-size: clamp(2rem, 8vw, 3rem);
                line-height: .95;
                font-weight: 950;
                letter-spacing: -.055em;
            }

            .muted {
                color: var(--muted);
                font-size: .88rem;
            }

            .section-title {
                margin: 1.35rem 0 .65rem;
                font-size: 1.18rem;
                font-weight: 900;
                letter-spacing: -.025em;
            }

            .session-card, .driver-profile {
                padding: 1.1rem 1.15rem;
                border-radius: 20px;
                border: 1px solid rgba(255,255,255,.08);
                background: linear-gradient(145deg, #181d23, #12161a);
                margin-bottom: .8rem;
            }

            .session-title {
                font-size: 1.35rem;
                font-weight: 950;
                margin-top: .2rem;
            }

            .countdown {
                font-size: clamp(1.7rem, 7vw, 2.35rem);
                font-weight: 950;
                letter-spacing: -.04em;
                margin: .15rem 0;
            }

            .standing-row, .result-row, .form-row {
                display: flex;
                align-items: center;
                gap: .8rem;
                padding: .78rem .85rem;
                margin-bottom: .45rem;
                border-radius: 15px;
                border: 1px solid rgba(255,255,255,.065);
                background: rgba(255,255,255,.045);
            }

            .standing-pos, .result-pos {
                flex: 0 0 2.1rem;
                color: var(--accent);
                font-weight: 950;
                font-size: 1.05rem;
            }

            .standing-main, .result-main {
                min-width: 0;
                flex: 1;
            }

            .standing-name, .result-name {
                font-weight: 900;
                line-height: 1.15;
            }

            .standing-team, .result-detail {
                color: var(--muted);
                font-size: .79rem;
                margin-top: .15rem;
                overflow-wrap: anywhere;
            }

            .standing-points {
                font-weight: 950;
                white-space: nowrap;
            }

            .standing-points small {
                color: var(--muted);
                font-weight: 700;
            }

            .metric-grid {
                display: grid;
                gap: .55rem;
                grid-template-columns: repeat(2, minmax(0,1fr));
                margin: .7rem 0;
            }

            .metric-grid.cols-3 {
                grid-template-columns: repeat(3, minmax(0,1fr));
            }

            .metric-card {
                padding: .85rem;
                border-radius: 16px;
                background: rgba(255,255,255,.045);
                border: 1px solid rgba(255,255,255,.065);
            }

            .metric-label {
                color: var(--muted);
                font-size: .72rem;
                text-transform: uppercase;
                letter-spacing: .07em;
                font-weight: 800;
            }

            .metric-value {
                font-weight: 950;
                font-size: 1.02rem;
                margin-top: .2rem;
                overflow-wrap: anywhere;
            }

            .metric-sub {
                color: var(--muted);
                font-size: .75rem;
            }


            .weekend-hero {
                position: relative;
                overflow: hidden;
                padding: 1.25rem 1.2rem;
                border-radius: 22px;
                border: 1px solid rgba(255,255,255,.08);
                background:
                    radial-gradient(circle at 92% 15%, rgba(255,56,71,.18), transparent 38%),
                    linear-gradient(145deg, #191e24, #11151a);
                margin: .65rem 0 1rem;
            }

            .weekend-round {
                color: var(--accent);
                font-size: .72rem;
                font-weight: 900;
                letter-spacing: .12em;
                text-transform: uppercase;
            }

            .weekend-name {
                margin: .2rem 0 .35rem;
                font-size: clamp(1.55rem, 6vw, 2.15rem);
                font-weight: 950;
                letter-spacing: -.045em;
                line-height: 1;
            }

            .weekend-location {
                color: var(--muted);
                font-size: .86rem;
            }

            .weekend-progress-head {
                display: flex;
                justify-content: space-between;
                gap: 1rem;
                margin: .85rem 0 .35rem;
                color: var(--muted);
                font-size: .76rem;
                font-weight: 800;
            }

            .weekend-session {
                display: grid;
                grid-template-columns: 5.8rem minmax(0, 1fr) auto;
                gap: .7rem;
                align-items: center;
                padding: .82rem .9rem;
                margin-bottom: .45rem;
                border-radius: 15px;
                border: 1px solid rgba(255,255,255,.065);
                background: rgba(255,255,255,.04);
            }

            .weekend-session.next {
                border-color: rgba(255,56,71,.28);
                background: rgba(255,56,71,.075);
            }

            .weekend-session.live {
                border-color: rgba(85,220,140,.27);
                background: rgba(85,220,140,.065);
            }

            .weekend-day {
                color: var(--muted);
                font-size: .72rem;
                font-weight: 850;
                text-transform: uppercase;
            }

            .weekend-session-name {
                font-weight: 900;
                line-height: 1.15;
            }

            .weekend-session-time {
                color: var(--muted);
                font-size: .75rem;
                margin-top: .12rem;
            }

            .weekend-state {
                text-align: right;
                white-space: nowrap;
                font-size: .7rem;
                font-weight: 900;
                letter-spacing: .04em;
                color: var(--muted);
            }

            .weekend-state.next {
                color: #ff6570;
            }

            .weekend-state.live {
                color: #67dc98;
            }

            .podium-grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(0,1fr));
                gap: .5rem;
                margin: .6rem 0;
            }

            .podium-card {
                padding: .75rem .7rem;
                border-radius: 15px;
                border: 1px solid rgba(255,255,255,.065);
                background: rgba(255,255,255,.04);
                min-width: 0;
            }

            .podium-pos {
                color: var(--accent);
                font-size: .7rem;
                font-weight: 950;
            }

            .podium-name {
                margin-top: .15rem;
                font-size: .86rem;
                font-weight: 900;
                line-height: 1.12;
                overflow-wrap: anywhere;
            }

            .podium-points {
                margin-top: .22rem;
                color: var(--muted);
                font-size: .72rem;
            }

            .calendar-head {
                display: grid;
                gap: .35rem;
                padding: .35rem 0 .7rem;
            }

            .badge {
                display: inline-block;
                width: fit-content;
                padding: .2rem .45rem;
                border-radius: 999px;
                font-size: .64rem;
                font-weight: 900;
                letter-spacing: .06em;
                background: rgba(255,56,71,.14);
                color: #ff6570;
                border: 1px solid rgba(255,56,71,.25);
            }

            .badge.done {
                background: rgba(255,255,255,.06);
                border-color: rgba(255,255,255,.08);
                color: #9ca4ad;
            }

            .session-line {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 1rem;
                padding: .55rem 0;
                border-top: 1px solid rgba(255,255,255,.06);
            }

            .profile-name {
                font-weight: 950;
                font-size: 1.65rem;
                letter-spacing: -.035em;
                margin: .15rem 0;
            }

            .form-row {
                justify-content: space-between;
            }

            .form-position {
                font-size: 1.15rem;
                font-weight: 950;
                color: var(--accent);
            }

            .form-strip {
                display: flex;
                justify-content: space-between;
                gap: 1rem;
                margin-top: .7rem;
                padding: .85rem 1rem;
                border-radius: 15px;
                background: rgba(255,56,71,.08);
                border: 1px solid rgba(255,56,71,.18);
            }

            .form-strip span {
                color: #ff6570;
                font-size: .75rem;
                font-weight: 900;
                letter-spacing: .1em;
            }

            .info-box, .empty-box, .error-box {
                padding: .9rem 1rem;
                border-radius: 15px;
                margin: .8rem 0;
                border: 1px solid rgba(255,255,255,.07);
                background: rgba(255,255,255,.035);
                color: #b1b8c0;
                font-size: .86rem;
            }

            .error-box {
                border-color: rgba(255,56,71,.18);
                background: rgba(255,56,71,.07);
            }

            .footer {
                text-align: center;
                margin-top: 2.4rem;
                color: #69727b;
                font-size: .72rem;
            }

            div[data-testid="stLinkButton"] a,
            div[data-testid="stButton"] button {
                min-height: 46px;
                border-radius: 999px !important;
                font-weight: 850 !important;
            }

            div[role="radiogroup"] {
                gap: .25rem;
            }

            @media (max-width: 640px) {
                .block-container {
                    padding-left: .75rem;
                    padding-right: .75rem;
                }

                .hero {
                    border-radius: 20px;
                    padding: 1.2rem 1rem;
                }

                .metric-grid.cols-3 {
                    grid-template-columns: repeat(3, minmax(0,1fr));
                }

                .metric-card {
                    padding: .7rem .6rem;
                }

                .metric-value {
                    font-size: .9rem;
                }

                .standing-row, .result-row {
                    gap: .55rem;
                    padding: .7rem;
                }

                .standing-points {
                    font-size: .9rem;
                }

                .session-line {
                    font-size: .86rem;
                }

                .weekend-session {
                    grid-template-columns: 4.8rem minmax(0, 1fr);
                    gap: .55rem;
                    padding: .72rem;
                }

                .weekend-state {
                    grid-column: 2;
                    text-align: left;
                }

                .podium-grid {
                    grid-template-columns: repeat(3, minmax(0,1fr));
                }

                .podium-card {
                    padding: .65rem .55rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(kicker: str, title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">{escape(kicker)}</div>
            <div class="hero-title">{escape(title)}</div>
            <div class="muted">{escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(text: str):
    st.markdown(f'<div class="section-title">{escape(text)}</div>', unsafe_allow_html=True)


def render_session_card(gp: str, session: str, countdown: str, details: str):
    st.markdown(
        f"""
        <div class="session-card">
            <div class="eyebrow">{escape(gp)}</div>
            <div class="session-title">{escape(session)}</div>
            <div class="countdown">{escape(countdown)}</div>
            <div class="muted">{escape(details)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def driver_row_html(row: dict, full: bool = False) -> str:
    driver = row.get("Driver", {})
    constructors = row.get("Constructors", [])
    team = constructors[0].get("name", "—") if constructors else "—"
    name = f"{driver.get('givenName', '')} {driver.get('familyName', '')}".strip()
    secondary = team
    if full:
        secondary += f" · {row.get('wins', '0')} zwyc."
    return f"""
        <div class="standing-row">
            <div class="standing-pos">{escape(str(row.get('position', '—')))}</div>
            <div class="standing-main">
                <div class="standing-name">{escape(name)}</div>
                <div class="standing-team">{escape(secondary)}</div>
            </div>
            <div class="standing-points">{escape(str(row.get('points', '0')))}<small> pkt</small></div>
        </div>
    """


def render_metric_cards(items, columns=2):
    """Render metric cards as one compact HTML block.

    Streamlit/Markdown can interpret an indented HTML fragment after a blank
    line as a Markdown code block. Building the whole grid without leading
    indentation or blank lines prevents the second/third card from being
    displayed as raw <div> markup.
    """
    cls = "metric-grid cols-3" if columns == 3 else "metric-grid"
    cards = []
    for label, value, sub in items:
        cards.append(
            '<div class="metric-card">'
            f'<div class="metric-label">{escape(str(label))}</div>'
            f'<div class="metric-value">{escape(str(value))}</div>'
            f'<div class="metric-sub">{escape(str(sub))}</div>'
            '</div>'
        )

    html = f'<div class="{cls}">{"".join(cards)}</div>'
    st.markdown(html, unsafe_allow_html=True)



def render_weekend_header(round_no, race_name, circuit, location, date_range):
    html = (
        '<div class="weekend-hero">'
        f'<div class="weekend-round">RUNDA {escape(str(round_no))} · WEEKEND CENTER</div>'
        f'<div class="weekend-name">{escape(str(race_name))}</div>'
        f'<div class="weekend-location">{escape(str(circuit))} · {escape(str(location))}</div>'
        f'<div class="weekend-location" style="margin-top:.2rem;">{escape(str(date_range))}</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_weekend_session(label, dt_text, day_text, state, note=""):
    state_upper = (state or "").upper()
    row_class = "weekend-session"
    state_class = "weekend-state"

    if state_upper == "NASTĘPNA":
        row_class += " next"
        state_class += " next"
    elif state_upper == "TRWA":
        row_class += " live"
        state_class += " live"

    note_html = f'<div class="weekend-session-time">{escape(str(note))}</div>' if note else ""
    html = (
        f'<div class="{row_class}">'
        f'<div class="weekend-day">{escape(str(day_text))}</div>'
        '<div>'
        f'<div class="weekend-session-name">{escape(str(label))}</div>'
        f'<div class="weekend-session-time">{escape(str(dt_text))}</div>'
        f'{note_html}'
        '</div>'
        f'<div class="{state_class}">{escape(str(state))}</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_podium_cards(items):
    cards = []
    for position, name, points in items[:3]:
        cards.append(
            '<div class="podium-card">'
            f'<div class="podium-pos">P{escape(str(position))}</div>'
            f'<div class="podium-name">{escape(str(name))}</div>'
            f'<div class="podium-points">{escape(str(points))} pkt</div>'
            '</div>'
        )
    st.markdown(f'<div class="podium-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_empty(text: str):
    st.markdown(f'<div class="empty-box">{escape(text)}</div>', unsafe_allow_html=True)


def render_error(text: str):
    st.markdown(f'<div class="error-box">{escape(text)}</div>', unsafe_allow_html=True)


def status_badge(status: str) -> str:
    done = status.upper() == "ZAKOŃCZONE"
    cls = "badge done" if done else "badge"
    return f'<span class="{cls}">{escape(status)}</span>'


def format_local_datetime(dt: datetime | None, short=False) -> str:
    if not dt:
        return "—"
    local = dt.astimezone(WARSAW)
    if short:
        return local.strftime("%d.%m · %H:%M")
    return local.strftime("%d.%m.%Y · %H:%M")


def format_session_name(name: str) -> str:
    value = (name or "").strip().lower()
    mapping = {
        "practice 1": "FP1",
        "practice 2": "FP2",
        "practice 3": "FP3",
        "sprint qualifying": "Kwalifikacje sprintu",
        "sprint shootout": "Kwalifikacje sprintu",
        "sprint": "Sprint",
        "qualifying": "Kwalifikacje",
        "race": "Wyścig",
    }
    return mapping.get(value, name)


def _seconds_to_time(value: float) -> str:
    if value < 0:
        return ""
    hours = int(value // 3600)
    remainder = value - hours * 3600
    minutes = int(remainder // 60)
    seconds = remainder - minutes * 60
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:06.3f}"
    return f"{minutes}:{seconds:06.3f}"


def format_duration(value) -> str:
    if value in (None, "", []):
        return ""

    if isinstance(value, list):
        parts = []
        for idx, item in enumerate(value[:3], start=1):
            if item in (None, ""):
                continue
            if isinstance(item, (int, float)):
                item_text = _seconds_to_time(float(item))
            else:
                item_text = str(item)
            parts.append(f"Q{idx} {item_text}")
        return " · ".join(parts)

    if isinstance(value, (int, float)):
        return _seconds_to_time(float(value))

    return str(value)


def format_gap(value) -> str:
    if value in (None, "", []):
        return ""

    if isinstance(value, list):
        usable = [x for x in value if x not in (None, "")]
        if not usable:
            return ""
        value = usable[-1]

    if isinstance(value, (int, float)):
        if float(value) == 0:
            return "lider"
        return f"+{float(value):.3f}"

    text = str(value)
    if text == "0":
        return "lider"
    if text.startswith("+"):
        return text
    return text
