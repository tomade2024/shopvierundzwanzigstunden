import streamlit as st
from datetime import datetime, timedelta, timezone
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Patch Vorbestellung", page_icon="🎖️", layout="centered")

# =========================
# Einstellungen
# =========================
FORM_URL = "https://forms.gle/EjwizyDncYcpHTUf7"
START_TIME = datetime(2026, 4, 15, 18, 0, 0, tzinfo=timezone.utc)
DURATION_HOURS = 24
END_TIME = START_TIME + timedelta(hours=DURATION_HOURS)
MAX_PATCHES = 100
MAX_PER_PERSON = 2
PRICE_EUR = 5
LOW_STOCK_THRESHOLD = 15

# Google Sheets
SPREADSHEET_NAME = "Patches Stairrun 2026"
WORKSHEET_NAME = "Formularantworten 1"
AMOUNT_COLUMN_NAME = "Anzahl Patches"
STATUS_COLUMN_NAME = "Status"

# Optional: manueller Override
# Werte: None | "waitlist" | "closed"
MANUAL_MODE = None


def get_gsheet_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]

    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes,
    )
    return gspread.authorize(credentials)


@st.cache_data(ttl=60)
def load_sheet_data():
    client = get_gsheet_client()
    spreadsheet = client.open(SPREADSHEET_NAME)
    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    records = worksheet.get_all_records()
    return records


def compute_stock_info(records):
    confirmed_total = 0
    waitlist_count = 0

    for row in records:
        amount_raw = row.get(AMOUNT_COLUMN_NAME, 0)
        status_raw = str(row.get(STATUS_COLUMN_NAME, "")).strip().upper()

        try:
            amount = int(amount_raw)
        except Exception:
            amount = 0

        if status_raw == "BESTAETIGT" or status_raw == "BESTÄTIGT":
            confirmed_total += amount
        elif status_raw == "WARTELISTE":
            waitlist_count += 1

    remaining_patches = max(MAX_PATCHES - confirmed_total, 0)

    if remaining_patches <= 0:
        live_status = "waitlist"
    else:
        live_status = "open"

    return {
        "confirmed_total": confirmed_total,
        "remaining_patches": remaining_patches,
        "waitlist_count": waitlist_count,
        "live_status": live_status,
    }


def get_status(now_utc: datetime, live_status: str) -> str:
    if MANUAL_MODE == "closed":
        return "closed"
    if MANUAL_MODE == "waitlist":
        return "waitlist"
    if now_utc < START_TIME:
        return "not_started"
    if now_utc >= END_TIME:
        return "closed"
    return live_status


def format_dt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%d.%m.%Y, %H:%M UTC")


def countdown_parts(delta: timedelta):
    total_seconds = max(int(delta.total_seconds()), 0)
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return days, hours, minutes, seconds


now = datetime.now(timezone.utc)
remaining = END_TIME - now

days, hours, minutes, seconds = countdown_parts(remaining)

sheet_error = None
try:
    records = load_sheet_data()
    stock_info = compute_stock_info(records)
except Exception as e:
    records = []
    stock_info = {
        "confirmed_total": 0,
        "remaining_patches": MAX_PATCHES,
        "waitlist_count": 0,
        "live_status": "open",
    }
    sheet_error = str(e)

status = get_status(now, stock_info["live_status"])
remaining_patches = stock_info["remaining_patches"]
confirmed_total = stock_info["confirmed_total"]
waitlist_count = stock_info["waitlist_count"]

st.markdown(
    """
    <style>
    .shop-card {
        border: 1px solid rgba(49, 51, 63, 0.2);
        border-radius: 18px;
        padding: 1.25rem;
        background: linear-gradient(180deg, rgba(255,255,255,1) 0%, rgba(248,249,251,1) 100%);
        box-shadow: 0 8px 30px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    .badge-row {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin: 0.5rem 0 1rem 0;
    }
    .badge {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 700;
    }
    .badge-open {
        background: #e8f7ec;
        color: #17663a;
    }
    .badge-waitlist {
        background: #fff5e6;
        color: #9a5a00;
    }
    .badge-soldout {
        background: #fdeaea;
        color: #a61b1b;
    }
    .badge-info {
        background: #eef3ff;
        color: #274c9b;
    }
    .countdown {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.75rem;
        margin: 1rem 0 1rem 0;
    }
    .count-box {
        border: 1px solid rgba(49, 51, 63, 0.12);
        border-radius: 14px;
        padding: 0.9rem 0.6rem;
        text-align: center;
        background: white;
    }
    .count-number {
        font-size: 1.6rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .count-label {
        font-size: 0.82rem;
        color: #555;
        margin-top: 0.2rem;
    }
    .product-title {
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0.25rem;
    }
    .subtitle {
        color: #555;
        margin-bottom: 0.75rem;
    }
    .note {
        font-size: 0.95rem;
        color: #444;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if status == "open":
    status_badge = '<span class="badge badge-open">JETZT VERFUEGBAR</span>'
    if remaining_patches <= LOW_STOCK_THRESHOLD:
        secondary_badge = f'<span class="badge badge-waitlist">NUR NOCH {remaining_patches} VERFUEGBAR</span>'
    else:
        secondary_badge = f'<span class="badge badge-info">{remaining_patches} verfuegbar</span>'
elif status == "waitlist":
    status_badge = '<span class="badge badge-waitlist">WARTELISTE</span>'
    secondary_badge = '<span class="badge badge-info">Kontingent erreicht</span>'
elif status == "closed":
    status_badge = '<span class="badge badge-soldout">AUSVERKAUFT / GESCHLOSSEN</span>'
    secondary_badge = '<span class="badge badge-info">Vorbestellung beendet</span>'
else:
    status_badge = '<span class="badge badge-info">NOCH NICHT GESTARTET</span>'
    secondary_badge = '<span class="badge badge-info">Startet bald</span>'

st.markdown(
    f"""
    <div class="shop-card">
        <div class="product-title">Patch Vorbestellung</div>
        <div class="subtitle">Limitierte Vorbestellung fuer 24 Stunden</div>
        <div style="font-size:1.35rem; font-weight:800; margin-bottom:0.5rem;">{PRICE_EUR},00 EUR pro Patch</div>
        <div class="badge-row">
            {status_badge}
            {secondary_badge}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container(border=True):
    st.markdown(
        f"""
**Wichtige Hinweise**

- Insgesamt limitiert auf **{MAX_PATCHES} Patches**
- Maximal **{MAX_PER_PERSON} Patches pro Person**
- **Preis: {PRICE_EUR} EUR pro Patch**
- **Kein Versand**
- **Abholung am 18.04.2026 ab 10:00 Uhr am Stand**
- Nach Erreichen des Limits erfolgt Eintragung auf die **Warteliste**
        """
    )

col1, col2 = st.columns(2)
col1.metric("Start", format_dt(START_TIME))
col2.metric("Ende", format_dt(END_TIME))

col3, col4, col5 = st.columns(3)
col3.metric("Bestaetigt", confirmed_total)
col4.metric("Verfuegbar", remaining_patches)
col5.metric("Warteliste", waitlist_count)

if status in ["open", "not_started"]:
    st.markdown(
        f"""
        <div class="countdown">
            <div class="count-box"><div class="count-number">{days}</div><div class="count-label">Tage</div></div>
            <div class="count-box"><div class="count-number">{hours}</div><div class="count-label">Stunden</div></div>
            <div class="count-box"><div class="count-number">{minutes}</div><div class="count-label">Minuten</div></div>
            <div class="count-box"><div class="count-number">{seconds}</div><div class="count-label">Sekunden</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if status == "not_started":
    st.info("Die Vorbestellung hat noch nicht begonnen.")
elif status == "open":
    st.success(f"Die Vorbestellung ist geoeffnet. Noch {days} Tage, {hours} Stunden und {minutes} Minuten verbleibend.")
    if remaining_patches <= LOW_STOCK_THRESHOLD:
        st.warning(f"Nur noch wenige verfuegbar: aktuell {remaining_patches} Patch(es).")
    st.link_button("Jetzt vorbestellen", FORM_URL, use_container_width=True)
elif status == "waitlist":
    st.warning("Das Kontingent ist erreicht. Neue Eintraege gehen auf die Warteliste.")
    st.link_button("Zur Warteliste", FORM_URL, use_container_width=True)
else:
    st.error("Die 24-Stunden-Vorbestellung ist beendet.")
    st.button("Vorbestellung geschlossen", disabled=True, use_container_width=True)

if sheet_error:
    st.warning("Google-Sheets-Daten konnten nicht geladen werden. Die Seite zeigt gerade Fallback-Werte an.")
    st.code(sheet_error)

st.markdown(
    """
    <div class="note">
    Der Bestand wird automatisch aus Google Sheets gelesen. Voraussetzung ist, dass die Tabelle eine Spalte fuer die Menge und eine Spalte fuer den Status enthaelt.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("So verbindest du Google Sheets"):
    st.markdown(
        """
1. Erstelle in Streamlit `secrets.toml` einen Eintrag `gcp_service_account` mit deinem Service-Account-JSON.
2. Teile dein Google Sheet mit der E-Mail-Adresse des Service Accounts.
3. Trage den Namen der Tabelle in `SPREADSHEET_NAME` ein.
4. Trage den Namen des Tabellenblatts in `WORKSHEET_NAME` ein.
5. Stelle sicher, dass die Spaltennamen zu `AMOUNT_COLUMN_NAME` und `STATUS_COLUMN_NAME` passen.

Beispiel fuer `.streamlit/secrets.toml`:
        """
    )
    st.code(
        '''[gcp_service_account]
type = "service_account"
project_id = "dein-projekt"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
client_email = "dein-service-account@dein-projekt.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."''',
        language="toml",
    )

with st.expander("So passt du die App an"):
    st.code(
        '''FORM_URL = "HIER_DEIN_GOOGLE_FORM_LINK"
START_TIME = datetime(2026, 4, 17, 10, 0, 0, tzinfo=timezone.utc)
DURATION_HOURS = 24
SPREADSHEET_NAME = "Patch Vorbestellungen"
WORKSHEET_NAME = "Form Responses 1"
AMOUNT_COLUMN_NAME = "Anzahl Patches"
STATUS_COLUMN_NAME = "Status"
MANUAL_MODE = None  # None | waitlist | closed''',
        language="python",
    )
