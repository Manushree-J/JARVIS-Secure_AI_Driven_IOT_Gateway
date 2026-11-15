#!/usr/bin/env python3
"""Google OAuth 2.0 authentication module — fixed for actual browser auth.

Requires:
    - client_secrets.json in the project root (from Google Cloud: Desktop OAuth app)
    - pip install google-api-python-client google-auth-oauthlib google-auth-httplib2

Usage:
    python google_auth.py gmail     # opens browser, logs you in, saves token
    python google_auth.py calendar  # same for calendar
    python google_auth.py status    # shows which account is linked

Security notes:
    - Tokens saved locally (tokens/*.pkl) with 0o600 permissions
    - Client secrets in .gitignored client_secrets.json
    - Read-only scopes only
    - Never exposes tokens to the web frontend
"""

import json
import os
import pickle
import threading
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
CLIENT_SECRETS_PATH = PROJECT_ROOT / "client_secrets.json"
TOKEN_DIR = PROJECT_ROOT / "tokens"
TOKEN_DIR.mkdir(exist_ok=True)

GMAIL_TOKEN_FILE = "gmail_token.pkl"
CALENDAR_TOKEN_FILE = "calendar_token.pkl"

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

REDIRECT_URI = "http://localhost:8888/"

_gmail_creds = None
_calendar_creds = None
_cache_lock = threading.Lock()


def _ensure_client_secrets():
    if not CLIENT_SECRETS_PATH.exists():
        raise FileNotFoundError(
            f"MISSING: {CLIENT_SECRETS_PATH}\n"
            "To fix:\n"
            "1) Go to https://console.cloud.google.com/apis/credentials\n"
            "2) Create OAuth client ID (Desktop app)\n"
            f"3) Download JSON and save it as {CLIENT_SECRETS_PATH}"
        )


def get_client_secrets() -> Dict[str, Any]:
    _ensure_client_secrets()
    with open(CLIENT_SECRETS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # InstalledAppFlow needs the FULL file (with "installed" or "web" wrapper)
    return data


def load_token_file(name: str) -> Optional[Credentials]:
    p = TOKEN_DIR / name
    if not p.exists():
        return None
    try:
        with open(p, "rb") as f:
            c: Credentials = pickle.load(f)
        if c.valid:
            return c
        if c.expired and c.refresh_token:
            c.refresh(Request())
            with open(p, "wb") as f:
                pickle.dump(c, f)
            return c
        # Expired without refresh token
        p.unlink()
        return None
    except Exception:
        p.unlink(missing_ok=True)
        return None


def save_token_file(creds: Credentials, name: str) -> None:
    p = TOKEN_DIR / name
    with open(p, "wb") as f:
        pickle.dump(creds, f)
    os.chmod(p, 0o600)


def get_gmail_creds() -> Optional[Credentials]:
    global _gmail_creds
    with _cache_lock:
        if _gmail_creds is not None:
            return _gmail_creds
    c = load_token_file(GMAIL_TOKEN_FILE)
    with _cache_lock:
        if c is not None:
            _gmail_creds = c
    return c


def get_calendar_creds() -> Optional[Credentials]:
    global _calendar_creds
    with _cache_lock:
        if _calendar_creds is not None:
            return _calendar_creds
    c = load_token_file(CALENDAR_TOKEN_FILE)
    with _cache_lock:
        if c is not None:
            _calendar_creds = c
    return c


def _auth_flow(scopes: list, token_file: str, label: str):
    secrets = get_client_secrets()
    # InstalledAppFlow handles browser open + redirect properly
    flow = InstalledAppFlow.from_client_config(
        secrets,
        scopes=scopes,
        redirect_uri=REDIRECT_URI,
    )
    # This opens the browser automatically
    print(f"[Google Auth] Opening browser for {label} authentication...")
    print(f"[Google Auth] If browser doesn't open, copy the URL below and paste it manually:")
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    print(f"\nAUTH URL: {auth_url}\n")
    # Try to open browser; if it fails, user pastes manually
    try:
        webbrowser.open(auth_url)
    except Exception:
        pass

    # Get the authorization code
    print(f"[Google Auth] After allowing access in the browser,")
    print(f"[Google Auth] you will be redirected (or shown a code).")
    print(f"[Google Auth] If redirected to localhost, the code is captured automatically.")
    print(f"[Google Auth] Otherwise, copy the 'code=' value from the URL and paste it below.")

    # For desktop apps using InstalledAppFlow with redirect, the user
    # typically sees the redirect URL in browser. We ask for the code.
    auth_code = input(f"Enter authorization code for {label}: ").strip()

    if not auth_code:
        # Some flows redirect to localhost; try to fetch from redirect URI
        # For simplicity we rely on user input. If user presses enter,
        # we try running the local server way (simpler)
        print(f"[Google Auth] No code provided. Falling back to local server flow...")
        try:
            # Run local server to catch redirect
            creds = flow.run_local_server(host="localhost", port=8888, open_browser=True)
        except Exception as e:
            print(f"[Google Auth] Fallback also failed: {e}")
            return None
    else:
        try:
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
        except Exception as e:
            print(f"[Google Auth] Failed to fetch token with code: {e}")
            # Try the local server fallback
            try:
                creds = flow.run_local_server(host="localhost", port=8888, open_browser=False)
            except Exception as e2:
                print(f"[Google Auth] Fallback failed: {e2}")
                return None

    save_token_file(creds, token_file)
    global _gmail_creds, _calendar_creds
    if token_file == GMAIL_TOKEN_FILE:
        _gmail_creds = creds
    else:
        _calendar_creds = creds
    return creds


def authenticate_gmail(force_reauth: bool = False) -> Optional[Credentials]:
    global _gmail_creds
    if not force_reauth:
        existing = get_gmail_creds()
        if existing:
            return existing
    print("[Google Auth] Gmail authentication started.")
    try:
        return _auth_flow(GMAIL_SCOPES, GMAIL_TOKEN_FILE, "Gmail")
    except Exception as e:
        print(f"[Google Auth] Gmail auth error: {e}")
        return None


def authenticate_calendar(force_reauth: bool = False) -> Optional[Credentials]:
    global _calendar_creds
    if not force_reauth:
        existing = get_calendar_creds()
        if existing:
            return existing
    print("[Google Auth] Calendar authentication started.")
    try:
        return _auth_flow(CALENDAR_SCOPES, CALENDAR_TOKEN_FILE, "Calendar")
    except Exception as e:
        print(f"[Google Auth] Calendar auth error: {e}")
        return None


def get_gmail_service():
    c = get_gmail_creds()
    if not c:
        return None
    try:
        return build("gmail", "v1", credentials=c)
    except Exception as e:
        print(f"[Google Auth] Gmail service build error: {e}")
        return None


def get_calendar_service():
    c = get_calendar_creds()
    if not c:
        return None
    try:
        return build("calendar", "v3", credentials=c)
    except Exception as e:
        print(f"[Google Auth] Calendar service build error: {e}")
        return None


def clear_gmail_token() -> None:
    global _gmail_creds
    p = TOKEN_DIR / GMAIL_TOKEN_FILE
    p.unlink(missing_ok=True)
    with _cache_lock:
        _gmail_creds = None
    print("[Google Auth] Gmail token cleared.")


def clear_calendar_token() -> None:
    global _calendar_creds
    p = TOKEN_DIR / CALENDAR_TOKEN_FILE
    p.unlink(missing_ok=True)
    with _cache_lock:
        _calendar_creds = None
    print("[Google Auth] Calendar token cleared.")


def is_gmail_authenticated() -> bool:
    return get_gmail_creds() is not None


def is_calendar_authenticated() -> bool:
    return get_calendar_creds() is not None


def list_token_files() -> list:
    return [f.name for f in TOKEN_DIR.glob("*.pkl") if f.is_file()]


def get_connected_email(service_type: str = "gmail") -> str:
    service = get_gmail_service() if service_type == "gmail" else get_calendar_service()
    if not service:
        return "not authenticated"
    try:
        if service_type == "gmail":
            profile = service.users().getProfile(userId="me").execute()
            return profile.get("emailAddress", "unknown")
        else:
            # Calendar: get settings for user email info
            settings = service.settings().get(userId="me", setting="calendar").execute()
            # The settings response may contain the calendar ID (email-like for primary)
            return settings.get("id", "unknown")
    except Exception:
        return "unknown"


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "gmail":
        creds = authenticate_gmail()
        if creds:
            print(f"[Google Auth] Gmail OK. Account: {get_connected_email('gmail')}")
        else:
            print("[Google Auth] Gmail authentication failed or cancelled.")

    elif cmd == "calendar":
        creds = authenticate_calendar()
        if creds:
            print("[Google Auth] Calendar OK.")
        else:
            print("[Google Auth] Calendar authentication failed or cancelled.")

    elif cmd == "status":
        g = is_gmail_authenticated()
        c = is_calendar_authenticated()
        print(f"Gmail:    {'CONNECTED' if g else 'NOT AUTHENTICATED'}")
        print(f"Calendar: {'CONNECTED' if c else 'NOT AUTHENTICATED'}")
        if g:
            print(f"  Gmail account: {get_connected_email('gmail')}")

    else:
        print("Usage:")
        print("  python google_auth.py gmail     -> login to Gmail")
        print("  python google_auth.py calendar  -> login to Calendar")
        print("  python google_auth.py status    -> check connection")
