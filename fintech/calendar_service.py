import os
import json
from pathlib import Path

REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/api/auth/callback")

# Allow HTTP only for localhost development
if REDIRECT_URI.startswith("http://localhost"):
    os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
CREDENTIALS_FILE = "credentials.json"

# On Railway/cloud, store token in a mounted volume via TOKEN_DIR env var
_DATA_DIR = Path(os.getenv("DATA_DIR", "."))
TOKEN_FILE = _DATA_DIR / "token.json"

_flow_state: dict = {"flow": None, "state": None}


def _get_client_config() -> dict | None:
    """Load OAuth client config from env var (cloud) or credentials.json (local)."""
    raw = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if raw:
        return json.loads(raw)
    p = Path(CREDENTIALS_FILE)
    if p.exists():
        return json.loads(p.read_text())
    return None


def credentials_file_exists() -> bool:
    return _get_client_config() is not None


def _load_credentials() -> Credentials | None:
    if not TOKEN_FILE.exists():
        return None
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_token(creds)
    return creds


def _save_token(creds: Credentials) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(creds.to_json())


def is_authenticated() -> bool:
    try:
        creds = _load_credentials()
        return creds is not None and creds.valid
    except Exception:
        return False


def get_auth_url() -> str:
    config = _get_client_config()
    if not config:
        raise Exception("Credenciais Google não configuradas")
    flow = Flow.from_client_config(config, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")
    _flow_state["flow"] = flow
    _flow_state["state"] = state
    return auth_url


def exchange_code(code: str, state: str = "") -> None:
    flow: Flow | None = _flow_state.get("flow")
    if flow is None:
        config = _get_client_config()
        if not config:
            raise Exception("Credenciais Google não configuradas")
        flow = Flow.from_client_config(config, scopes=SCOPES, redirect_uri=REDIRECT_URI)

    authorization_response = f"{REDIRECT_URI}?code={code}"
    if state:
        authorization_response += f"&state={state}"

    flow.fetch_token(authorization_response=authorization_response)
    _save_token(flow.credentials)
    _flow_state["flow"] = None
    _flow_state["state"] = None


def _get_service():
    creds = _load_credentials()
    if not creds or not creds.valid:
        raise Exception("Não autenticado. Conecte sua conta Google primeiro.")
    return build("calendar", "v3", credentials=creds)


def create_event(transaction) -> str:
    service = _get_service()
    emoji = "⚠️" if transaction.type == "despesa" else "💰"
    action = "Pagar" if transaction.type == "despesa" else "Receber"
    color_id = "11" if transaction.type == "despesa" else "10"  # red | green

    event = {
        "summary": f"{emoji} {action}: {transaction.description} — R$ {transaction.amount:,.2f}",
        "description": (
            f"Categoria: {transaction.category}\n"
            f"Tipo: {transaction.type.capitalize()}\n"
            f"Valor: R$ {transaction.amount:,.2f}\n\n"
            "Criado pelo sistema Finanças Empresariais."
        ),
        "start": {"date": transaction.due_date.isoformat(), "timeZone": "America/Sao_Paulo"},
        "end":   {"date": transaction.due_date.isoformat(), "timeZone": "America/Sao_Paulo"},
        "colorId": color_id,
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 1440},
                {"method": "popup", "minutes": 60},
            ],
        },
    }

    result = service.events().insert(calendarId="primary", body=event).execute()
    return result["id"]


def delete_event(event_id: str) -> None:
    service = _get_service()
    service.events().delete(calendarId="primary", eventId=event_id).execute()
