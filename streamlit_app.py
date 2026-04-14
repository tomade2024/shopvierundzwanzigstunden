import streamlit as st
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="Patch Vorbestellung", page_icon="🎖️", layout="centered")

# =========================
# Einstellungen
# =========================
FORM_URL = "https://forms.gle/fuFw7HV8dxeH4Hjw7"
START_TIME = datetime(2026, 4, 15, 18, 0, 0, tzinfo=timezone.utc)
DURATION_HOURS = 24
END_TIME = START_TIME + timedelta(hours=DURATION_HOURS)
MAX_PATCHES = 100
MAX_PER_PERSON = 2

# Optional: Wenn du den aktuellen Status manuell umschalten willst
# Werte: "open", "waitlist", "closed"
MANUAL_MODE = "open"


def get_status(now_utc: datetime) -> str:
    if MANUAL_MODE == "closed":
        return "closed"
    if MANUAL_MODE == "waitlist":
        return "waitlist"
    if now_utc < START_TIME:
        return "not_started"
    if now_utc >= END_TIME:
        return "closed"
    return "open"


def format_dt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%d.%m.%Y, %H:%M UTC")


now = datetime.now(timezone.utc)
status = get_status(now)
remaining = END_TIME - now

st.title("Patch Vorbestellung")
st.caption("Limitierte Vorbestellung für 24 Stunden")

with st.container(border=True):
    st.markdown(
        f"""
**Wichtige Hinweise**

- Insgesamt limitiert auf **{MAX_PATCHES} Patches**
- Maximal **{MAX_PER_PERSON} Patches pro Person**
- **Kein Versand**
- **Abholung am 18.04.2026 ab 10:00 Uhr am Stand**
- Nach Erreichen des Limits erfolgt Eintragung auf die **Warteliste**
        """
    )

col1, col2 = st.columns(2)
col1.metric("Start", format_dt(START_TIME))
col2.metric("Ende", format_dt(END_TIME))

if status == "not_started":
    st.info("Die Vorbestellung hat noch nicht begonnen.")
elif status == "open":
    hours_left = max(int(remaining.total_seconds() // 3600), 0)
    minutes_left = max(int((remaining.total_seconds() % 3600) // 60), 0)
    st.success(f"Die Vorbestellung ist geöffnet. Noch {hours_left} Std. {minutes_left} Min. verbleibend.")
    st.link_button("Jetzt vorbestellen", FORM_URL, use_container_width=True)
elif status == "waitlist":
    st.warning("Das Kontingent ist erreicht. Neue Einträge gehen auf die Warteliste.")
    st.link_button("Zur Warteliste", FORM_URL, use_container_width=True)
else:
    st.error("Die 24-Stunden-Vorbestellung ist beendet.")
    st.button("Vorbestellung geschlossen", disabled=True, use_container_width=True)

with st.expander("So passt du die App an"):
    st.code(
        '''FORM_URL = "https://forms.gle/fuFw7HV8dxeH4Hjw7"
START_TIME = datetime(2026, 4, 17, 10, 0, 0, tzinfo=timezone.utc)
DURATION_HOURS = 24
MANUAL_MODE = "open"  # open | waitlist | closed''',
        language="python",
    )
    st.markdown(
        """
- `FORM_URL`: Link zu deinem Google-Formular
- `START_TIME`: Start der Aktion
- `DURATION_HOURS`: Laufzeit der Aktion
- `MANUAL_MODE`:
  - `open` = normal geöffnet
  - `waitlist` = Button bleibt aktiv, aber Seite zeigt Warteliste
  - `closed` = komplett geschlossen
        """
    )

st.divider()
st.caption("Hinweis: Die eigentliche Vergabe von BESTÄTIGT oder WARTELISTE sollte weiter im Google-Formular bzw. Google-Sheet erfolgen.")
