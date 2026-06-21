"""
NPG Suite — Unified Practice Dashboard
=======================================
Seven-tab desktop application:
  Tab 1 · Test Checker       — Calendar-based test checking & patient reminders
  Tab 2 · Test Transfer      — Google Sheets → Excel → patient folder + transcript
  Tab 3 · Report Builder     — Qwen 3-call segmented (primary) + OpenAI (alternative)
  Tab 4 · Report Editor      — Edit draft report and export to formatted PDF
  Tab 5 · Report Sender      — PDF report → patient email + referring provider email/fax
  Tab 6 · Billing Assistant  — Insurance form → ICD-10 → billing email
  Tab 7 · Superbill          — Insurance data → Superbill PDF (standard / self-pay)


Config:     C:\\ProgramData\\NollPsych\\config.json   (or next to this .py / .exe)
Service account: set in config.json → google_service_account_json
"""


from __future__ import annotations


# ── stdlib ────────────────────────────────────────────────────────────────────
import datetime as dt
import glob
import hashlib
import html as htmllib
import json
import math
import os
import queue
import re
import shutil
import smtplib
import string
import subprocess
import sys
import threading
import time
import traceback
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


# ── GUI ────────────────────────────────────────────────────────────────────────
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


# ── Third-party (graceful degradation) ────────────────────────────────────────
try:
    import requests
except ImportError:
    requests = None  # type: ignore


try:
    import gspread
    from google.oauth2.service_account import Credentials as SACredentials
    from googleapiclient.discovery import build as google_build
    GOOGLE_OK = True
except ImportError:
    GOOGLE_OK = False
    gspread = None  # type: ignore
    SACredentials = None  # type: ignore
    google_build = None  # type: ignore


try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore


try:
    import xlwings as xw
except ImportError:
    xw = None  # type: ignore


try:
    from openpyxl import load_workbook as openpyxl_load_workbook
except ImportError:
    openpyxl_load_workbook = None  # type: ignore


try:
    import pandas as pd
except ImportError:
    pd = None  # type: ignore


try:
    import docx as python_docx
except ImportError:
    python_docx = None  # type: ignore


try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None  # type: ignore


try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors as rl_colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle, HRFlowable,
                                     BaseDocTemplate, Frame, PageTemplate,
                                     NextPageTemplate, Image as RLImage)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False


try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None  # type: ignore


# =============================================================================
# ── PATHS / CONFIG ────────────────────────────────────────────────────────────
# =============================================================================


APP_FOLDER_NAME   = "NollPsych"
REPORT_SENDER_FOLDER = "Report_Sender"
BILLING_FOLDER    = "Billing_Assistant"


# ── Report Editor asset paths ─────────────────────────────────────────────────
_RE_LOGO_PRIMARY  = r"C:\Suite\assets\npg_logo.png"
_RE_LOGO_FALLBACK = r"C:\ProgramData\NollPsych\npg_logo.png"
_RE_SIG_PRIMARY   = r"C:\Suite\assets\noll_signature.png"
_RE_SIG_FALLBACK  = r"C:\ProgramData\NollPsych\noll_signature.png"


def _re_asset(primary: str, fallback: str) -> str:
    return primary if os.path.exists(primary) else fallback


def _app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _programdata_dir(sub: str = APP_FOLDER_NAME) -> str:
    base = os.environ.get("PROGRAMDATA") or r"C:\ProgramData"
    return os.path.join(base, sub)


def _candidate_config_paths() -> List[str]:
    pd_path = os.path.join(_programdata_dir(), "config.json")
    app_path = os.path.join(_app_dir(), "config.json")
    cwd_path = os.path.join(os.getcwd(), "config.json")
    # Legacy paths
    legacy1 = r"C:\NPG_DesktopApp\config.json"
    legacy2 = os.path.join(_programdata_dir("Report_Sender"), "config.json")
    return [pd_path, app_path, cwd_path, legacy1, legacy2]


def load_config() -> Dict[str, Any]:
    tried: List[str] = []
    for p in _candidate_config_paths():
        tried.append(p)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            cfg["_loaded_from"] = p
            cfg["_config_dir"]  = os.path.dirname(p)
            return cfg
    raise FileNotFoundError(
        "config.json not found. Tried:\n  " + "\n  ".join(tried)
    )


def _candidate_report_config_paths() -> List[str]:
    return [
        os.path.join(_programdata_dir(), "report_config.json"),
        os.path.join(_app_dir(), "report_config.json"),
        r"C:\NPG_DesktopApp\report_config.json",
        os.path.join(os.getcwd(), "report_config.json"),
    ]


def load_report_config_raw() -> Dict[str, Any]:
    for p in _candidate_report_config_paths():
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return {}


def _resolve_sa_path(cfg: Dict[str, Any]) -> str:
    """Resolve service_account JSON path from config, checking multiple locations."""
    raw = cfg.get("google_service_account_json") or ""
    candidates = []
    if raw:
        candidates.append(raw)
        if not os.path.isabs(raw):
            candidates.append(os.path.join(_app_dir(), raw))
    # common fallbacks
    candidates += [
        os.path.join(_programdata_dir(), "service_account.json"),
        os.path.join(_programdata_dir("Report_Sender"), "service_account.json"),
        os.path.join(_app_dir(), "service_account.json"),
        r"C:\NPG_DesktopApp\service_account.json",
        r"C:\ProgramData\Report_Sender\service_account.json",
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return raw  # return raw for error messaging


def _resolve_contacts_path() -> str:
    for d in [r"C:\Suite", _programdata_dir(REPORT_SENDER_FOLDER), _app_dir()]:
        p = os.path.join(d, "provider_contacts.json")
        if os.path.exists(p):
            return p
    return os.path.join(_programdata_dir(REPORT_SENDER_FOLDER), "provider_contacts.json")


def _resolve_icd_cache_path() -> str:
    d = _programdata_dir(BILLING_FOLDER)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "icd10_cache.json")


def _resolve_patients_root(cfg: Dict[str, Any]) -> str:
    raw = (cfg.get("patients_root") or cfg.get("patient_root_folder") or "").strip()
    for p in [raw, r"C:\nollpsych\patients", r"C:\NollPsych\Patients"]:
        if p and os.path.isdir(p):
            return p
    return raw or r"C:\nollpsych\patients"


def _ensure_scaffold() -> None:
    for sub in [APP_FOLDER_NAME, REPORT_SENDER_FOLDER, BILLING_FOLDER]:
        os.makedirs(_programdata_dir(sub), exist_ok=True)


# =============================================================================
# ── SHARED UTILITIES ──────────────────────────────────────────────────────────
# =============================================================================


def _now_ts() -> str:
    return time.strftime("[%H:%M:%S]")


def normalize_email(s: str) -> str:
    return (s or "").strip().lower()


def normalize_name(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower().strip())


def digits_only(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def parse_cc_list(raw: str) -> List[str]:
    parts = re.split(r"[;,]+", (raw or "").strip())
    return [p.strip() for p in parts if p.strip() and "@" in p]


def safe_get(d: Dict, *keys, default=None):
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def html_to_text(s: str) -> str:
    s = s or ""
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</p>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = htmllib.unescape(s).replace("\u00a0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    lines = [ln.strip() for ln in s.split("\n")]
    out: List[str] = []
    blank = 0
    for ln in lines:
        if not ln:
            blank += 1
            if blank <= 1:
                out.append("")
        else:
            blank = 0
            out.append(ln)
    return "\n".join(out).strip()


def normalize_newlines(text: str) -> str:
    return (text or "").replace("\r\n", "\n").replace("\r", "\n")


def open_file_os(path: str) -> None:
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)
    except Exception:
        pass


def call_with_retry(func, *args, log=None, **kwargs):
    if log is None:
        def log(_m): pass
    backoffs = [1.0, 1.5, 2.0, 3.0, 4.5]
    last_exc = None
    for i, b in enumerate(backoffs, 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exc = e
            msg = str(e)
            transient = any(code in msg for code in
                            ["429", "503", "502", "500", "rateLimitExceeded", "backendError"])
            if not transient:
                raise
            log(f"⚠️ Google transient error — backing off {b:.1f}s ({i}/{len(backoffs)})")
            time.sleep(b)
    raise last_exc


# =============================================================================
# ── GOOGLE CLIENT FACTORY ─────────────────────────────────────────────────────
# =============================================================================


SCOPES_SHEETS   = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SCOPES_CALENDAR = ["https://www.googleapis.com/auth/calendar.readonly"]
SCOPES_DRIVE    = ["https://www.googleapis.com/auth/drive.readonly"]
SCOPES_FULL     = SCOPES_SHEETS + SCOPES_CALENDAR + SCOPES_DRIVE


def _build_creds(sa_path: str, scopes: List[str]):
    if not GOOGLE_OK:
        raise RuntimeError("google-auth / google-api-python-client not installed.")
    return SACredentials.from_service_account_file(sa_path, scopes=scopes)


def init_gspread_client(sa_path: str):
    creds = _build_creds(sa_path, SCOPES_SHEETS)
    return gspread.authorize(creds)


def init_calendar_service(sa_path: str):
    creds = _build_creds(sa_path, SCOPES_CALENDAR)
    return google_build("calendar", "v3", credentials=creds, cache_discovery=False)


def init_drive_service(sa_path: str):
    creds = _build_creds(sa_path, SCOPES_DRIVE)
    return google_build("drive", "v3", credentials=creds, cache_discovery=False)




SCOPES_GMAIL    = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.modify",
]


def init_gmail_service(sa_path: str, delegated_user: str):
    """
    Build a Gmail API client using domain-wide delegation.


    SETUP REQUIRED (one-time, ~5 minutes):
    1. Google Admin Console → Security → API Controls → Domain-wide Delegation
    2. Add the service account's Client ID
    3. Scopes to grant (comma-separated in Admin Console):
       https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.labels,https://www.googleapis.com/auth/gmail.modify
       NOTE: gmail.send is NOT needed — replies use the existing SMTP config.
    4. Set config.json → calendar_owner_email to the mailbox to access
       (e.g. "nicholas@nollpsychgroup.com")


    delegated_user: the Gmail address to impersonate (calendar_owner_email)
    """
    if not GOOGLE_OK:
        raise RuntimeError("google-auth / google-api-python-client not installed.")
    creds = SACredentials.from_service_account_file(sa_path, scopes=SCOPES_GMAIL)
    creds = creds.with_subject(delegated_user)
    return google_build("gmail", "v1", credentials=creds, cache_discovery=False)


# =============================================================================
# ── SMTP HELPER ───────────────────────────────────────────────────────────────
# =============================================================================


def send_smtp(
    smtp_conf: Dict[str, Any],
    to_emails: List[str],
    subject: str,
    body: str,
    attachments: Optional[List[str]] = None,
    cc_emails: Optional[List[str]] = None,
    log: Callable[[str], None] = print,
) -> bool:
    host       = smtp_conf.get("host", "smtp.gmail.com")
    port       = int(smtp_conf.get("port", 587))
    username   = smtp_conf.get("username", "")
    password   = smtp_conf.get("app_password") or smtp_conf.get("password", "")
    from_name  = smtp_conf.get("from_name", "Noll Psych Group")
    from_email = smtp_conf.get("from_email", username)
    use_tls    = bool(smtp_conf.get("use_tls", True))


    to_emails = [e.strip() for e in (to_emails or []) if e and e.strip()]
    cc_emails = [e.strip() for e in (cc_emails or []) if e and e.strip()]


    if not (host and port and username and password and from_email):
        log("❌ SMTP configuration incomplete.")
        return False
    if not to_emails:
        log("❌ No recipients specified.")
        return False


    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"]    = f"{from_name} <{from_email}>"
    msg["To"]      = ", ".join(to_emails)
    if cc_emails:
        msg["Cc"]  = ", ".join(cc_emails)
    msg.set_content(body)


    for path in (attachments or []):
        try:
            with open(path, "rb") as f:
                data = f.read()
            msg.add_attachment(data, maintype="application", subtype="pdf",
                               filename=os.path.basename(path))
        except Exception as e:
            log(f"❌ Failed to attach {path}: {e}")
            return False


    try:
        log(f"Connecting to {host}:{port}…")
        with smtplib.SMTP(host, port, timeout=25) as srv:
            if use_tls:
                srv.starttls()
            srv.login(username, password)
            srv.send_message(msg)
        log("✅ Email sent.")
        return True
    except smtplib.SMTPAuthenticationError as e:
        log(f"❌ SMTP auth failed: {e}")
        return False
    except Exception as e:
        log(f"❌ SMTP send failed: {e}")
        return False


# =============================================================================
# ── CALENDAR HELPERS ──────────────────────────────────────────────────────────
# =============================================================================


def resolve_calendar_id(cfg: Dict[str, Any]) -> str:
    cal_id = (cfg.get("calendar_id") or "").strip()
    owner  = (cfg.get("calendar_owner_email") or "").strip()
    if not cal_id:
        raise ValueError("Missing 'calendar_id' in config.json")
    if cal_id.lower() == "primary" and owner:
        return owner
    return cal_id


def fetch_calendar_events(
    cal_service,
    calendar_id: str,
    start_date: dt.date,
    end_date: dt.date,
    tz_str: str,
    log: Callable[[str], None] = print,
) -> List[Dict[str, Any]]:
    if end_date < start_date:
        start_date, end_date = end_date, start_date


    if ZoneInfo is not None:
        tz = ZoneInfo(tz_str)
        t_min = dt.datetime.combine(start_date, dt.time.min).replace(tzinfo=tz).isoformat()
        t_max = dt.datetime.combine(end_date + dt.timedelta(days=1), dt.time.min).replace(tzinfo=tz).isoformat()
    else:
        t_min = dt.datetime.combine(start_date, dt.time.min).isoformat() + "Z"
        t_max = dt.datetime.combine(end_date + dt.timedelta(days=1), dt.time.min).isoformat() + "Z"


    log(f"Fetching calendar: {start_date} → {end_date} (tz={tz_str})")
    result = call_with_retry(
        cal_service.events().list,
        calendarId=calendar_id,
        timeMin=t_min, timeMax=t_max,
        timeZone=tz_str,
        singleEvents=True, orderBy="startTime",
        maxResults=2500,
        log=log,
    ).execute()
    return result.get("items", [])


def extract_patient_email_from_event(event: Dict[str, Any], owner_email: str) -> Optional[str]:
    owner      = normalize_email(owner_email)
    organizer  = normalize_email(safe_get(event, "organizer", "email") or "")
    creator    = normalize_email(safe_get(event, "creator",   "email") or "")
    skip       = {owner, organizer, creator}


    for a in (event.get("attendees") or []):
        email = normalize_email(a.get("email", ""))
        if email and email not in skip and a.get("responseStatus") != "declined":
            return email


    desc = event.get("description") or ""
    m = re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", desc, flags=re.I)
    if m:
        email = normalize_email(m.group(0))
        if email and email not in skip:
            return email
    return None


def infer_patient_name_from_event(event: Dict[str, Any]) -> str:
    summary = event.get("summary") or ""
    m = re.search(r"\(([^)]+)\)", summary)
    if m:
        return m.group(1).strip()
    return summary.strip() or "(unknown)"


def event_start_str(event: Dict[str, Any]) -> str:
    return safe_get(event, "start", "dateTime") or safe_get(event, "start", "date") or ""


# =============================================================================
# ── NAME MATCHING (for Test Transfer) ─────────────────────────────────────────
# =============================================================================


_NICKNAMES = {
    "danny": {"daniel"}, "dan": {"daniel"}, "mike": {"michael"},
    "bill": {"william"}, "billy": {"william"}, "will": {"william"},
    "liz": {"elizabeth"}, "beth": {"elizabeth"},
    "kate": {"katherine", "kathryn"}, "kathy": {"katherine", "kathryn"},
    "bob": {"robert"}, "rob": {"robert"}, "jim": {"james"},
    "dave": {"david"}, "steve": {"steven", "stephen"},
    "jen": {"jennifer"}, "chris": {"christopher"},
}


def _cn(s: str) -> str:
    return re.sub(r"[^a-z]", "", (s or "").strip().lower())


def _first_match(a: str, b: str) -> bool:
    a0, b0 = _cn(a), _cn(b)
    if not a0 or not b0: return False
    if a0 == b0: return True
    if b0 in _NICKNAMES.get(a0, set()): return True
    if a0 in _NICKNAMES.get(b0, set()): return True
    if len(a0) >= 3 and (b0.startswith(a0) or a0.startswith(b0)): return True
    if len(a0) >= 3 and len(b0) >= 3 and a0[:3] == b0[:3]: return True
    if a0[0] == b0[0] and (len(a0) <= 4 or len(b0) <= 4): return True
    return False


def _last_match(a: str, b: str) -> bool:
    a0, b0 = _cn(a), _cn(b)
    if not a0 or not b0: return False
    if a0 == b0: return True
    if len(a0) >= 4 and b0.startswith(a0): return True
    if len(b0) >= 4 and a0.startswith(b0): return True
    return False


def _split_name(name: str) -> Tuple[str, str]:
    toks = [t for t in re.split(r"[,\s]+", (name or "").strip()) if t]
    if not toks: return "", ""
    if len(toks) == 1: return toks[0], toks[0]
    return toks[0], toks[-1]


def liberal_fullname_match(patient_name: str, row_first: str, row_last: str, row_full: str = "") -> bool:
    p_first, p_last = _split_name(patient_name)
    if row_last and _last_match(p_last, row_last):
        if row_first: return _first_match(p_first, row_first)
        if row_full:
            toks = [t for t in re.split(r"[,\s]+", row_full.strip()) if t]
            if toks: return _first_match(p_first, toks[0])
        return True
    if row_full:
        toks = [t for t in re.split(r"[,\s]+", row_full.strip()) if t]
        if len(toks) >= 2:
            return _last_match(p_last, toks[-1]) and _first_match(p_first, toks[0])
    return False


# =============================================================================
# ── REPORT PAYLOAD BUILDER ────────────────────────────────────────────────────
# =============================================================================


def _find_workbook(patient_folder: str, pattern: str) -> Optional[str]:
    matches = glob.glob(os.path.join(patient_folder, pattern))
    return matches[0] if matches else None


def _extract_ai_export_xlwings(wb_path: str, sheet: str) -> Optional[Any]:
    if xw is None: return None
    try:
        app = xw.App(visible=False, add_book=False)
        app.display_alerts = False
        app.screen_updating = False
        wb = app.books.open(wb_path, update_links=False, read_only=True)
        try:
            sht = wb.sheets[sheet]
        except Exception:
            wb.close(); app.quit(); return None
        vals = sht.used_range.value
        wb.close(); app.quit()
        if not vals or not isinstance(vals, list) or len(vals) < 2:
            return None
        header = [str(x).strip() if x is not None else "" for x in vals[0]]
        if pd:
            df = pd.DataFrame(vals[1:], columns=header)
            return df
        return {"header": header, "rows": vals[1:]}
    except Exception:
        try: app.quit()  # type: ignore
        except Exception: pass
        return None


def _extract_ai_export_openpyxl(wb_path: str, sheet: str) -> Optional[List[Dict]]:
    if openpyxl_load_workbook is None: return None
    try:
        wb = openpyxl_load_workbook(wb_path, data_only=True)
        if sheet not in wb.sheetnames: return None
        ws = wb[sheet]
        data = list(ws.values)
        if not data or len(data) < 2: return None
        header = [str(x).strip() if x is not None else "" for x in data[0]]
        rows = []
        for row in data[1:]:
            rows.append({header[i]: (row[i] if i < len(row) else None) for i in range(len(header))})
        return rows
    except Exception:
        return None


def load_ai_export(wb_path: str, sheet: str = "AI_Export") -> List[Dict]:
    if pd:
        result = _extract_ai_export_xlwings(wb_path, sheet)
        if result is not None and hasattr(result, "iterrows"):
            result = result.where(result.notna(), None)
            return [{c: row[c] for c in result.columns} for _, row in result.iterrows()]
    rows = _extract_ai_export_openpyxl(wb_path, sheet)
    return rows or []


def _read_transcript(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx" and python_docx:
        try:
            doc = python_docx.Document(path)
            return "\n".join(p.text for p in doc.paragraphs if p.text)
        except Exception:
            pass
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def find_transcripts_in_folder(patient_folder: str) -> List[str]:
    exts = (".docx", ".doc", ".txt", ".rtf", ".pdf")
    patterns_prio = ["*Notes by Gemini*.docx", "*transcript*.txt", "*transcript*.docx"]
    found: List[str] = []
    for pat in patterns_prio:
        m = glob.glob(os.path.join(patient_folder, pat))
        found.extend(m)
    if not found:
        for fn in os.listdir(patient_folder):
            if os.path.splitext(fn)[1].lower() in exts:
                found.append(os.path.join(patient_folder, fn))
    found.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return found


def build_report_payload(patient_folder: str, rcfg: Dict[str, Any]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "patient_folder": patient_folder,
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        "tests": {},
        "transcript": {},
    }
    for tc in rcfg.get("tests", []):
        name    = tc.get("name", "")
        pattern = tc.get("file_pattern", "")
        sheet   = tc.get("ai_export_sheet", "AI_Export")
        wb      = _find_workbook(patient_folder, pattern)
        if not wb:
            payload["tests"][name] = {"rows": [], "error": f"No workbook matching: {pattern}"}
            continue
        rows = load_ai_export(wb, sheet)
        payload["tests"][name] = {"workbook_path": wb, "rows": rows, "error": None}


    transcripts = find_transcripts_in_folder(patient_folder)
    if transcripts:
        payload["transcript"] = {"path": transcripts[0], "text": _read_transcript(transcripts[0])}
    return payload


def save_payload(patient_folder: str, payload: Dict[str, Any]) -> str:
    out = os.path.join(patient_folder, "report_data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)
    return out


# =============================================================================
# ── QWEN (OPEN WEBUI) PIPELINE ────────────────────────────────────────────────
# =============================================================================


# Default Qwen endpoint on Spark device (LAN).  Override in report_config.json
# under the "qwen" key.  Tailscale address:  100.123.33.43
# Tailscale hostname:                        spark-c17b
QWEN_DEFAULT_URL   = "http://100.123.33.43:8000"  # vLLM on spark-c17b (Tailscale)
QWEN_DEFAULT_MODEL = "Qwen3-235B"


HTTP_TIMEOUT = 900


@dataclass
class QwenConfig:
    base_url: str      = QWEN_DEFAULT_URL
    model: str         = QWEN_DEFAULT_MODEL
    temperature: float = 0.2
    timeout_sec: int   = HTTP_TIMEOUT
    api_key: str       = ""
    api_path: str      = "/v1/chat/completions"        # vLLM OpenAI-compatible endpoint


def load_qwen_config(rcfg: Dict[str, Any]) -> QwenConfig:
    """Load Qwen/Open-WebUI config from report_config.json.
    Keys tried in order: 'qwen', 'heretic', 'webui' (legacy names accepted)."""
    h = rcfg.get("qwen") or rcfg.get("heretic") or rcfg.get("webui") or {}


    # API key: check report_config.json, then ndp4 settings file, then env var
    api_key = h.get("api_key") or h.get("key") or ""
    if not api_key:
        settings_path = os.path.join(_programdata_dir(), "npg_dspy_pipeline_settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                api_key = settings.get("webui_api_key", "")
            except Exception:
                pass
    if not api_key:
        api_key = os.environ.get("OPENWEBUI_API_KEY", "")


    return QwenConfig(
        base_url    = h.get("base_url", QWEN_DEFAULT_URL),
        model       = h.get("model",    QWEN_DEFAULT_MODEL),
        temperature = float(h.get("temperature", 0.2)),
        timeout_sec = int(h.get("timeout_sec", HTTP_TIMEOUT)),
        api_key     = api_key,
        api_path    = h.get("api_path", "/v1/chat/completions"),
    )


# Keep legacy name so any external code that imports it still works
HereticConfig     = QwenConfig
load_heretic_config = load_qwen_config


def _webui_call(url: str, model: str, temperature: float, timeout: int,
                messages: List[Dict], max_tokens: Optional[int] = None,
                api_key: str = "") -> Tuple[str, Optional[str]]:
    if requests is None:
        raise RuntimeError("requests library not installed.")
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    body: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
        "max_tokens": max_tokens if max_tokens else 2048,
    }
    r = requests.post(url, headers=headers, json=body, timeout=max(10, timeout))
    if not r.ok:
        # Include vLLM's error detail in the exception message
        try:
            detail = r.json()
        except Exception:
            detail = r.text[:500]
        raise RuntimeError(f"{r.status_code} {r.reason} — {detail}")
    rj = r.json()
    choices = rj.get("choices") or []
    if choices:
        c0 = choices[0]
        content = ((c0.get("message") or {}).get("content") or "").strip()
        finish  = c0.get("finish_reason")
        # Strip Qwen3 thinking tokens — remove <think>…</think> blocks entirely
        content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
        return content, finish
    return "", None


def _looks_truncated(t: str) -> bool:
    s = (t or "").strip()
    if not s: return False
    if s.endswith((",", ":", ";", "-", "—", "…", "...")): return True
    if not any(s.endswith(x) for x in [".", "!", "?", '"', "\u201d", "\u2019"]): return True
    return False


def _truncate_payload_to_fit(payload: Dict[str, Any], prompt_text: str,
                              max_context_tokens: int = 16384,
                              reserved_output_tokens: int = 2048,
                              chars_per_token: float = 3.5) -> Dict[str, Any]:
    """
    Trim the payload so that prompt + serialized payload fits within the model's
    context window, leaving room for the output.
    Reduces transcript text first (biggest contributor), then other long strings.
    """
    # Budget: total context minus prompt minus output reservation minus safety buffer
    safety_buffer = 500
    prompt_tokens  = len(prompt_text) / chars_per_token
    budget_tokens  = max_context_tokens - prompt_tokens - reserved_output_tokens - safety_buffer
    budget_chars   = max(2000, int(budget_tokens * chars_per_token))


    # Quick check — if it already fits, return unchanged
    serialized = json.dumps(payload, ensure_ascii=False, default=str)
    if len(serialized) <= budget_chars:
        return payload


    # Deep-copy so we don't mutate the caller's dict
    import copy
    p = copy.deepcopy(payload)


    # 1. Trim transcript text first (largest single field)
    trans = p.get("transcript") or {}
    if isinstance(trans, dict) and trans.get("text"):
        other_chars = len(json.dumps(
            {k: v for k, v in p.items() if k != "transcript"}, default=str))
        max_trans = max(500, budget_chars - other_chars - 200)
        if len(trans["text"]) > max_trans:
            trans["text"] = trans["text"][:max_trans] + "\n… [truncated to fit context window]"
            p["transcript"] = trans
        serialized = json.dumps(p, ensure_ascii=False, default=str)


    # 2. If still too long, trim context_from_prior_sections (Phase 3 specific)
    if len(serialized) > budget_chars:
        ctx = p.get("context_from_prior_sections") or {}
        if ctx:
            remaining = budget_chars - len(json.dumps(
                {k: v for k, v in p.items() if k != "context_from_prior_sections"}, default=str))
            max_ctx = max(500, remaining - 200)
            for key in ("background_section_text", "test_results_section_text"):
                if isinstance(ctx.get(key), str) and len(ctx[key]) > max_ctx // 2:
                    ctx[key] = ctx[key][:max_ctx // 2] + "\n… [truncated]"
            p["context_from_prior_sections"] = ctx
            serialized = json.dumps(p, ensure_ascii=False, default=str)


    # 3. Last resort: trim any remaining long string values proportionally
    if len(serialized) > budget_chars:
        def _trim(obj, limit):
            if isinstance(obj, str) and len(obj) > 200:
                return obj[:limit] + "…" if limit > 10 else "…"
            if isinstance(obj, dict):
                out = {}
                per = max(100, limit // max(1, len(obj)))
                for k, v in obj.items():
                    out[k] = _trim(v, per)
                return out
            if isinstance(obj, list):
                per = max(50, limit // max(1, len(obj)))
                return [_trim(i, per) for i in obj]
            return obj
        p = _trim(p, budget_chars)


    return p




def _heretic_phase(
    prompt_text: str,
    payload: Dict[str, Any],
    hcfg: QwenConfig,
    min_chars: int = 0,
    log: Callable[[str], None] = print,
) -> str:
    url = hcfg.base_url.rstrip("/") + hcfg.api_path


    # Trim payload to fit within the model's context window before sending
    payload = _truncate_payload_to_fit(payload, prompt_text)
    user_content = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    log(f"  → calling Qwen ({hcfg.model})… payload {len(user_content):,} chars")


    messages = [
        {"role": "system", "content": prompt_text},
        {"role": "user",   "content": user_content},
    ]
    text, finish = _webui_call(url, hcfg.model, hcfg.temperature, hcfg.timeout_sec, messages, api_key=hcfg.api_key)
    full = text.strip()


    # Continuation loop — dynamically cap max_tokens to what the context allows
    MAX_CONTEXT = 16384
    CHARS_PER_TOK = 3.5
    for _ in range(6):
        if finish != "length" and not _looks_truncated(full) and (not min_chars or len(full) >= min_chars):
            break
        log("  → output looks incomplete — continuing…")
        messages.append({"role": "assistant", "content": full})
        messages.append({"role": "user", "content":
            "Continue the report EXACTLY where you left off. "
            "Do not repeat earlier text. Pick up mid-sentence if needed. End with a period."})
        # Calculate how many tokens remain for the next output
        used_chars = sum(len(m["content"]) for m in messages)
        used_tokens = int(used_chars / CHARS_PER_TOK)
        available = max(64, MAX_CONTEXT - used_tokens - 100)
        continuation_max = min(1024, available)
        more, finish = _webui_call(url, hcfg.model, hcfg.temperature, hcfg.timeout_sec,
                                   messages, max_tokens=continuation_max, api_key=hcfg.api_key)
        if not more: break
        full = (full.rstrip() + "\n\n" + more.lstrip()).strip()


    return full


def _filter_payload_phase(payload: Dict[str, Any], phase: int) -> Dict[str, Any]:
    p = payload or {}
    def pick(*keys): return {k: p[k] for k in keys if k in p}
    if phase == 1:
        out = {}
        out.update(pick("demographics", "referral", "identifying_information"))
        out.update(pick("pif", "PIF", "intake", "history"))
        out.update(pick("transcript", "interview", "records", "collateral"))
        out.update(pick("meta", "metadata", "dates"))
        return out or p
    if phase == 2:
        out = {}
        out.update(pick("tests", "test_results", "measures"))
        out.update(pick("demographics", "referral"))
        out.update(pick("meta", "metadata", "dates"))
        return out or p
    # phase 3
    out = {}
    out.update(pick("demographics", "referral"))
    out.update(pick("tests", "test_results", "measures"))
    out.update(pick("meta", "metadata", "dates"))
    out.update(pick("pif", "PIF"))
    return out or p


def _summarize_for_phase3(t1: str, t2: str, max_chars: int = 3000) -> str:
    """
    Produce a compact summary of phases 1 & 2 to pass as context into phase 3.
    Keeps the last max_chars of each section (most clinically relevant content
    tends to appear after preamble) plus a leading snippet.
    """
    def _trim(text: str, budget: int) -> str:
        text = (text or "").strip()
        if len(text) <= budget:
            return text
        head = text[:200]
        tail = text[-(budget - 200):]
        return head + "\n… [middle truncated] …\n" + tail


    half = max_chars // 2
    s1 = _trim(t1, half)
    s2 = _trim(t2, half)
    return (
        "=== BACKGROUND / HISTORY (Phase 1 summary) ===\n" + s1 +
        "\n\n=== TEST RESULTS (Phase 2 summary) ===\n" + s2
    )




def _strip_llm_markdown(text: str) -> str:
    """
    Remove markdown artifacts that Qwen sometimes emits despite instructions.
    Converts headings to plain text, removes bold/italic markers, cleans up
    excess blank lines, and normalises bullet points to plain prose dashes.
    """
    lines = text.splitlines()
    out = []
    for line in lines:
        # Strip ATX headings: ### Foo  ->  Foo
        stripped = line.lstrip()
        if stripped.startswith("#"):
            line = re.sub(r"^#+\s*", "", stripped)
        # Bold/italic: **text** -> text, *text* -> text, __text__ -> text
        line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
        line = re.sub(r"\*([^*]+)\*",       r"\1", line)
        line = re.sub(r"__([^_]+)__",         r"\1", line)
        line = re.sub(r"_([^_]+)_",           r"\1", line)
        # Bullet points: leading - or * -> keep line content, strip marker
        line = re.sub(r"^(\s*)[-*]\s+", r"\1", line)
        # Horizontal rules
        if re.match(r"^[-*_]{3,}\s*$", line.strip()):
            continue
        out.append(line)
    result = "\n".join(out)
    # Collapse 3+ consecutive blank lines to 2
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()




def generate_qwen_single_prompt(
    payload: Dict[str, Any],
    hcfg: QwenConfig,
    prompt_text: str,
    log: Callable[[str], None] = print,
) -> str:
    """Single-call Qwen generation — analogous to the OpenAI path."""
    url = hcfg.base_url.rstrip("/") + hcfg.api_path
    payload = _truncate_payload_to_fit(payload, prompt_text)
    user_content = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    log(f"Engine: Qwen single-prompt ({hcfg.model})  payload {len(user_content):,} chars")
    messages = [
        {"role": "system", "content": prompt_text},
        {"role": "user",   "content": user_content},
    ]
    text, finish = _webui_call(
        url, hcfg.model, hcfg.temperature, hcfg.timeout_sec,
        messages, max_tokens=4096, api_key=hcfg.api_key)
    full = text.strip()
    for _ in range(8):
        if finish != "length" and not _looks_truncated(full) and len(full) >= 3000:
            break
        log("  → output looks incomplete — continuing…")
        messages.append({"role": "assistant", "content": full})
        messages.append({"role": "user", "content":
            "Continue the report EXACTLY where you left off. "
            "Do not repeat earlier text. Pick up mid-sentence if needed. End with a period."})
        more, finish = _webui_call(
            url, hcfg.model, hcfg.temperature, hcfg.timeout_sec,
            messages, max_tokens=2048, api_key=hcfg.api_key)
        if not more:
            break
        full = (full.rstrip() + "\n\n" + more.lstrip()).strip()
    full = _strip_llm_markdown(full)
    log(f"✅ Single-prompt report: {len(full):,} chars")
    return full




def generate_heretic_segmented(
    payload: Dict[str, Any],
    hcfg: QwenConfig,
    p1_prompt: str, p2_prompt: str, p3_prompt: str,
    log: Callable[[str], None] = print,
) -> str:
    """
    Three-phase segmented report generation designed to fit within Qwen's 16K
    context limit.  Each phase receives only the data it needs and a tightly
    bounded output budget so prompt + data + output never exceeds 16K tokens.


    Token budget per phase (chars, at 3.5 chars/token):
      Total context  = 16 384 tokens  → ~57 344 chars
      System prompt  ≈  2 000 tokens  →  ~7 000 chars  (generous estimate)
      Safety buffer  =    500 tokens  →  ~1 750 chars
      Available for data + output ≈ 48 594 chars
      Output target  ≈  4 096 tokens  → ~14 336 chars  (per phase)
      Data budget    ≈ 34 000 chars   (remainder after output reservation)
    """
    MAX_CONTEXT_TOKENS  = 16_384
    CHARS_PER_TOK       = 3.5
    # Per-phase output allowance (tokens).  Keeping this modest per phase;
    # report length comes from stitching all three phases together.
    OUTPUT_TOKENS_PER_PHASE = 1_200   # ~4 200 chars per call — fast on Qwen AWQ; continuation builds full length
    MIN_PHASE_CHARS = 2_000           # minimum acceptable section length before continuing


    def _run_phase(label: str, prompt: str, data_payload: Dict, phase_num: int) -> str:
        log(f"Phase {phase_num}: {label}…")
        # Compute how much of the context the prompt itself uses
        prompt_tokens = len(prompt) / CHARS_PER_TOK
        safety        = 400
        data_budget_tokens  = MAX_CONTEXT_TOKENS - prompt_tokens - OUTPUT_TOKENS_PER_PHASE - safety
        data_budget_chars   = max(4_000, int(data_budget_tokens * CHARS_PER_TOK))


        # Trim payload to fit in remaining data budget
        trimmed = _truncate_payload_to_fit(
            data_payload, prompt,
            max_context_tokens=MAX_CONTEXT_TOKENS,
            reserved_output_tokens=OUTPUT_TOKENS_PER_PHASE,
            chars_per_token=CHARS_PER_TOK,
        )
        user_content = json.dumps(trimmed, ensure_ascii=False, indent=2, default=str)


        # Warn if data still exceeds budget (truncation should handle it but log for visibility)
        if len(user_content) > data_budget_chars:
            log(f"  ⚠️  Phase {phase_num} data {len(user_content):,} chars > budget "
                f"{data_budget_chars:,} — model context may be tight")


        url = hcfg.base_url.rstrip("/") + hcfg.api_path
        log(f"  → calling Qwen ({hcfg.model})… data {len(user_content):,} chars  "
            f"max_tokens={OUTPUT_TOKENS_PER_PHASE}")


        messages = [
            {"role": "system", "content": prompt},
            {"role": "user",   "content": user_content},
        ]
        # Use at least 300s per call; shorter output = faster but still allow headroom
        call_timeout = max(300, hcfg.timeout_sec)
        text, finish = _webui_call(
            url, hcfg.model, hcfg.temperature, call_timeout,
            messages, max_tokens=OUTPUT_TOKENS_PER_PHASE, api_key=hcfg.api_key,
        )
        full = text.strip()


        # Continuation loop — up to 8 short passes to build full section length
        for _ in range(8):
            if finish != "length" and not _looks_truncated(full) and len(full) >= MIN_PHASE_CHARS:
                break
            log(f"  → output looks incomplete ({len(full):,} chars) — continuing…")
            messages.append({"role": "assistant", "content": full})
            messages.append({"role": "user", "content":
                "Continue the report EXACTLY where you left off. "
                "Do not repeat earlier text. Pick up mid-sentence if needed. End with a period."})
            used_chars   = sum(len(m["content"]) for m in messages)
            used_tokens  = int(used_chars / CHARS_PER_TOK)
            avail        = max(64, MAX_CONTEXT_TOKENS - used_tokens - 100)
            cont_max     = min(OUTPUT_TOKENS_PER_PHASE, avail)
            if cont_max < 64:
                log("  → no context budget remaining for continuation — stopping")
                break
            more, finish = _webui_call(
                url, hcfg.model, hcfg.temperature, call_timeout,
                messages, max_tokens=cont_max, api_key=hcfg.api_key,
            )
            if not more:
                break
            full = (full.rstrip() + "\n\n" + more.lstrip()).strip()


        full = _strip_llm_markdown(full)
        log(f"  Phase {phase_num} done ({len(full):,} chars after markdown strip)")
        return full


    t1 = _run_phase("Background / History",    p1_prompt, _filter_payload_phase(payload, 1), 1)
    t2 = _run_phase("Test Results",             p2_prompt, _filter_payload_phase(payload, 2), 2)


    # Phase 3: pass a compact summary of phases 1 & 2 instead of full text
    # This is the critical change — passing full t1+t2 text blows out the 16K window
    p3_base = _filter_payload_phase(payload, 3)
    ctx_summary = _summarize_for_phase3(t1, t2, max_chars=3_500)
    p3_base["context_from_prior_sections"] = ctx_summary
    t3 = _run_phase("Diagnoses / Recommendations", p3_prompt, p3_base, 3)


    stitched = "\n\n".join(t for t in [t1, t2, t3] if t.strip())
    log(f"✅ Total report: {len(stitched):,} chars")
    return stitched


# =============================================================================
# ── OPENAI PIPELINE ───────────────────────────────────────────────────────────
# =============================================================================


def generate_openai_report(
    payload: Dict[str, Any],
    rcfg: Dict[str, Any],
    log: Callable[[str], None] = print,
) -> str:
    if OpenAI is None:
        raise RuntimeError("openai library not installed.")
    oai = rcfg.get("openai") or {}
    model   = oai.get("model", "gpt-4o")
    api_key = oai.get("api_key") or os.environ.get("OPENAI_API_KEY", "")
    prompt_file = oai.get("prompt_file", "")


    # Resolve prompt
    prompt_text = ""
    for candidate in [
        prompt_file,
        os.path.join(_programdata_dir(), prompt_file),
        r"C:\NPG_DesktopApp\report_prompt.txt",
        os.path.join(_app_dir(), "report_prompt.txt"),
    ]:
        if candidate and os.path.exists(candidate):
            with open(candidate, "r", encoding="utf-8") as f:
                prompt_text = f.read()
            break


    if not prompt_text:
        raise FileNotFoundError(f"OpenAI prompt file not found: {prompt_file}")
    if not api_key:
        raise ValueError("OpenAI API key not set.")


    log(f"Calling OpenAI ({model})…")
    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt_text},
            {"role": "user",   "content": json.dumps(payload, ensure_ascii=False, indent=2, default=str)},
        ],
    )
    return (resp.choices[0].message.content or "").strip()


# =============================================================================
# ── PROVIDER CONTACTS ─────────────────────────────────────────────────────────
# =============================================================================


class ProviderContacts:
    def __init__(self, path: str):
        self.path = path
        self.data: Dict[str, Any] = {"contacts": []}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                pass


    def save(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)


    def _norm(self, s: str) -> str:
        return re.sub(r"\s+", " ", (s or "").lower().strip())


    def find(self, provider: str) -> Optional[Dict[str, Any]]:
        needle = self._norm(provider)
        if not needle: return None
        for c in self.data.get("contacts", []):
            keys = [c.get("key", "")] + (c.get("aliases") or [])
            norms = [self._norm(k) for k in keys if k]
            if any(k == needle or (k and (k in needle or needle in k)) for k in norms):
                return c
        return None


    def get_emails(self, provider: str) -> Tuple[List[str], List[str]]:
        c = self.find(provider)
        if not c: return [], []
        return (c.get("emails") or []), (c.get("cc") or [])


    def get_fax(self, provider: str) -> str:
        c = self.find(provider)
        return (c or {}).get("fax", "")


    def upsert_email(self, key: str, email: str, cc: List[str] = []):
        c = self.find(key)
        if c is None:
            c = {"key": key, "aliases": [key], "emails": [email], "cc": cc, "fax": ""}
            self.data["contacts"].append(c)
        else:
            emails = c.get("emails") or []
            if email not in emails: emails.append(email)
            c["emails"] = emails
            existing_cc = c.get("cc") or []
            for x in cc:
                if x and x not in existing_cc: existing_cc.append(x)
            c["cc"] = existing_cc
        self.save()


    def upsert_fax(self, key: str, fax: str):
        fax = digits_only(fax)
        if not fax: return
        c = self.find(key)
        if c is None:
            self.data["contacts"].append({"key": key, "aliases": [key], "emails": [], "cc": [], "fax": fax})
        else:
            c["fax"] = fax
        self.save()


    def contact_has_alias(self, c: Dict, alias: str) -> bool:
        needle = self._norm(alias)
        if not needle: return True
        keys = [c.get("key", "")] + (c.get("aliases") or [])
        return any(self._norm(k) == needle for k in keys if k)


    def add_alias(self, c: Dict, alias: str) -> bool:
        if not alias or self._norm(alias) in [self._norm(k) for k in ([c.get("key","")] + (c.get("aliases") or []))]:
            return False
        aliases = c.get("aliases") or []
        aliases.append(alias)
        c["aliases"] = aliases
        self.save()
        return True


# =============================================================================
# ── PDF HELPERS (Report Sender) ───────────────────────────────────────────────
# =============================================================================


def read_pdf_first_pages(pdf_path: str, max_pages: int = 2) -> str:
    if PdfReader is None: return ""
    try:
        reader = PdfReader(pdf_path)
        texts = []
        for i in range(min(max_pages, len(reader.pages))):
            try: texts.append(reader.pages[i].extract_text() or "")
            except Exception: pass
        return "\n".join(texts)
    except Exception:
        return ""


def extract_referred_by_from_pdf(pdf_path: str) -> str:
    text = normalize_newlines(read_pdf_first_pages(pdf_path, 2))
    text = "\n".join(re.sub(r"[ \t]+", " ", ln) for ln in text.split("\n"))
    m = re.search(r"(?im)^\s*Referred By\s*:\s*(.*)\s*$", text)
    if m and m.group(1).strip():
        return m.group(1).strip()
    lines = [ln.strip() for ln in text.split("\n")]
    for i, ln in enumerate(lines):
        if ln.lower() in {"referred by:", "referred by"}:
            for j in range(i + 1, min(i + 10, len(lines))):
                if lines[j]: return lines[j].strip()
    return ""


def find_report_pdf(patients_root: str, patient_name: str) -> Tuple[Optional[str], str]:
    """Find the patient's PDF report by LastFirst key."""
    s = (patient_name or "").strip()
    if not s: return None, "Empty patient name."
    if "," in s:
        parts = [p.strip() for p in s.split(",") if p.strip()]
        last  = parts[0].split()[0] if parts else ""
        first = parts[1].split()[0] if len(parts) > 1 else ""
    else:
        parts = s.split()
        first = parts[0]  if parts else ""
        last  = parts[-1] if parts else ""
    key = re.sub(r"[^A-Za-z0-9]", "", last + first)
    if not key: return None, "Could not infer key from patient name."
    if not os.path.isdir(patients_root):
        return None, f"patients_root not found: {patients_root}"


    def newest(folder: str) -> Optional[str]:
        hits = glob.glob(os.path.join(folder, f"{key}*.pdf")) or \
               glob.glob(os.path.join(folder, "*.pdf"))
        if hits:
            hits.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return hits[0]
        return None


    direct = os.path.join(patients_root, key)
    dirs = [direct] if os.path.isdir(direct) else []
    if not dirs:
        try:
            dirs = [os.path.join(patients_root, d)
                    for d in os.listdir(patients_root)
                    if os.path.isdir(os.path.join(patients_root, d)) and d.lower().startswith(key.lower())]
        except Exception:
            pass
    for d in dirs:
        p = newest(d)
        if p: return p, ""


    # walk
    found: List[str] = []
    for root, _, files in os.walk(patients_root):
        for fn in files:
            if fn.lower().endswith(".pdf") and fn.lower().startswith(key.lower()):
                found.append(os.path.join(root, fn))
    if found:
        found.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return found[0], ""
    return None, f"No PDF found matching '{key}*.pdf' under {patients_root}"


# =============================================================================
# ── NPI LOOKUP ────────────────────────────────────────────────────────────────
# =============================================================================


def lookup_fax_npi(provider_text: str, log: Callable = print) -> List[Dict[str, str]]:
    if requests is None: return []
    q = (provider_text or "").strip()
    if not q: return []
    url = "https://npiregistry.cms.hhs.gov/api/"
    results: List[Dict[str, str]] = []


    def _parse(data: Dict) -> None:
        for item in (data.get("results") or []):
            basic = item.get("basic") or {}
            name = (basic.get("organization_name") or
                    f"{basic.get('first_name','')} {basic.get('last_name','')}".strip())
            for a in (item.get("addresses") or []):
                fax = digits_only(a.get("fax_number") or "")
                if fax and len(fax) >= 10:
                    addr = ", ".join(x for x in [a.get("address_1"), a.get("city"),
                                                  a.get("state"), a.get("postal_code")] if x)
                    results.append({"fax": fax, "name": name, "address": addr})


    try:
        r = requests.get(url, params={"version": "2.1", "organization_name": q, "limit": 20},
                         timeout=(4, 10))
        if r.ok: _parse(r.json())
    except Exception: pass
    if not results:
        try:
            parts = q.split()
            if len(parts) >= 2:
                r = requests.get(url, params={"version": "2.1", "first_name": parts[0],
                                              "last_name": parts[-1], "limit": 20},
                                 timeout=(4, 10))
                if r.ok: _parse(r.json())
        except Exception: pass
    return results


# =============================================================================
# ── ICD-10 LOADER ─────────────────────────────────────────────────────────────
# =============================================================================


ICD_FAVORITES = [
    "F90.2 - ADHD, combined presentation",
    "F90.0 - ADHD, predominantly inattentive presentation",
    "F41.1 - Generalized anxiety disorder",
    "F33.1 - Major depressive disorder, recurrent, moderate",
    "F33.2 - Major depressive disorder, recurrent, severe",
    "F31.13 - Bipolar Disorder, Type I",
    "G31.9 - Major Neurocognitive Disorder",
    "F60.5 - Obsessive Compulsive Personality Disorder",
    "F43.10 - PTSD",
    "F84.0 - Autism Spectrum Disorder",
    "F60.3 - Borderline Personality Disorder",
]


def load_icd_codes(log: Callable = print) -> List[str]:
    cache = _resolve_icd_cache_path()
    if os.path.exists(cache):
        try:
            with open(cache, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                return data
        except Exception: pass
    return ICD_FAVORITES


# =============================================================================
# ── TEST CHECKER HELPERS ──────────────────────────────────────────────────────
# =============================================================================


def normalize_text_tc(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower().strip())


def word_overlap(a: str, b: str) -> float:
    wa = set(normalize_text_tc(a).split())
    wb = set(normalize_text_tc(b).split())
    if not wa or not wb: return 0.0
    return len(wa & wb) / min(len(wa), len(wb))


def detect_appointment_type(summary: str, description: str, apt_types: Dict[str, Any]) -> Tuple[Optional[str], str]:
    """
    Extract the patient's appointment type answer from the calendar description
    and fuzzy-match it against the configured appointment type names.


    Returns (matched_type_or_None, candidate_text).


    The booking form structure is:
        Appointment Type: Enter one choice: (Choice A, Choice B, ...)
        Patient typed answer here
        You are scheduling...


    Google Calendar delivers descriptions as HTML — tags are stripped before
    any parsing takes place.


    Matching strategy (in order):
    1. Strip HTML from description (Google Calendar returns HTML).
    2. Extract text after closing ')' of the choices list (first non-empty line).
    3. Score that candidate against every configured type key using word overlap.
    4. Apply semantic aliases for common free-text variants.
    5. Return None if best score < 0.40 so the UI shows "Undetermined".
    """
    if not apt_types:
        return None, ""


    # ── Step 1: strip HTML — Google Calendar returns HTML-formatted descriptions ──
    desc = html_to_text(description or "")
    candidate_text = ""


    # ── Step 2: locate "Appointment Type:" and extract patient answer ────────
    m_label = re.search(r"Appointment\s+Type\s*[:\s]", desc, re.IGNORECASE)
    if m_label:
        after_label = desc[m_label.end():]
        paren_close = after_label.find(")")
        if paren_close != -1:
            raw = after_label[paren_close + 1 : paren_close + 161]
            for segment in re.split(r'[\r\n]+|__', raw):
                segment = segment.strip()
                if len(segment) >= 2:
                    candidate_text = segment
                    break


    # Fallback: use summary + full description
    if not candidate_text:
        candidate_text = f"{summary} {desc}"


    cand_lower = candidate_text.lower()


    # ── Step 3: semantic alias pre-screening ─────────────────────────────────
    def _best_key_containing(substring: str) -> Optional[str]:
        """Return the apt_types key whose name contains `substring` (case-insensitive)."""
        matches = [k for k in apt_types if substring.lower() in k.lower()]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            return min(matches, key=len)
        return None


    # "ADHD" alone, or "unsure about adhd" / "adult adhd" etc.
    # -> prefer "Adult with ADHD" if present, else any key containing "ADHD"
    if re.search(r"\badhd\b", cand_lower):
        if "no adhd" not in cand_lower and "without adhd" not in cand_lower:
            k = _best_key_containing("with ADHD") or _best_key_containing("ADHD")
            if k:
                return k, candidate_text


    # "no adhd" / "without adhd" -> Adult no ADHD
    if re.search(r"no\s+adhd|without\s+adhd", cand_lower):
        k = _best_key_containing("no ADHD")
        if k:
            return k, candidate_text


    # ── Step 4: word-overlap fuzzy scoring ──────────────────────────────────
    best_type, best_score = None, 0.0
    for atype in apt_types:
        score = word_overlap(candidate_text, atype)
        if score > best_score:
            best_score = score
            best_type  = atype


    THRESHOLD = 0.40
    return (best_type if best_score >= THRESHOLD else None), candidate_text




def check_patient_in_sheet(gspread_client, sheet_id: str, patient_email: str,
                            log: Callable = print,
                            worksheet_name: str = "Form Responses 1") -> bool:
    try:
        sh = call_with_retry(gspread_client.open_by_key, sheet_id, log=log)
        try:
            ws = sh.worksheet(worksheet_name)
        except Exception:
            ws = sh.get_worksheet(0)
        vals = call_with_retry(ws.col_values, 2, log=log)
        target = normalize_email(patient_email)
        return any(normalize_email(v) == target for v in vals)
    except Exception as e:
        log(f"  Sheet check error ({sheet_id}): {e}")
        return False




def check_patient_in_sheet_with_fallback(
    gspread_client, sheet_id: str, patient_email: str,
    patient_name: str = "",
    log: Callable = print,
    worksheet_name: str = "Form Responses 1",
    email_col: int = 2,
    name_col: int = 3,
) -> bool:
    """
    Check for patient by email first; if no email match found, fall back to
    name matching using liberal_fullname_match (same logic as Test Transfer).
    """
    try:
        sh = call_with_retry(gspread_client.open_by_key, sheet_id, log=log)
        try:
            ws = sh.worksheet(worksheet_name)
        except Exception:
            ws = sh.get_worksheet(0)


        # Email match
        if patient_email:
            email_vals = call_with_retry(ws.col_values, email_col, log=log)
            target = normalize_email(patient_email)
            if any(normalize_email(v) == target for v in email_vals):
                return True
            log(f"    (no email match — trying name fallback)")


        # Name fallback
        if patient_name:
            try:
                all_rows = call_with_retry(ws.get_all_values, log=log)
                for row in all_rows[1:]:
                    row_name = row[name_col - 1] if len(row) >= name_col else ""
                    if not row_name:
                        continue
                    first, last = _split_name(row_name)
                    if liberal_fullname_match(patient_name, first, last, row_name):
                        log(f"    ✅ Matched by name: {row_name!r}")
                        return True
            except Exception as e:
                log(f"    Name fallback error: {e}")


        return False
    except Exception as e:
        log(f"  Sheet check error ({sheet_id}): {e}")
        return False


def get_meet_link_from_event(event: Dict) -> Optional[str]:
    link = event.get("hangoutLink")
    if link and "meet.google.com" in link:
        return link.strip()
    conf = event.get("conferenceData") or {}
    for ep in conf.get("entryPoints", []):
        uri = ep.get("uri", "")
        if "meet.google.com" in uri:
            return uri.strip()
    desc = event.get("description") or ""
    m = re.search(r"https://meet\.google\.com/\S+", desc)
    if m:
        return m.group(0).strip()
    return None


def clean_name_for_greeting(raw: str) -> str:
    if not raw: return "Patient"
    s = str(raw).strip()
    m = re.search(r"\(([^)]+)\)", s)
    if m and m.group(1).strip(): return m.group(1).strip()
    return s


def format_appt_for_email(start_str: str) -> str:
    if not start_str: return ""
    try:
        d = dt.datetime.fromisoformat(start_str)
        local = d.astimezone()
        return local.strftime("%m-%d-%Y") + " at " + local.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return start_str


def send_missing_tests_email_tc(smtp_conf: Dict, to_email: str, patient_name: str,
                                 missing_tests: List[str], appt_start: str = "",
                                 meet_link: str = "", log: Callable = print) -> bool:
    greeting = clean_name_for_greeting(patient_name)
    pretty   = format_appt_for_email(appt_start)
    subject  = "Reminder: Please complete your pre-appointment questionnaires"
    lines = [f"Dear {greeting},", ""]
    if pretty:
        lines += [f"Your upcoming appointment is scheduled for {pretty}.", ""]
    else:
        lines += ["You have an upcoming appointment.", ""]
    lines += ["Our records show that the following forms/tests are still outstanding:", ""]
    for t in missing_tests:
        lines.append(f"  \u2022 {t}")
    lines += [
        "",
        "You can access and complete these forms/tests at:",
        "  www.psyscreen.com",
        "using the password:",
        "  poiuytrewq0987",
        "",
        "Your evaluation will be conducted by telemedicine using Google Meet.",
    ]
    if meet_link:
        lines += ["", "You can join your telemedicine session using this link:", f"  {meet_link}"]
    else:
        lines += ["", "Your Google Meet link is included in your appointment confirmation from Google Calendar."]
    lines += [
        "",
        "Please complete these forms at your earliest convenience so that your evaluation can be as thorough and efficient as possible.",
        "",
        "If you believe you received this message in error, feel free to ignore it or contact our office.",
        "",
        "Thank you,",
        smtp_conf.get("from_name", "Noll Psych Group"),
    ]
    return send_smtp(smtp_conf, [to_email], subject, "\n".join(lines), log=log)


def send_appointment_reminder_email_tc(smtp_conf: Dict, to_email: str, patient_name: str,
                                        appt_start: str, meet_link: str = "",
                                        include_insurance: bool = False,
                                        log: Callable = print) -> bool:
    greeting = clean_name_for_greeting(patient_name)
    pretty   = format_appt_for_email(appt_start)
    subject  = "Appointment Reminder \u2013 Noll Psych Group"
    lines = [f"Dear {greeting},", ""]
    if pretty:
        lines.append(f"This is a reminder of your upcoming appointment on {pretty}.")
    else:
        lines.append("This is a reminder of your upcoming appointment.")
    lines += ["", "This appointment will be conducted by telemedicine using Google Meet."]
    if meet_link:
        lines += ["", "You can join your session using this link:", f"  {meet_link}"]
    lines += [
        "",
        "Please complete all required forms and tests prior to your evaluation by visiting:",
        "  www.psyscreen.com",
        "and entering the password:",
        "  poiuytrewq0987",
        "",
        "If you have questions or need to reschedule, please text 816-835-9882.",
        "Please do not reply to this email for scheduling or other inquiries, as this mailbox is not monitored for clinical communication.",
    ]
    if include_insurance:
        lines += [
            "",
            "About insurance",
            "",
            "If using insurance, your cost will depend on whether the service is a covered benefit under your policy, "
            "and whether you have a copayment that you will owe or a deductible to meet. This is specific to the policy "
            "that you have purchased. If you have questions we suggest you contact your insurance company to ask them about "
            "the specifics of your coverage.",
            "",
            "We will use the following CPT codes:",
            "  \u2022 90791 \u2013 initial interview",
            "  \u2022 96132 \u2013 first unit of neuropsychological testing",
            "  \u2022 96133 \u2013 additional units of neuropsychological testing.",
            "",
            "We will use 1 unit of 90791, 1 unit of 96132, and 6 units of 96133.",
            "We will charge $165 for the 90791, $150 for the initial unit of 96132, "
            "and $100 for each additional unit of 96133.",
            "Insurance will pay whatever they allow based on our network agreement.",
            "",
            "Following the appointment you will be informed about what you may owe by the explanation of benefits (EOB) "
            "form that you receive from your insurance company.",
            "If you end up owing based on your insurance coverage, when you get your insurance EOB you have the option of "
            "texting us to set up a payment plan.",
            "After receiving the EOB from insurance we will charge the balance due to your card.",
            "By requesting an appointment, you are agreeing to our policies.",
        ]
    lines += ["", "Thank you,", smtp_conf.get("from_name", "Noll Psych Group")]
    return send_smtp(smtp_conf, [to_email], subject, "\n".join(lines), log=log)


def extract_patient_email_tc(event: Dict, owner_email: str) -> Optional[str]:
    return extract_patient_email_from_event(event, owner_email)


def extract_patient_name_tc(event: Dict, email: str, owner_email: str) -> str:
    summary = event.get("summary") or ""
    for part in re.split(r"[,\-\|]", summary):
        part = part.strip()
        if part and part.lower() not in normalize_email(owner_email) and "@" not in part:
            return part
    name = infer_patient_name_from_event(event)
    if name != "(unknown)": return name
    return email.split("@")[0].replace(".", " ").replace("_", " ").title()


def get_events_range(cal_service, calendar_id: str, start_str: str, end_str: str) -> List[Dict]:
    start_date = dt.datetime.fromisoformat(start_str).date()
    end_date   = dt.datetime.fromisoformat(end_str).date()
    return fetch_calendar_events(cal_service, calendar_id, start_date, end_date, "America/Chicago")


# =============================================================================
# ── INSURANCE FORM HELPER ─────────────────────────────────────────────────────
# =============================================================================


def fetch_insurance_row(gspread_client, ins_conf: Dict[str, Any], patient_email: str, log: Callable) -> Dict[str, str]:
    sheet_id  = ins_conf.get("google_sheet_id") or ins_conf.get("sheet_id", "")
    ws_name   = ins_conf.get("worksheet") or "Form Responses 1"
    email_col = int(ins_conf.get("email_column_index", 2))


    sh = call_with_retry(gspread_client.open_by_key, sheet_id, log=log)
    ws = call_with_retry(sh.worksheet, ws_name, log=log)
    headers   = call_with_retry(ws.row_values, 1, log=log)
    email_vals = call_with_retry(ws.col_values, email_col, log=log)
    target    = normalize_email(patient_email)


    match_row = None
    for idx, v in enumerate(email_vals[1:], start=2):
        if normalize_email(v) == target:
            match_row = idx; break
    if match_row is None:
        for idx, v in enumerate(email_vals[1:], start=2):
            if target and target in normalize_email(v):
                match_row = idx; break
    if match_row is None:
        raise LookupError(f"No insurance-form row for: {patient_email}")


    row = call_with_retry(ws.row_values, match_row, log=log)
    row += [""] * max(0, len(headers) - len(row))
    return {headers[i].strip(): (row[i] if i < len(row) else "") for i in range(len(headers))}


def format_insurance_block(row_dict: Dict[str, str]) -> str:
    excl_fragments = [
        "after my insurance has been filed",
        "i am consenting to",
        "consent", "payment", "signature",
    ]
    lines = []
    for k, v in row_dict.items():
        key = (k or "").strip()
        val = (v or "").strip()
        if not key or not val: continue
        key_norm = key.lower()
        if any(f in key_norm for f in excl_fragments): continue
        lines.append(f"{key}: {val}")
    return "\n".join(lines)


# =============================================================================
# ── DRIVE TRANSCRIPT HELPER ───────────────────────────────────────────────────
# =============================================================================


def download_transcripts_from_drive(drive_service, folder_id: str, patient_name: str,
                                     dest_folder: str, log: Callable = print,
                                     appt_date: Optional[dt.date] = None) -> List[str]:
    """
    Exact port of test_transfer_app_s.py download_transcripts_from_drive_folder,
    plus optional date filtering using the calendar appointment date.
    """
    import io
    try:
        from googleapiclient.http import MediaIoBaseDownload
    except ImportError:
        log("  ❌ googleapiclient.http not available")
        return []


    ext_set = {".docx", ".doc", ".txt", ".rtf", ".pdf"}
    patient_lower = patient_name.lower()


    def _sanitize(name: str) -> str:
        base, ext = os.path.splitext(name)
        base = re.sub(r'[<>:"/\\|?*]', "_", base).strip() or "file"
        return base + ext


    def _date_ok(modified_time_str: str) -> bool:
        if not appt_date or not modified_time_str:
            return True
        try:
            mt = dt.datetime.fromisoformat(modified_time_str.replace("Z", "+00:00"))
            delta = abs((mt.date() - appt_date).days)
            return delta <= 1
        except Exception:
            return True


    fields = "nextPageToken, files(id, name, mimeType, modifiedTime)"


    log(f"  Drive folder: {folder_id}")
    log(f"  Searching for files containing: {patient_lower!r}")
    if appt_date:
        log(f"  Date filter: within 1 day of {appt_date} (appointment date)")


    downloaded: List[str] = []
    page_token = None
    total_seen = 0


    while True:
        list_kwargs: Dict[str, Any] = dict(
            q=f"'{folder_id}' in parents and trashed = false",
            spaces="drive",
            fields=fields,
            pageSize=200,
        )
        if page_token:
            list_kwargs["pageToken"] = page_token


        try:
            response = drive_service.files().list(**list_kwargs).execute()
        except Exception as e:
            log(f"  ❌ Drive list failed: {e}")
            log(f"  {traceback.format_exc()}")
            break


        files = response.get("files", [])
        total_seen += len(files)


        for file in files:
            name          = file.get("name", "")
            mime_type     = file.get("mimeType", "")
            file_id       = file.get("id", "")
            modified_time = file.get("modifiedTime", "")


            if patient_lower not in name.lower():
                continue


            if not _date_ok(modified_time):
                log(f"  Skipped (date mismatch {modified_time[:10]}): {name}")
                continue


            log(f"  Match: {name!r} modified={modified_time[:10] if modified_time else '?'}")


            if mime_type == "application/vnd.google-apps.document":
                candidate_name = name if name.lower().endswith(".docx") else name + ".docx"
                safe_name = _sanitize(candidate_name)
                request = drive_service.files().export_media(
                    fileId=file_id,
                    mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            else:
                _, ext = os.path.splitext(name)
                if ext.lower() not in ext_set:
                    log(f"    Skipped (extension {ext!r} not in allowed set)")
                    continue
                safe_name = _sanitize(name)
                request = drive_service.files().get_media(fileId=file_id)


            dest_path = os.path.join(dest_folder, safe_name)
            base_n, ext2 = os.path.splitext(safe_name)
            counter = 1
            while os.path.exists(dest_path):
                dest_path = os.path.join(dest_folder, f"{base_n} ({counter}){ext2}")
                counter += 1


            try:
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                with open(dest_path, "wb") as f:
                    f.write(fh.getvalue())
                log(f"  ✅ Downloaded: {os.path.basename(dest_path)}")
                downloaded.append(dest_path)
            except Exception as e:
                log(f"  ❌ Download failed for {name!r}: {e}")
                log(f"  {traceback.format_exc()}")


        page_token = response.get("nextPageToken")
        if not page_token:
            break


    log(f"  Scanned {total_seen} file(s) in Drive folder — {len(downloaded)} downloaded.")
    return downloaded


# =============================================================================
# ── LETTER PDF GENERATOR ──────────────────────────────────────────────────────
# =============================================================================


def generate_letter_pdf(
    out_path: str,
    letter_text: str,
    date_str: str = "",
) -> str:
    """
    Render letter_text as an NPG-letterhead letter PDF.
    Same letterhead / signature block as generate_report_pdf.
    letter_text should be plain text starting AFTER the date line
    (i.e. salutation through body; do NOT include date/logo/address — those
    come from the letterhead canvas callback).
    Returns out_path on success, raises on failure.
    """
    if not REPORTLAB_OK:
        raise RuntimeError("reportlab is not installed.")


    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    BF = _BODY_FONT


    # Paragraph styles
    N  = ParagraphStyle("LT_N",  fontName=BF, fontSize=12, leading=16,
                        spaceAfter=12, spaceBefore=0)
    BL = ParagraphStyle("LT_BL", fontName=BF, fontSize=12, leading=14,
                        spaceAfter=0,  spaceBefore=0)   # signature block lines


    doc = BaseDocTemplate(
        out_path, pagesize=letter,
        leftMargin=_RE_L, rightMargin=_RE_R,
        topMargin=_RE_T + _RE_LH_H,
        bottomMargin=_RE_B + 0.25 * inch,
    )
    doc._re_hdr = ""
    doc._re_dob = ""


    frame_first = Frame(
        _RE_L, _RE_B + 0.25 * inch, _RE_W - _RE_L - _RE_R,
        _RE_H - _RE_T - _RE_LH_H - _RE_B - 0.25 * inch, id="first")
    doc.addPageTemplates([
        PageTemplate(id="First", frames=[frame_first], onPage=_re_draw_first_page),
    ])


    story: List = [Spacer(1, 6)]


    # Date line
    if date_str:
        story.append(Paragraph(_re_sanitize(date_str), N))
        story.append(Spacer(1, 4))


    # Parse letter body: split on double-newlines for paragraphs
    paragraphs = re.split(r"\n{2,}", normalize_newlines(letter_text).strip())
    in_sig_block = False
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Detect signature block start (Sincerely / Regards / etc.)
        if re.match(r"^(Sincerely|Regards|Respectfully|Best regards|Thank you)[,.]?\s*$",
                    para, re.I):
            in_sig_block = True
            story.append(Paragraph(_re_sanitize(para), N))
            story.append(Spacer(1, 48))   # space for handwritten signature
            continue
        if in_sig_block:
            story.append(Paragraph(_re_sanitize(para), BL))
        else:
            story.append(Paragraph(_re_sanitize(para), N))


    doc.build(story)
    return out_path




# =============================================================================
# ── PATIENT FOLDER HELPER ─────────────────────────────────────────────────────
# =============================================================================


def _strip_noll_psych_group(name: str) -> str:
    """
    If the name contains a parenthetical — e.g. 'Noll Psych Group (Jane Smith)' —
    extract only the content inside the parentheses.
    This mirrors infer_patient_name_from_event in test_transfer_app_s.
    """
    name = (name or "").strip()
    m = re.search(r"\(([^)]+)\)", name)
    if m:
        return m.group(1).strip()
    return name


def ensure_patient_folder(patients_root: str, patient_name: str) -> str:
    clean = _strip_noll_psych_group(patient_name)
    folder = os.path.join(patients_root, clean)
    os.makedirs(folder, exist_ok=True)
    return folder


# =============================================================================
# ══════════════════════════════════════════════════════════════════════════════
# ── MAIN APPLICATION ──────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
# =============================================================================


# =============================================================================
# ── REPORT EDITOR PDF GENERATOR ───────────────────────────────────────────────
# =============================================================================


_RE_W, _RE_H = letter           # 612 × 792 pt
_RE_L = 1.00 * inch
_RE_R = 1.00 * inch
_RE_T = 0.75 * inch
_RE_B = 0.75 * inch


# Letterhead dimensions
_RE_LOGO_W  = 1.10 * inch
_RE_LOGO_H  = 0.72 * inch
_RE_ADDR_H  = 0.55 * inch      # 4 address lines × 10 pt + small gap
_RE_LH_H    = _RE_LOGO_H + _RE_ADDR_H + 0.10 * inch   # total letterhead on p1
_RE_LATER_T = 0.38 * inch      # running-header height on pages 2+


_RE_ADDR_LINES = [
    "186 B Highway 92",
    "Kearney, MO 64060",
    "Phone: (816) 835-9882",
    "Fax: (866) 601-2313",
]


# ── Register Arial via Liberation Sans (metrically identical) ─────────────────
_LIBERATION_DIR = "/usr/share/fonts/truetype/liberation"


def _register_arial() -> bool:
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.pdfbase.pdfmetrics import registerFontFamily
        pairs = [
            ("Arial",            "LiberationSans-Regular.ttf"),
            ("Arial-Bold",       "LiberationSans-Bold.ttf"),
            ("Arial-Italic",     "LiberationSans-Italic.ttf"),
            ("Arial-BoldItalic", "LiberationSans-BoldItalic.ttf"),
        ]
        for rl_name, fname in pairs:
            p = os.path.join(_LIBERATION_DIR, fname)
            if not os.path.exists(p):
                return False
            pdfmetrics.registerFont(TTFont(rl_name, p))
        registerFontFamily("Arial", normal="Arial", bold="Arial-Bold",
                           italic="Arial-Italic", boldItalic="Arial-BoldItalic")
        return True
    except Exception:
        return False


_ARIAL_REGISTERED = _register_arial()
_BODY_FONT = "Arial"      if _ARIAL_REGISTERED else "Helvetica"




def _re_sanitize(text: str) -> str:
    """Replace encoding artifacts and XML-escape."""
    text = text or ""
    for a, b in [('\u2019',"'"), ('\u2018',"'"), ('\u201c','"'), ('\u201d','"'),
                 ('\u2014','-'), ('\u2013','-'), ('\u2011','-'), ('\u00a0',' ')]:
        text = text.replace(a, b)
    text = re.sub(r'[\u25a0-\u25ff]', '-', text)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return text




def _re_dob_fmt(dob: str) -> str:
    """Normalise any DOB string to MM/DD/YYYY."""
    dob = (dob or "").strip()
    if re.match(r'\d{1,2}/\d{1,2}/\d{4}', dob):
        p = dob.split('/')
        return f"{int(p[0]):02d}/{int(p[1]):02d}/{p[2]}"
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', dob)
    if m:
        return f"{m.group(2)}/{m.group(3)}/{m.group(1)}"
    import datetime as _dt
    for fmt in ('%B %d %Y', '%B %d, %Y', '%b %d %Y', '%b %d, %Y',
                '%B %-d %Y', '%B %-d, %Y'):
        try:
            return _dt.datetime.strptime(dob, fmt).strftime('%m/%d/%Y')
        except Exception:
            pass
    return dob




def _re_patient_filename(patient_name: str) -> str:
    """'First Last' → 'LastFirst' — no spaces, no special chars."""
    name = (patient_name or "").strip()
    if ',' in name:
        parts = [p.strip() for p in name.split(',', 1)]
        last, first = parts[0], parts[1]
    else:
        parts = name.split()
        last  = parts[-1] if parts else name
        first = ' '.join(parts[:-1]) if len(parts) > 1 else ''
    return re.sub(r'[^A-Za-z0-9]', '', last + first)




def _re_strip_practice(val: str) -> str:
    """Remove parenthetical practice names: keep names/credentials only."""
    return re.sub(r'\s*\([^)]*\)', '', val or '').strip()




# Known section headings (normalised, without colon)
_RE_HEADINGS = {
    "identifying information and referral question",
    "history and background information",
    "mental status examination",
    "tests administered",
    "neurosychological/personality test results",
    "neuropsychological/personality test results",
    "neurosychological / personality test results",
    "diagnostic impression",
    "conclusions/recommendations",
    "conclusions / recommendations",
    "mpaci",
}




def _re_is_heading(line: str) -> bool:
    return line.strip().rstrip(':').strip().lower() in _RE_HEADINGS




def _re_ensure_colon(line: str) -> str:
    line = line.strip()
    return line if line.endswith(':') else line + ':'




def _re_draw_first_page(canvas, doc):
    """Page 1: logo at left margin, address centred under logo, page number bottom-right."""
    canvas.saveState()
    logo_top    = _RE_H - _RE_T
    logo_bottom = logo_top - _RE_LOGO_H
    logo_path   = _re_asset(_RE_LOGO_PRIMARY, _RE_LOGO_FALLBACK)
    if os.path.exists(logo_path):
        canvas.drawImage(logo_path, _RE_L, logo_bottom,
                         width=_RE_LOGO_W, height=_RE_LOGO_H,
                         preserveAspectRatio=True, mask="auto")
    # Address centred under the logo (within the logo's horizontal span),
    # lines packed tight at 8pt leading (zero space between lines)
    canvas.setFont(_BODY_FONT, 8)
    y = logo_bottom - 9          # 1 pt gap then immediately into first line
    for line in _RE_ADDR_LINES:
        w = canvas.stringWidth(line, _BODY_FONT, 8)
        # Centre within logo width: left edge = _RE_L, span = _RE_LOGO_W
        x = _RE_L + (_RE_LOGO_W - w) / 2
        canvas.drawString(x, y, line)
        y -= 8                   # 8pt = font size → zero inter-line space
    canvas.drawRightString(_RE_W - _RE_R, _RE_B - 0.15 * inch, str(doc.page))
    canvas.restoreState()




def _re_draw_later_pages(canvas, doc):
    """Pages 2+: 'Last, First' left, 'DOB: MM/DD/YYYY' right — Arial 8."""
    canvas.saveState()
    canvas.setFont(_BODY_FONT, 8)
    canvas.drawString(_RE_L, _RE_H - 0.35 * inch, getattr(doc, "_re_hdr", ""))
    canvas.drawRightString(_RE_W - _RE_R, _RE_H - 0.35 * inch,
                           f"DOB: {getattr(doc, '_re_dob', '')}")
    canvas.drawRightString(_RE_W - _RE_R, _RE_B - 0.15 * inch, str(doc.page))
    canvas.restoreState()




def generate_report_pdf(
    out_path: str,
    report_text: str,
    patient_name: str,
    dob: str,
    referred_by: str = "",
    age: str = "",
    eval_date: str = "",
) -> str:
    """
    Render report_text (clean plain-text from the Report Editor) as a
    formatted NPG evaluation PDF and save to out_path.
    """
    if not REPORTLAB_OK:
        raise RuntimeError("reportlab is not installed.")


    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)


    pname  = (patient_name or "").strip()
    pts    = pname.split()
    hdr_last  = pts[-1] if pts else pname
    hdr_first = ' '.join(pts[:-1]) if len(pts) > 1 else ''
    header_name = f"{hdr_last}, {hdr_first}" if hdr_first else pname
    dob_formatted = _re_dob_fmt(dob)
    ref_display   = _re_strip_practice(referred_by)


    # ── Styles ────────────────────────────────────────────────────────────────
    BF = _BODY_FONT
    # Body paragraphs: Arial 12, single-spaced, one-line gap between paragraphs
    N  = ParagraphStyle("RE_N",  fontName=BF, fontSize=12, leading=14,
                        spaceAfter=14, spaceBefore=0)
    # Numbered list items (diagnoses): no gap between entries, but space after the last one
    NL = ParagraphStyle("RE_NL", fontName=BF, fontSize=12, leading=14,
                        spaceAfter=0, spaceBefore=0)
    # Last item in a numbered list: adds a paragraph gap after the list ends
    NL_LAST = ParagraphStyle("RE_NL_LAST", fontName=BF, fontSize=12, leading=14,
                             spaceAfter=14, spaceBefore=0)
    # Section headings: Arial 12, NOT bold, space above and below
    SH = ParagraphStyle("RE_SH", fontName=BF, fontSize=12, leading=14,
                        spaceAfter=14, spaceBefore=14)
    # Title: NOT bold, centred
    TI = ParagraphStyle("RE_TI", fontName=BF, fontSize=12, leading=14,
                        alignment=TA_CENTER, spaceAfter=0)
    # Demographic table cells: no bold, no spacing between rows
    DM = ParagraphStyle("RE_DM", fontName=BF, fontSize=12, leading=14,
                        spaceAfter=0, spaceBefore=0)
    # Signature block: no gap between lines
    SG = ParagraphStyle("RE_SG", fontName=BF, fontSize=12, leading=14,
                        spaceAfter=0, spaceBefore=0)


    # ── Document ──────────────────────────────────────────────────────────────
    doc = BaseDocTemplate(
        out_path, pagesize=letter,
        leftMargin=_RE_L, rightMargin=_RE_R,
        topMargin=_RE_T + _RE_LH_H,
        bottomMargin=_RE_B + 0.25 * inch,
    )
    doc._re_hdr = header_name
    doc._re_dob = dob_formatted


    frame_first = Frame(
        _RE_L, _RE_B + 0.25 * inch, _RE_W - _RE_L - _RE_R,
        _RE_H - _RE_T - _RE_LH_H - _RE_B - 0.25 * inch, id="first")
    frame_later = Frame(
        _RE_L, _RE_B + 0.25 * inch, _RE_W - _RE_L - _RE_R,
        _RE_H - _RE_LATER_T - 0.25 * inch - _RE_B - 0.25 * inch, id="later")
    doc.addPageTemplates([
        PageTemplate(id="First", frames=[frame_first], onPage=_re_draw_first_page),
        PageTemplate(id="Later", frames=[frame_later], onPage=_re_draw_later_pages),
    ])


    # ── Story: title + demographics ───────────────────────────────────────────
    story: List = [
        Spacer(1, 28),                                           # two lines above title
        Paragraph("NEUROPSYCHOLOGICAL EVALUATION", TI),          # not bold
        Spacer(1, 28),                                           # two lines below title
    ]


    info_rows = [
        ("Patient Name:",      pname),
        ("Referred by:",       ref_display),
        ("Date of Birth:",     dob_formatted),
        ("Date of Evaluation:", eval_date),
    ]
    td = [
        [Paragraph(_re_sanitize(k), DM), Paragraph(_re_sanitize(v), DM)]
        for k, v in info_rows if v.strip()
    ]
    if td:
        it = Table(td, colWidths=[1.65 * inch, 4.5 * inch])
        it.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(it)
    story.append(NextPageTemplate("Later"))


    # ── Parse body ────────────────────────────────────────────────────────────
    # Strip the leading metadata block the LLM emits at the top of the text
    _meta_keys = {
        "neuropsychological evaluation", "patient name:", "referred by:",
        "referred to:", "date of birth:", "age:", "date of evaluation:",
    }
    raw_lines = report_text.splitlines()
    i = 0
    while i < len(raw_lines):
        s = raw_lines[i].lower().strip()
        if any(s.startswith(k) for k in _meta_keys) or s == "":
            i += 1
        else:
            break
    body_lines = raw_lines[i:]


    # Split into paragraph blocks on blank lines
    blocks: List[str] = []
    current: List[str] = []
    for line in body_lines:
        if line.strip() == "":
            if current:
                blocks.append("\n".join(current).strip())
                current = []
        else:
            current.append(line.rstrip())
    if current:
        blocks.append("\n".join(current).strip())


    # Numbered item regex
    _NUM_RE = re.compile(r'^(\d+)[.)]\s+(.+)', re.DOTALL)


    dx_mode  = False   # inside Diagnostic Impression section (stays True through intro text)
    rec_mode = False   # inside Conclusions/Recommendations


    for block in blocks:
        block = block.strip()
        if not block:
            continue


        # ── Section heading (single line, known heading) ──────────────────────
        if '\n' not in block and _re_is_heading(block):
            story.append(Paragraph(_re_sanitize(_re_ensure_colon(block)), SH))
            clean = block.lower().rstrip(':').strip()
            dx_mode  = (clean == "diagnostic impression")
            rec_mode = (clean in ("conclusions/recommendations",
                                  "conclusions / recommendations"))
            continue


        # ── Diagnostic Impression: numbered diagnoses ─────────────────────────
        if dx_mode:
            # Join all lines (strips CRLF/trailing spaces) then split on
            # numbered-item boundaries. Handles three formats:
            #   • Separate lines, no blank between  ("1. Foo\n2. Bar")
            #   • Packed into one paragraph        ("1. Foo 2. Bar 3. Baz")
            #   • Mix of both
            joined = ' '.join(l.strip() for l in block.splitlines() if l.strip())
            raw_parts = re.split(r'(?<=\S)\s+(?=\d+[.)]\s)', joined)
            items: List[Tuple[int, str]] = []
            for part in raw_parts:
                part = part.strip()
                m = _NUM_RE.match(part)
                if m:
                    items.append((int(m.group(1)), m.group(2).strip()))
                elif items:
                    items[-1] = (items[-1][0], items[-1][1] + ' ' + part)
            if items:
                for idx, (num, text) in enumerate(items):
                    style = NL_LAST if idx == len(items) - 1 else NL
                    story.append(Paragraph(f"{num}. {_re_sanitize(text)}", style))
                dx_mode = False
                continue
            # No numbered items found — this is an intro sentence (e.g. OpenAI's
            # "Based on the patient's interview...the following is suggested:").
            # Render it as a normal paragraph but keep dx_mode active so the
            # numbered list in the next block is still caught.
            text = ' '.join(l.strip() for l in block.splitlines())
            story.append(Paragraph(_re_sanitize(text), N))
            continue   # dx_mode remains True


        # ── Conclusions: each numbered recommendation = separate paragraph ─────
        if rec_mode:
            m = _NUM_RE.match(block)
            if m:
                num  = m.group(1)
                text = m.group(2).strip()
                rest = block.splitlines()[1:]
                if rest:
                    text += ' ' + ' '.join(l.strip() for l in rest if l.strip())
                story.append(Paragraph(f"{num}. {_re_sanitize(text)}", NL_LAST))
                continue
            rec_mode = False   # non-numbered block while in rec_mode → normal


        # ── Normal paragraph ──────────────────────────────────────────────────
        text = ' '.join(l.strip() for l in block.splitlines())
        story.append(Paragraph(_re_sanitize(text), N))


    # ── Signature ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.35 * inch))
    sig = _re_asset(_RE_SIG_PRIMARY, _RE_SIG_FALLBACK)
    if os.path.exists(sig):
        sig_img = RLImage(sig, width=1.55 * inch, height=1.05 * inch)
        sig_img.hAlign = 'LEFT'
        story.append(sig_img)
    story.append(Paragraph("Nicholas C. Noll, Ph.D.", SG))
    story.append(Paragraph("Clinical Psychologist", SG))


    doc.build(story)
    return out_path




class NPGSuite(tk.Tk):
    """Five-tab unified NPG practice dashboard."""


    def __init__(self):
        super().__init__()
        self.title("NPG Suite")
        self.geometry("1180x840")
        self.minsize(980, 700)


        _ensure_scaffold()


        # ── load config ──
        try:
            self.cfg = load_config()
        except FileNotFoundError as e:
            messagebox.showerror("Config not found", str(e))
            self.cfg = {}


        self.rcfg: Dict[str, Any] = load_report_config_raw()
        self.sa_path: str         = _resolve_sa_path(self.cfg)
        self.patients_root: str   = _resolve_patients_root(self.cfg)
        self.smtp_conf: Dict      = self.cfg.get("smtp") or {}
        self.scheduled_tasks: List[Dict] = []
        self.contacts             = ProviderContacts(_resolve_contacts_path())


        # ── shared Google clients (lazy) ──
        self._gspread   = None
        self._calendar  = None
        self._drive     = None
        self._google_lock = threading.Lock()


        # ── build UI ──
        self._build_notebook()
        self._build_tab3_checker()    # 1 · Test Checker
        self._build_tab1_transfer()   # 2 · Test Transfer
        self._build_tab2_report()     # 3 · Report Builder
        self._build_tab7_report_editor()  # 4 · Report Editor
        self._build_tab5_sender()     # 5 · Report Sender
        self._build_tab4_billing()    # 6 · Billing
        self._build_tab6_superbill()  # 7 · Superbill
        self._build_tab8_letters()    # 8 · Letter Generator
        self._build_tab9_email()      # 9 · Email
        self.after(60_000, self._t3_task_ticker)


        # ── status bar ──
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var, relief="sunken",
                  anchor="w").pack(side="bottom", fill="x")


        self.after(200, self._post_init)


    # ------------------------------------------------------------------
    # Shared Google client access
    # ------------------------------------------------------------------


    def _init_google(self, log: Callable[[str], None] = print):
        with self._google_lock:
            if self._gspread is None:
                if not os.path.exists(self.sa_path):
                    raise FileNotFoundError(f"Service account not found: {self.sa_path}")
                log("Initializing Google APIs…")
                self._gspread  = init_gspread_client(self.sa_path)
                self._calendar = init_calendar_service(self.sa_path)
                self._drive    = init_drive_service(self.sa_path)
                log("✅ Google APIs ready.")


    def _post_init(self):
        self.status_var.set(f"Config loaded from: {self.cfg.get('_loaded_from','?')}  |  SA: {self.sa_path}")


    # ------------------------------------------------------------------
    # Notebook
    # ------------------------------------------------------------------


    def _build_notebook(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=6, pady=6)


    # ==================================================================
    # ── TAB 1: TEST TRANSFER ──────────────────────────────────────────
    # ==================================================================


    def _build_tab1_transfer(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="  Test Transfer  ")


        # ── controls ──
        ctrl = ttk.LabelFrame(tab, text="Patient", padding=8)
        ctrl.pack(fill="x", padx=8, pady=6)


        ttk.Label(ctrl, text="Patient Name:").grid(row=0, column=0, sticky="w")
        self.t1_patient = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self.t1_patient, width=40).grid(row=0, column=1, padx=6, sticky="w")


        ttk.Label(ctrl, text="Patient Email (auto if blank):").grid(row=0, column=2, sticky="w", padx=(12,0))
        self.t1_email = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self.t1_email, width=36).grid(row=0, column=3, padx=6, sticky="w")


        btn_row = ttk.Frame(tab)
        btn_row.pack(fill="x", padx=8, pady=4)
        ttk.Button(btn_row, text="▶  Run Transfer",
                   command=self._t1_run).pack(side="left", padx=4)
        ttk.Button(btn_row, text="🔍  Deep Search",
                   command=self._t1_deep_search).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Clear Patient",
                   command=self._t1_clear).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Clear Log",
                   command=lambda: self.t1_log.delete("1.0", "end")).pack(side="left", padx=4)


        # ── Fetch Appointments panel ──
        fa_frame = ttk.LabelFrame(tab, text="Fetch Appointments (click to populate Patient Name)", padding=6)
        fa_frame.pack(fill="x", padx=8, pady=4)


        fa_top = ttk.Frame(fa_frame)
        fa_top.pack(fill="x")
        today = dt.date.today().strftime("%Y-%m-%d")
        self.t1_fa_start = tk.StringVar(value=today)
        self.t1_fa_end   = tk.StringVar(value=today)
        ttk.Label(fa_top, text="Start:").pack(side="left")
        ttk.Entry(fa_top, textvariable=self.t1_fa_start, width=12).pack(side="left", padx=4)
        ttk.Label(fa_top, text="End:").pack(side="left")
        ttk.Entry(fa_top, textvariable=self.t1_fa_end, width=12).pack(side="left", padx=4)
        ttk.Button(fa_top, text="Fetch Appointments",
                   command=self._t1_fetch_appts).pack(side="left", padx=8)


        fa_list_frame = ttk.Frame(fa_frame)
        fa_list_frame.pack(fill="x", pady=(4, 0))
        self.t1_appt_lb = tk.Listbox(fa_list_frame, height=5, font=("Consolas", 9),
                                      selectmode="browse", activestyle="dotbox")
        fa_sb = ttk.Scrollbar(fa_list_frame, command=self.t1_appt_lb.yview)
        self.t1_appt_lb.configure(yscrollcommand=fa_sb.set)
        fa_sb.pack(side="right", fill="y")
        self.t1_appt_lb.pack(fill="x", expand=True)
        self.t1_appt_lb.bind("<<ListboxSelect>>", self._t1_appt_selected)
        self.t1_appts_data: List[Dict] = []


        # ── split pane: log left, folder viewer right ──
        pane = tk.PanedWindow(tab, orient="horizontal", sashwidth=6, sashrelief="raised")
        pane.pack(fill="both", expand=True, padx=8, pady=4)


        log_frame = ttk.LabelFrame(pane, text="Log", padding=4)
        self.t1_log = tk.Text(log_frame, wrap="word", state="normal", font=("Consolas", 9))
        sb1 = ttk.Scrollbar(log_frame, command=self.t1_log.yview)
        self.t1_log.configure(yscrollcommand=sb1.set)
        sb1.pack(side="right", fill="y")
        self.t1_log.pack(fill="both", expand=True)
        pane.add(log_frame, stretch="always")


        fv_frame = ttk.LabelFrame(pane, text="Patient Folder Contents", padding=4)
        fv_btn = ttk.Frame(fv_frame)
        fv_btn.pack(fill="x", pady=(0,4))
        ttk.Button(fv_btn, text="↻ Refresh",
                   command=self._t1_refresh_folder).pack(side="left", padx=2)
        ttk.Button(fv_btn, text="📂 Open Folder",
                   command=self._t1_open_folder).pack(side="left", padx=2)
        ttk.Button(fv_btn, text="▶ Open Selected",
                   command=self._t1_open_selected).pack(side="left", padx=2)


        self.t1_filelist = tk.Listbox(fv_frame, font=("Consolas", 9), activestyle="dotbox",
                                       selectmode="browse", width=36)
        sb_fv = ttk.Scrollbar(fv_frame, command=self.t1_filelist.yview)
        self.t1_filelist.configure(yscrollcommand=sb_fv.set)
        sb_fv.pack(side="right", fill="y")
        self.t1_filelist.pack(fill="both", expand=True)
        self.t1_filelist.bind("<Double-Button-1>", lambda e: self._t1_open_selected())
        pane.add(fv_frame, stretch="never")


    def _t1_log(self, msg: str):
        self.t1_log.insert("end", msg + "\n")
        self.t1_log.see("end")
        self.t1_log.update_idletasks()


    def _t1_clear(self):
        self.t1_patient.set("")
        self.t1_email.set("")
        self.t1_log.delete("1.0", "end")
        self.t1_filelist.delete(0, "end")


    def _t1_refresh_folder(self):
        self.t1_filelist.delete(0, "end")
        name = self.t1_patient.get().strip()
        if not name:
            return
        folder = os.path.join(self.patients_root, name.strip())
        if not os.path.isdir(folder):
            self.t1_filelist.insert("end", "(folder not found)")
            return
        entries = sorted(os.listdir(folder))
        if not entries:
            self.t1_filelist.insert("end", "(empty)")
        for e in entries:
            self.t1_filelist.insert("end", e)


    def _t1_open_folder(self):
        name = self.t1_patient.get().strip()
        if not name:
            return
        folder = os.path.join(self.patients_root, name.strip())
        if os.path.isdir(folder):
            open_file_os(folder)
        else:
            messagebox.showinfo("Not found", f"Folder not found:\n{folder}")


    def _t1_open_selected(self):
        sel = self.t1_filelist.curselection()
        if not sel:
            return
        filename = self.t1_filelist.get(sel[0])
        if filename.startswith("("):
            return
        name = self.t1_patient.get().strip()
        path = os.path.join(self.patients_root, name.strip(), filename)
        if os.path.exists(path):
            open_file_os(path)
        else:
            messagebox.showerror("Not found", f"File not found:\n{path}")


    def _t1_fetch_appts(self):
        threading.Thread(target=self._t1_fetch_appts_worker, daemon=True).start()


    def _t1_fetch_appts_worker(self):
        log = self._t1_log
        try:
            self._init_google(log)
            cfg    = self.cfg
            cal_id = resolve_calendar_id(cfg)
            tz_str = cfg.get("calendar_timezone", "America/Chicago")
            start  = dt.datetime.fromisoformat(self.t1_fa_start.get()).date()
            end    = dt.datetime.fromisoformat(self.t1_fa_end.get()).date()
            events = fetch_calendar_events(self._calendar, cal_id, start, end, tz_str, log)
            owner  = cfg.get("calendar_owner_email", "")


            appts: List[Dict] = []
            for ev in events:
                email = extract_patient_email_from_event(ev, owner)
                if not email:
                    continue
                name     = _strip_noll_psych_group(extract_patient_name_tc(ev, email, owner))
                start_s  = event_start_str(ev)
                label_dt = ""
                try:
                    label_dt = dt.datetime.fromisoformat(
                        start_s.replace("Z", "+00:00")).astimezone().strftime("%m/%d %I:%M %p")
                except Exception:
                    label_dt = start_s[:16]
                appts.append({"name": name, "email": email, "start_str": start_s, "label": label_dt})


            def _populate():
                self.t1_appt_lb.delete(0, "end")
                self.t1_appts_data.clear()
                for a in appts:
                    self.t1_appt_lb.insert("end", f"{a['label']}  —  {a['name']}")
                    self.t1_appts_data.append(a)
                log(f"✅ {len(appts)} appointment(s) fetched — click to populate Patient Name.")


            self.after(0, _populate)
        except Exception as e:
            log(f"❌ Fetch Appointments error: {e}\n{traceback.format_exc()}")


    def _t1_appt_selected(self, _event=None):
        sel = self.t1_appt_lb.curselection()
        if not sel:
            return
        appt = self.t1_appts_data[sel[0]]
        self.t1_patient.set(_strip_noll_psych_group(appt["name"]))
        self.t1_email.set(appt["email"])


    def _t1_deep_search(self):
        name = self.t1_patient.get().strip()
        if not name:
            messagebox.showerror("Input error", "Enter a patient name first.")
            return
        self.t1_log.delete("1.0", "end")
        self._t1_log("🔍  Deep Search — scanning ALL email columns + name fallback in every sheet…")
        threading.Thread(target=self._t1_deep_search_worker, args=(name,), daemon=True).start()


    def _t1_deep_search_worker(self, patient_name: str):
        log = self._t1_log
        try:
            self._init_google(log)
            cfg       = self.cfg
            tests_cfg = cfg.get("tests") or []
            patient_folder = ensure_patient_folder(self.patients_root, patient_name)


            found_emails: set = set()
            if self.t1_email.get().strip():
                found_emails.add(normalize_email(self.t1_email.get()))


            log("\n── Pass 1: collecting all emails associated with this name ──")
            for test_def in tests_cfg:
                test_name = test_def.get("name", "<unnamed>")
                sheet_id  = test_def.get("google_sheet_id", "")
                if not sheet_id: continue
                try:
                    sh = call_with_retry(self._gspread.open_by_key, sheet_id, log=log)
                    ws_name = test_def.get("worksheet_name", "Form Responses 1")
                    ws = call_with_retry(sh.worksheet, ws_name, log=log)
                    all_rows = call_with_retry(ws.get_all_values, log=log)
                    email_col = int(cfg.get("email_column_index", 2)) - 1


                    for row_idx, row in enumerate(all_rows[1:], start=2):
                        matched = False
                        if "patient_name_column" in test_def:
                            ci = self._col_letter_to_idx(test_def["patient_name_column"])
                            cell = row[ci] if ci < len(row) else ""
                            matched = self._t1_names_match(cell, patient_name)
                        elif "first_name_column" in test_def and "last_name_column" in test_def:
                            fi = self._col_letter_to_idx(test_def["first_name_column"])
                            li = self._col_letter_to_idx(test_def["last_name_column"])
                            first = row[fi] if fi < len(row) else ""
                            last  = row[li] if li < len(row) else ""
                            matched = self._t1_names_match(f"{first} {last}".strip(), patient_name)
                        else:
                            ni = int(test_def.get("name_column_index", 3)) - 1
                            cell = row[ni] if ni < len(row) else ""
                            matched = self._t1_names_match(cell, patient_name)


                        if matched:
                            em = normalize_email(row[email_col]) if email_col < len(row) else ""
                            if em:
                                if em not in found_emails:
                                    log(f"  [{test_name}] row {row_idx}: NEW email found → {em}")
                                    found_emails.add(em)
                                else:
                                    log(f"  [{test_name}] row {row_idx}: email {em} (already known)")
                except Exception as e:
                    log(f"  [{test_name}] scan error: {e}")


            log(f"\nAll emails found for {patient_name!r}: {sorted(found_emails) or '(none)'}")


            if not found_emails:
                log("⚠️  No emails found — cannot do email-based deep transfer.")
                return


            log("\n── Pass 2: transferring for each discovered email ──")
            transferred_any: List[str] = []
            for email in sorted(found_emails):
                log(f"\n  ▶ Trying email: {email}")
                for test_def in tests_cfg:
                    test_name = test_def.get("name", "<unnamed>")
                    sheet_id  = test_def.get("google_sheet_id", "")
                    if not sheet_id: continue
                    template_path = test_def.get("excel_workbook_path", "")
                    if not os.path.exists(template_path):
                        continue
                    try:
                        sh  = call_with_retry(self._gspread.open_by_key, sheet_id, log=log)
                        ws_name = test_def.get("worksheet_name", "Form Responses 1")
                        ws  = call_with_retry(sh.worksheet, ws_name, log=log)
                        row_idx = self._t1_find_row(ws, test_def, email,
                                                     int(cfg.get("email_column_index", 2)),
                                                     patient_name, log)
                        if row_idx is None:
                            continue


                        base, ext = os.path.splitext(os.path.basename(template_path))
                        dest_name = f"{base} [{email}]{ext}"
                        patient_wb = os.path.join(patient_folder, dest_name)
                        shutil.copy2(template_path, patient_wb)


                        excel_sheet = test_def.get("excel_sheet_name", "Sheet1")
                        segments    = test_def.get("segments")
                        if segments:
                            for seg in segments:
                                vals = self._t1_read_range(ws, row_idx,
                                                           seg["source_start_column"],
                                                           seg["source_end_column"])
                                self._t1_write_excel(patient_wb, excel_sheet,
                                                     seg.get("dest_column", "B"),
                                                     int(seg["dest_start_row"]), vals, log)
                        else:
                            src_start = test_def.get("data_start_column", "")
                            src_end   = test_def.get("data_end_column", "")
                            if not (src_start and src_end): continue
                            vals = self._t1_read_range(ws, row_idx, src_start, src_end)
                            self._t1_write_excel(patient_wb, excel_sheet,
                                                 test_def.get("excel_destination_column", "B"),
                                                 int(test_def.get("excel_destination_start_row", 1)),
                                                 vals, log)
                        log(f"    ✅ {test_name} → {dest_name}")
                        transferred_any.append(f"{test_name} [{email}]")
                    except Exception as e:
                        log(f"    ❌ {test_name}: {e}")


            log(f"\n✅ Deep search complete. Transferred: {transferred_any or '(none)'}")
            self.after(0, self._t1_refresh_folder)
        except Exception as e:
            log(f"!!! ERROR: {e}\n{traceback.format_exc()}")


    def _t1_run(self):
        name = self.t1_patient.get().strip()
        if not name:
            messagebox.showerror("Input error", "Enter a patient name.")
            return
        self.t1_log.delete("1.0", "end")
        threading.Thread(target=self._t1_worker, args=(name,), daemon=True).start()


    def _t1_worker(self, patient_name: str):
        log = self._t1_log
        try:
            self._init_google(log)
            cfg       = self.cfg
            tests_cfg = cfg.get("tests") or []
            if not tests_cfg:
                log("⚠️  No tests defined in config.json under 'tests'.")
                return


            patient_email = normalize_email(self.t1_email.get())
            owner_email   = cfg.get("calendar_owner_email", "")
            appt_date: Optional[dt.date] = None


            if not patient_email:
                log("Attempting to auto-fill email from Calendar…")
                cal_id = resolve_calendar_id(cfg)
                tz_str = cfg.get("calendar_timezone", "America/Chicago")
                today  = dt.date.today()
                events = fetch_calendar_events(
                    self._calendar, cal_id,
                    today - dt.timedelta(days=60), today + dt.timedelta(days=60),
                    tz_str, log,
                )
                for ev in events:
                    eml = extract_patient_email_from_event(ev, owner_email)
                    nm  = infer_patient_name_from_event(ev)
                    if eml and liberal_fullname_match(patient_name, *_split_name(nm)):
                        patient_email = eml
                        start = (ev.get("start") or {})
                        start_str = start.get("dateTime") or start.get("date") or ""
                        try:
                            appt_date = dt.datetime.fromisoformat(
                                start_str.replace("Z", "+00:00")).date()
                            log(f"✅ Found email from Calendar: {patient_email}  (appt date: {appt_date})")
                        except Exception:
                            log(f"✅ Found email from Calendar: {patient_email}")
                        self.after(0, lambda e=patient_email: (
                            self.t1_email.set(e),
                            self.update_idletasks(),
                        ))
                        break


            if patient_email:
                log(f"Using email: {patient_email}")
            else:
                log("⚠️  No email found — will fall back to name matching only.")


            patient_folder = ensure_patient_folder(self.patients_root, patient_name)
            log(f"Patient folder: {patient_folder}")


            email_col_idx = int(cfg.get("email_column_index", 2))
            transferred: List[str] = []


            for test_def in tests_cfg:
                test_name = test_def.get("name", "<unnamed>")
                try:
                    log(f"\n─── {test_name} ───")
                    sheet_id = test_def.get("google_sheet_id", "")
                    if not sheet_id:
                        log("  No google_sheet_id — skipping"); continue


                    sh = call_with_retry(self._gspread.open_by_key, sheet_id, log=log)
                    ws_name = test_def.get("worksheet_name", "Form Responses 1")
                    ws = call_with_retry(sh.worksheet, ws_name, log=log)
                    log(f"  Worksheet: {ws_name}")


                    row_idx = self._t1_find_row(
                        ws, test_def, patient_email, email_col_idx, patient_name, log
                    )
                    if row_idx is None:
                        log("  ❌ No match found — skipping")
                        continue


                    try:
                        row_email = ws.cell(row=row_idx, col=email_col_idx).value
                        log(f"  Row email (col {email_col_idx}): {row_email}")
                    except Exception:
                        pass


                    template_path = test_def.get("excel_workbook_path", "")
                    if not os.path.exists(template_path):
                        log(f"  ❌ Template not found: {template_path}"); continue


                    patient_wb = os.path.join(patient_folder, os.path.basename(template_path))
                    shutil.copy2(template_path, patient_wb)
                    log(f"  Copied template → {patient_wb}")


                    excel_sheet = test_def.get("excel_sheet_name", "Sheet1")
                    segments    = test_def.get("segments")


                    if segments:
                        log(f"  Using {len(segments)} segment(s)")
                        for seg in segments:
                            src_start = seg["source_start_column"]
                            src_end   = seg["source_end_column"]
                            dest_col  = seg.get("dest_column", test_def.get("excel_destination_column", "B"))
                            dest_row  = int(seg["dest_start_row"])
                            vals = self._t1_read_range(ws, row_idx, src_start, src_end)
                            log(f"    Segment {src_start}{row_idx}:{src_end}{row_idx} → {dest_col}{dest_row} ({len(vals)} cells)")
                            self._t1_write_excel(patient_wb, excel_sheet, dest_col, dest_row, vals, log)
                    else:
                        src_start = test_def.get("data_start_column", "")
                        src_end   = test_def.get("data_end_column",   "")
                        if not (src_start and src_end):
                            log("  ❌ Missing data_start_column / data_end_column — skipping"); continue
                        dest_col = test_def.get("excel_destination_column", "B")
                        dest_row = int(test_def.get("excel_destination_start_row", 1))
                        vals = self._t1_read_range(ws, row_idx, src_start, src_end)
                        log(f"  Range {src_start}{row_idx}:{src_end}{row_idx} → {dest_col}{dest_row} ({len(vals)} cells)")
                        self._t1_write_excel(patient_wb, excel_sheet, dest_col, dest_row, vals, log)


                    log(f"  ✅ Written to workbook")
                    transferred.append(test_name)


                except Exception as e:
                    log(f"  ❌ Error: {e}\n{traceback.format_exc()}")


            log(f"\n✅ Transfer complete. Tests transferred: {transferred or '(none)'}")


            folder_id = cfg.get("drive_meet_recordings_folder_id", "")
            if folder_id:
                log("\n─── Transcripts (Drive) ───")
                download_transcripts_from_drive(
                    self._drive, folder_id, patient_name, patient_folder, log,
                    appt_date=appt_date)
            else:
                log("\n(No drive_meet_recordings_folder_id set — transcript download skipped)")


            log(f"\nDone. Patient folder: {patient_folder}")


            self.after(0, lambda n=patient_name: (
                self.t2_patient.set(n),
                self._t1_refresh_folder(),
            ))


        except Exception as e:
            log(f"!!! ERROR: {e}\n{traceback.format_exc()}")


    def _t1_find_row(self, ws, test_def: Dict, patient_email: str,
                     email_col_idx: int, patient_name: str, log: Callable) -> Optional[int]:
        if patient_email:
            target = normalize_email(patient_email)
            email_vals = call_with_retry(ws.col_values, email_col_idx, log=log)
            log(f"  Searching col {email_col_idx} for email: {target}  ({len(email_vals)} rows)")
            for idx, v in enumerate(email_vals[1:], start=2):
                if normalize_email(v) == target:
                    log(f"  ✅ Matched by email at row {idx}")
                    return idx
            log("  (no email match — trying name fallback)")


        if "patient_name_column" in test_def:
            col_letter = test_def["patient_name_column"]
            col_idx    = self._col_letter_to_idx(col_letter) + 1
            name_vals  = call_with_retry(ws.col_values, col_idx, log=log)
            log(f"  Name fallback: col {col_letter} ({len(name_vals)} rows)")
            for idx, v in enumerate(name_vals[1:], start=2):
                if self._t1_names_match(v, patient_name):
                    log(f"  ✅ Matched by full name at row {idx} ({v!r})")
                    return idx


        elif "first_name_column" in test_def and "last_name_column" in test_def:
            first_idx = self._col_letter_to_idx(test_def["first_name_column"]) + 1
            last_idx  = self._col_letter_to_idx(test_def["last_name_column"])  + 1
            all_rows  = call_with_retry(ws.get_all_values, log=log)
            log(f"  Name fallback: first col {test_def['first_name_column']}, last col {test_def['last_name_column']}")
            for row_idx, row in enumerate(all_rows[1:], start=2):
                first = row[first_idx - 1] if len(row) >= first_idx else ""
                last  = row[last_idx  - 1] if len(row) >= last_idx  else ""
                candidate = f"{first} {last}".strip()
                if self._t1_names_match(candidate, patient_name):
                    log(f"  ✅ Matched by first+last at row {row_idx} ({candidate!r})")
                    return row_idx


        else:
            name_col_idx = int(test_def.get("name_column_index", 3))
            name_vals    = call_with_retry(ws.col_values, name_col_idx, log=log)
            log(f"  Name fallback: col index {name_col_idx} ({len(name_vals)} rows)")
            for idx, v in enumerate(name_vals[1:], start=2):
                if self._t1_names_match(v, patient_name):
                    log(f"  ✅ Matched by name at row {idx} ({v!r})")
                    return idx


        return None


    @staticmethod
    def _t1_names_match(sheet_val: str, target: str) -> bool:
        def tokens(s):
            s = re.sub(r"[,\s]+", " ", (s or "").lower().strip())
            return [t for t in s.split() if t]
        st = tokens(sheet_val)
        tt = tokens(target)
        if not st or not tt: return False
        if st == tt: return True
        if len(st) == len(tt) == 2 and st == list(reversed(tt)): return True
        return set(tt).issubset(set(st))


    @staticmethod
    def _t1_read_range(ws, row_idx: int, start_col: str, end_col: str) -> List:
        cell_range = f"{start_col}{row_idx}:{end_col}{row_idx}"
        rows = ws.get(cell_range)
        if not rows:
            return []
        row = rows[0]
        start_i = NPGSuite._col_letter_to_idx(start_col)
        end_i   = NPGSuite._col_letter_to_idx(end_col)
        expected = end_i - start_i + 1
        if len(row) < expected:
            row = row + [""] * (expected - len(row))
        return row


    @staticmethod
    def _col_letter_to_idx(col: str) -> int:
        col = (col or "A").upper().strip()
        result = 0
        for ch in col:
            result = result * 26 + (ord(ch) - ord("A") + 1)
        return result - 1


    @staticmethod
    def _t1_write_excel(path: str, sheet: str, col_letter: str, start_row: int,
                         values: List, log: Callable):
        if openpyxl_load_workbook is None:
            log("  ⚠️  openpyxl not installed — cannot write Excel."); return
        wb = openpyxl_load_workbook(path)
        ws = wb[sheet] if sheet in wb.sheetnames else wb.active
        col_idx = NPGSuite._col_letter_to_idx(col_letter) + 1
        for i, v in enumerate(values):
            ws.cell(row=start_row + i, column=col_idx, value=v)
        wb.save(path)
        # Force Excel to recalculate scoring formulas by opening and re-saving via
        # xlwings (which invokes the live Excel engine).  Without this step openpyxl
        # leaves the old cached formula results in the file, so the AI_Export sheet
        # would still carry stale scores when the payload is built.
        if xw is not None:
            try:
                app = xw.App(visible=False, add_book=False)
                app.display_alerts = False
                app.screen_updating = False
                xwb = app.books.open(path)
                xwb.save()
                xwb.close()
                app.quit()
                log("  ✅ Excel recalculated and saved (xlwings).")
            except Exception as _xw_err:
                log(f"  ⚠️  xlwings recalc skipped ({_xw_err}) — scores may be stale.")


    # ==================================================================
    # ── TAB 2: REPORT BUILDER ─────────────────────────────────────────
    # ==================================================================


    def _build_tab2_report(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="  Report Builder  ")


        ctrl = ttk.LabelFrame(tab, text="Patient", padding=8)
        ctrl.pack(fill="x", padx=8, pady=6)


        ttk.Label(ctrl, text="Patient Name:").grid(row=0, column=0, sticky="w")
        self.t2_patient = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self.t2_patient, width=40).grid(row=0, column=1, padx=6, sticky="w")
        ttk.Button(ctrl, text="Clear",
                   command=lambda: self.t2_patient.set("")).grid(row=0, column=2, padx=4, sticky="w")


        eng = ttk.LabelFrame(tab, text="Generation Engine", padding=8)
        eng.pack(fill="x", padx=8, pady=4)


        self.t2_engine = tk.StringVar(value="qwen_single")
        ttk.Radiobutton(eng, text="Qwen 235B — Single Prompt (primary)",
                        variable=self.t2_engine, value="qwen_single").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(eng, text="Qwen 235B — Segmented 3-Phase (alternative)",
                        variable=self.t2_engine, value="qwen").grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(eng, text="OpenAI (alternative)",
                        variable=self.t2_engine, value="openai").grid(row=2, column=0, sticky="w")


        self.t2_open_after = tk.BooleanVar(value=True)
        ttk.Checkbutton(eng, text="Open draft in Notepad after generation",
                        variable=self.t2_open_after).grid(row=0, column=1, sticky="w", padx=20)


        ttk.Label(eng, text="Open WebUI API Key:").grid(row=4, column=0, sticky="w", pady=(6,0))
        self.t2_webui_key = tk.StringVar()
        ttk.Entry(eng, textvariable=self.t2_webui_key, width=52, show="*"
                  ).grid(row=4, column=1, sticky="w", padx=6, pady=(6,0))
        ttk.Label(eng, text="(leave blank to use ndp4 settings / OPENWEBUI_API_KEY env var)",
                  foreground="gray").grid(row=5, column=1, sticky="w", padx=6)


        ph = ttk.LabelFrame(tab, text="Qwen Prompt Files (ProgramData\\NollPsych\\)", padding=8)
        ph.pack(fill="x", padx=8, pady=4)
        pd_dir = _programdata_dir()


        self.t2_p1_path = tk.StringVar(value=os.path.join(pd_dir, "report_prompt_spark_p1_background.txt"))
        self.t2_p2_path = tk.StringVar(value=os.path.join(pd_dir, "report_prompt_spark_p2_tests.txt"))
        self.t2_p3_path = tk.StringVar(value=os.path.join(pd_dir, "report_prompt_spark_p3_dx_recs.txt"))


        for row_n, (label, var) in enumerate([
            ("Phase 1 (Background):", self.t2_p1_path),
            ("Phase 2 (Test Results):", self.t2_p2_path),
            ("Phase 3 (Dx / Recs):", self.t2_p3_path),
        ]):
            ttk.Label(ph, text=label, width=22, anchor="e").grid(row=row_n, column=0, sticky="e")
            ttk.Entry(ph, textvariable=var, width=64).grid(row=row_n, column=1, padx=4, sticky="w")
            ttk.Button(ph, text="Browse",
                       command=lambda v=var: v.set(
                           filedialog.askopenfilename(filetypes=[("Text", "*.txt"), ("All", "*")]) or v.get()
                       )).grid(row=row_n, column=2, padx=2)
            ttk.Button(ph, text="Open",
                       command=lambda v=var: open_file_os(v.get())).grid(row=row_n, column=3, padx=2)


        # Single-prompt file field (used when engine = qwen_single)
        _sp_lf = ttk.LabelFrame(
            tab,
            text="Qwen Single-Prompt File  (shared with OpenAI — used when Single Prompt engine is selected)",
            padding=8)
        _sp_lf.pack(fill="x", padx=8, pady=4)
        _pd2 = _programdata_dir()
        self.t2_sp_path = tk.StringVar(
            value=r"C:\ProgramData\NPG_GUI\report_prompt.txt")
        ttk.Label(_sp_lf, text="Single Prompt:", width=22, anchor="e"
                  ).grid(row=0, column=0, sticky="e")
        ttk.Entry(_sp_lf, textvariable=self.t2_sp_path, width=64
                  ).grid(row=0, column=1, padx=4, sticky="w")
        ttk.Button(_sp_lf, text="Browse",
                   command=lambda: self.t2_sp_path.set(
                       filedialog.askopenfilename(
                           filetypes=[("Text", "*.txt"), ("All", "*")])
                       or self.t2_sp_path.get()
                   )).grid(row=0, column=2, padx=2)
        ttk.Button(_sp_lf, text="Open",
                   command=lambda: open_file_os(self.t2_sp_path.get())
                   ).grid(row=0, column=3, padx=2)
        ttk.Label(_sp_lf,
                  text="(if file is missing a built-in default prompt is used)",
                  foreground="gray").grid(row=1, column=1, sticky="w", padx=4)


        btn_row = ttk.Frame(tab)
        btn_row.pack(fill="x", padx=8, pady=4)
        ttk.Button(btn_row, text="1. Build Payload Only",
                   command=self._t2_build_payload).pack(side="left", padx=4)
        ttk.Button(btn_row, text="2. Generate Report",
                   command=self._t2_generate).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Clear Log",
                   command=lambda: self.t2_log.delete("1.0", "end")).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Test LLM Connection",
                   command=self._t2_test_llm).pack(side="left", padx=4)


        log_frame = ttk.LabelFrame(tab, text="Log", padding=4)
        log_frame.pack(fill="both", expand=True, padx=8, pady=4)
        self.t2_log = tk.Text(log_frame, wrap="word", font=("Consolas", 9))
        sb2 = ttk.Scrollbar(log_frame, command=self.t2_log.yview)
        self.t2_log.configure(yscrollcommand=sb2.set)
        sb2.pack(side="right", fill="y")
        self.t2_log.pack(fill="both", expand=True)


    def _t2_log(self, msg: str):
        self.t2_log.insert("end", msg + "\n")
        self.t2_log.see("end")
        self.t2_log.update_idletasks()


    def _t2_get_patient_folder(self) -> Optional[str]:
        name = self.t2_patient.get().strip()
        if not name:
            messagebox.showerror("Input error", "Enter a patient name.")
            return None
        return ensure_patient_folder(self.patients_root, name)


    def _t2_build_payload(self):
        folder = self._t2_get_patient_folder()
        if not folder: return
        self.t2_log.delete("1.0", "end")
        threading.Thread(target=self._t2_payload_worker, args=(folder,), daemon=True).start()


    def _t2_payload_worker(self, folder: str):
        log = self._t2_log
        try:
            log(f"Building payload for: {folder}")
            rcfg = self.rcfg
            payload = build_report_payload(folder, rcfg)
            out = save_payload(folder, payload)
            log(f"✅ Payload saved: {out}")
            for name, td in payload.get("tests", {}).items():
                rows = td.get("rows", [])
                err  = td.get("error")
                if err: log(f"  ⚠️  {name}: {err}")
                else:   log(f"  ✅ {name}: {len(rows)} rows")
            trans = payload.get("transcript", {})
            if trans.get("path"):
                log(f"  ✅ Transcript: {trans['path']} ({len(trans.get('text',''))} chars)")
            else:
                log("  ⚠️  No transcript found")
        except Exception as e:
            log(f"❌ {e}\n{traceback.format_exc()}")


    def _t2_generate(self):
        folder = self._t2_get_patient_folder()
        if not folder: return
        self.t2_log.delete("1.0", "end")
        threading.Thread(target=self._t2_generate_worker, args=(folder,), daemon=True).start()


    def _t2_generate_worker(self, folder: str):
        log = self._t2_log
        try:
            log("Building payload…")
            payload = build_report_payload(folder, self.rcfg)
            save_payload(folder, payload)


            engine = self.t2_engine.get()


            if engine in ("qwen", "qwen_single"):
                hcfg = load_qwen_config(self.rcfg)
                ui_key = self.t2_webui_key.get().strip()
                if ui_key:
                    hcfg.api_key = ui_key
                log(f"Engine: Qwen ({hcfg.base_url}{hcfg.api_path}  model={hcfg.model})")
                log(f"  API key: {'set (' + str(len(hcfg.api_key)) + ' chars)' if hcfg.api_key else '⚠️  NOT SET — will likely get 401'}")


                def _read_prompt(path_var: tk.StringVar) -> str:
                    p = path_var.get().strip()
                    if os.path.exists(p):
                        with open(p, "r", encoding="utf-8") as f:
                            return f.read()
                    log(f"  ⚠️  Prompt file not found: {p} — using minimal default")
                    return ("You are an expert clinical psychologist writing a neuropsychological "
                            "evaluation report. Use plain text, no markdown.")


                if engine == "qwen_single":
                    # Resolve prompt: prefer OpenAI prompt_file from rcfg, fall back to
                    # the single-prompt path field, then fall back to built-in default.
                    _single_prompt = ""
                    _oai_cfg = self.rcfg.get("openai") or {}
                    _oai_prompt_file = _oai_cfg.get("prompt_file", "")
                    for _candidate in [
                        _oai_prompt_file,
                        os.path.join(_programdata_dir(), _oai_prompt_file) if _oai_prompt_file else "",
                        self.t2_sp_path.get().strip(),
                    ]:
                        if _candidate and os.path.exists(_candidate):
                            with open(_candidate, "r", encoding="utf-8") as _spf:
                                _single_prompt = _spf.read()
                            log(f"  Single-prompt file: {_candidate}")
                            break
                    if not _single_prompt:
                        log("  ⚠️  No prompt file found — using built-in default")
                        _single_prompt = (
                            "You are an expert clinical neuropsychologist. "
                            "Write a complete, professional neuropsychological evaluation "
                            "report in plain prose. Include all standard sections: "
                            "Identifying Information and Referral Question, "
                            "History and Background Information, "
                            "Mental Status Examination, Tests Administered, "
                            "Neuropsychological/Personality Test Results, "
                            "Diagnostic Impression (numbered ICD-10 diagnoses), and "
                            "Conclusions/Recommendations. "
                            "Use plain text only — no markdown, no bold, no bullets. "
                            "Write all sections in full, detailed paragraphs."
                        )
                    draft = generate_qwen_single_prompt(payload, hcfg, _single_prompt, log)
                else:
                    p1 = _read_prompt(self.t2_p1_path)
                    p2 = _read_prompt(self.t2_p2_path)
                    p3 = _read_prompt(self.t2_p3_path)
                    draft = generate_heretic_segmented(payload, hcfg, p1, p2, p3, log)


            else:
                log("Engine: OpenAI")
                draft = generate_openai_report(payload, self.rcfg, log)


            # Strip any markdown the LLM emitted despite instructions
            draft = _strip_llm_markdown(draft)
            log(f"  Markdown stripped — {len(draft):,} chars after cleanup")


            draft_path = os.path.join(folder, "draft_report.txt")
            with open(draft_path, "w", encoding="utf-8") as f:
                f.write(draft)
            log(f"\n✅ Draft saved: {draft_path}  ({len(draft):,} chars)")


            if self.t2_open_after.get():
                open_file_os(draft_path)


            # Push draft to Report Editor tab
            self.after(0, lambda d=draft, n=self.t2_patient.get().strip():
                self._t7_load_from_builder(n, d))


        except Exception as e:
            log(f"❌ {e}\n{traceback.format_exc()}")


    def _t2_test_llm(self):
        threading.Thread(target=self._t2_test_llm_worker, daemon=True).start()

    def _t2_test_llm_worker(self):
        log = self._t2_log
        try:
            hcfg = load_qwen_config(self.rcfg)
            ui_key = self.t2_webui_key.get().strip()
            if ui_key:
                hcfg.api_key = ui_key
            models_url = hcfg.base_url.rstrip("/") + "/v1/models"
            headers = {"Authorization": f"Bearer {hcfg.api_key}"} if hcfg.api_key else {}
            resp = requests.get(models_url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("data", [])
            ids = [m.get("id", "?") for m in data]
            log(f"✅ Connected — model: {', '.join(ids)}")
        except Exception as e:
            log(f"❌ Connection failed: {e}")


    # ==================================================================
    # ── TAB 3: TEST CHECKER ───────────────────────────────────────────
    # ==================================================================


    def _build_tab3_checker(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="  Test Checker  ")


        ctrl = ttk.LabelFrame(tab, text="Date Range", padding=8)
        ctrl.pack(fill="x", padx=8, pady=6)


        today = dt.date.today().strftime("%Y-%m-%d")
        self.t3_start = tk.StringVar(value=today)
        self.t3_end   = tk.StringVar(value=today)


        ttk.Label(ctrl, text="Start (YYYY-MM-DD):").grid(row=0, column=0, sticky="w")
        ttk.Entry(ctrl, textvariable=self.t3_start, width=14).grid(row=0, column=1, padx=4)
        ttk.Label(ctrl, text="End:").grid(row=0, column=2, padx=(12,4))
        ttk.Entry(ctrl, textvariable=self.t3_end, width=14).grid(row=0, column=3, padx=4)
        ttk.Button(ctrl, text="Fetch Appointments",
                   command=self._t3_fetch).grid(row=0, column=4, padx=8)


        rctrl = ttk.LabelFrame(tab, text="Actions", padding=8)
        rctrl.pack(fill="x", padx=8, pady=4)


        self.t3_reminder_type = tk.StringVar(value="Basic appointment reminder")
        ttk.Label(rctrl, text="Reminder type:").grid(row=0, column=0, sticky="w")
        ttk.Combobox(rctrl, textvariable=self.t3_reminder_type, width=34, state="readonly",
                     values=["Basic appointment reminder", "Appointment + Insurance details"]
                     ).grid(row=0, column=1, padx=6, sticky="w")
        ttk.Button(rctrl, text="Send Now (checked)",
                   command=self._t3_send_reminders).grid(row=0, column=2, padx=4)
        ttk.Button(rctrl, text="Check Tests Now",
                   command=self._t3_check_tests).grid(row=0, column=3, padx=4)


        self.t3_insurance_only = tk.BooleanVar(value=False)
        ttk.Checkbutton(rctrl, text="Insurance Form Only",
                        variable=self.t3_insurance_only
                        ).grid(row=0, column=4, padx=12, sticky="w")


        ttk.Label(rctrl, text="Days before appt:").grid(row=1, column=0, sticky="w", pady=(6,0))
        self.t3_days_prior = tk.StringVar(value="3")
        ttk.Spinbox(rctrl, textvariable=self.t3_days_prior, from_=0, to=30, width=5
                    ).grid(row=1, column=1, sticky="w", padx=6, pady=(6,0))
        ttk.Button(rctrl, text="Schedule Reminders",
                   command=self._t3_schedule_reminders).grid(row=1, column=2, padx=4, pady=(6,0))
        ttk.Button(rctrl, text="Schedule Auto Test-Check",
                   command=self._t3_schedule_auto_check).grid(row=1, column=3, padx=4, pady=(6,0))


        self.t3_sched_status = tk.StringVar(value="No scheduled tasks.")
        ttk.Label(rctrl, textvariable=self.t3_sched_status, foreground="blue"
                  ).grid(row=2, column=0, columnspan=4, sticky="w", pady=(4,0))


        ttk.Label(rctrl, text="Custom Subject:").grid(row=3, column=0, sticky="w", pady=(8,0))
        self.t3_custom_subject = tk.StringVar()
        ttk.Entry(rctrl, textvariable=self.t3_custom_subject, width=50
                  ).grid(row=3, column=1, padx=6, pady=(8,0), sticky="w")
        ttk.Button(rctrl, text="Send Custom Now",
                   command=self._t3_send_custom).grid(row=3, column=2, padx=4, pady=(8,0))
        ttk.Button(rctrl, text="Schedule Custom",
                   command=self._t3_schedule_custom).grid(row=3, column=3, padx=4, pady=(8,0))


        self.t3_custom_body = tk.Text(rctrl, height=3, wrap="word")
        self.t3_custom_body.grid(row=4, column=0, columnspan=4, sticky="ew", padx=4, pady=4)
        rctrl.columnconfigure(1, weight=1)


        list_frame = ttk.LabelFrame(tab, text="Appointments", padding=4)
        list_frame.pack(fill="x", padx=8, pady=4)


        canvas = tk.Canvas(list_frame, height=200, borderwidth=0)
        vsb    = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        self.t3_inner = ttk.Frame(canvas)
        self.t3_inner.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=self.t3_inner, anchor="nw")
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")


        self.t3_appointments: List[Dict] = []
        self.t3_rows: List[Dict]         = []


        # ── Test Results viewer ───────────────────────────────────────
        results_lf = ttk.LabelFrame(tab, text="Test Check Results  (click row to open file)", padding=4)
        results_lf.pack(fill="x", padx=8, pady=4)


        res_canvas = tk.Canvas(results_lf, height=130, borderwidth=0)
        res_vsb    = ttk.Scrollbar(results_lf, orient="vertical", command=res_canvas.yview)
        res_canvas.configure(yscrollcommand=res_vsb.set)
        self.t3_results_inner = ttk.Frame(res_canvas)
        self.t3_results_inner.bind("<Configure>",
            lambda e: res_canvas.configure(scrollregion=res_canvas.bbox("all")))
        res_canvas.create_window((0, 0), window=self.t3_results_inner, anchor="nw")
        res_canvas.pack(side="left", fill="both", expand=True)
        res_vsb.pack(side="right", fill="y")


        self.t3_result_rows: List[Dict] = []   # {label, path, frame}


        log_frame = ttk.LabelFrame(tab, text="Log", padding=4)
        log_frame.pack(fill="both", expand=True, padx=8, pady=4)
        self.t3_log = tk.Text(log_frame, wrap="word", height=10, font=("Consolas", 9))
        sb3 = ttk.Scrollbar(log_frame, command=self.t3_log.yview)
        self.t3_log.configure(yscrollcommand=sb3.set)
        sb3.pack(side="right", fill="y")
        self.t3_log.pack(fill="both", expand=True)


    def _t3_log(self, msg: str):
        self.t3_log.insert("end", msg + "\n")
        self.t3_log.see("end")
        self.t3_log.update_idletasks()


    def _t3_clear_results(self):
        for r in self.t3_result_rows:
            r["frame"].destroy()
        self.t3_result_rows.clear()


    def _t3_add_result_row(self, patient_name: str, test_name: str,
                            status: str, file_path: Optional[str]):
        """Add one clickable row to the results viewer.
        status: '✅' or '❌'
        file_path: path to the workbook/file, or None if not applicable."""
        frame = ttk.Frame(self.t3_results_inner)
        frame.grid(row=len(self.t3_result_rows), column=0, sticky="ew", pady=1)


        color = "darkgreen" if "✅" in status else "darkred"
        lbl_text = f"{status}  {patient_name}  —  {test_name}"
        if file_path:
            lbl_text += "  [click to open]"
        lbl = ttk.Label(frame, text=lbl_text, foreground=color, cursor="hand2" if file_path else "")
        lbl.pack(side="left", padx=4)


        if file_path:
            lbl.bind("<Button-1>", lambda e, p=file_path: open_file_os(p))


        self.t3_result_rows.append({"frame": frame, "path": file_path})


    def _t3_clear_rows(self):
        for r in self.t3_rows:
            r["frame"].destroy()
        self.t3_rows.clear()
        self.t3_appointments.clear()


    def _t3_fetch(self):
        self.t3_log.delete("1.0", "end")
        threading.Thread(target=self._t3_fetch_worker, daemon=True).start()


    def _t3_fetch_worker(self):
        log = self._t3_log
        try:
            self._init_google(log)
            cal_id = resolve_calendar_id(self.cfg)
            tz_str = self.cfg.get("calendar_timezone", "America/Chicago")
            start  = dt.datetime.fromisoformat(self.t3_start.get()).date()
            end    = dt.datetime.fromisoformat(self.t3_end.get()).date()
            events = fetch_calendar_events(self._calendar, cal_id, start, end, tz_str, log)
            owner  = self.cfg.get("calendar_owner_email", "")
            apt_types = self.cfg.get("appointment_types") or {}


            if apt_types:
                log(f"Appointment types in config: {', '.join(apt_types.keys())}")
            else:
                log("⚠️  No appointment_types configured — all rows will show Undetermined")


            self.after(0, self._t3_clear_rows)
            time.sleep(0.05)


            shown = 0
            for ev in events:
                email = extract_patient_email_from_event(ev, owner)
                if not email: continue
                name  = extract_patient_name_tc(ev, email, owner)
                start_s = event_start_str(ev)
                appt_type, candidate = detect_appointment_type(
                    ev.get("summary",""), ev.get("description",""), apt_types)
                log(f"  {name}: extracted={candidate!r}  →  {appt_type or 'Undetermined'}")


                appt = {"event": ev, "start_str": start_s, "name": name,
                        "email": email, "appt_type": appt_type}
                self.after(0, lambda a=appt: self._t3_add_row(a))
                shown += 1


            log(f"\n✅ {shown} appointment(s) loaded.")
        except Exception as e:
            log(f"❌ {e}\n{traceback.format_exc()}")


    def _t3_add_row(self, appt: Dict):
        self.t3_appointments.append(appt)
        apt_types = self.cfg.get("appointment_types") or {}


        frame = ttk.Frame(self.t3_inner)
        frame.grid(row=len(self.t3_rows), column=0, sticky="ew", pady=1)


        sel_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, variable=sel_var).grid(row=0, column=0, padx=4)


        ttk.Label(frame, text=appt["start_str"][:16], width=17).grid(row=0, column=1, sticky="w", padx=2)
        ttk.Label(frame, text=f"{appt['name']} <{appt['email']}>", width=38
                  ).grid(row=0, column=2, sticky="w", padx=2)


        SPECIAL_OPTS = ["<Skip>", "All Tests", "Undetermined"]
        detected = appt["appt_type"]
        default_val = detected if detected else "Undetermined"
        type_var = tk.StringVar(value=default_val)
        opts = SPECIAL_OPTS + sorted(apt_types.keys())
        cb = ttk.Combobox(frame, textvariable=type_var, values=opts, width=38, state="readonly")
        cb.grid(row=0, column=3, padx=4)
        if default_val == "Undetermined":
            cb.configure(foreground="darkred")
            type_var.trace_add("write", lambda *_: cb.configure(
                foreground="darkred" if type_var.get() == "Undetermined" else "black"))


        self.t3_rows.append({"frame": frame, "appt": appt,
                              "sel_var": sel_var, "type_var": type_var})


    def _t3_check_tests(self):
        threading.Thread(target=self._t3_check_worker, daemon=True).start()


    def _t3_check_worker(self):
        log = self._t3_log
        try:
            self._init_google(log)
            # Clear results panel before new check
            self.after(0, self._t3_clear_results)


            apt_types     = self.cfg.get("appointment_types") or {}
            tests_cfg     = self.cfg.get("tests") or []
            ins_only      = self.t3_insurance_only.get()
            ins_cfg       = self.cfg.get("insurance_form") or {}
            ins_sheet_id  = ins_cfg.get("google_sheet_id") or ins_cfg.get("sheet_id", "")
            ins_ws_name   = ins_cfg.get("worksheet", "Form Responses 1")
            email_col     = int(self.cfg.get("email_column_index", 2))
            name_col      = int(self.cfg.get("name_column_index", 3))


            all_test_names: List[str] = [t.get("name","") for t in tests_cfg if t.get("name")]


            results: List[Dict] = []


            for row in self.t3_rows:
                if not row["sel_var"].get(): continue
                appt      = row["appt"]
                type_name = row["type_var"].get()
                if type_name == "<Skip>": continue


                patient_name = appt.get("name", "")
                patient_email = appt.get("email", "")
                log(f"\n{patient_name} <{patient_email}> — {type_name}")


                # Locate patient folder for linking found files
                patient_folder = os.path.join(self.patients_root, patient_name) \
                    if patient_name else None


                if ins_only:
                    check_tests: List[str] = []
                elif type_name in ("All Tests", "Undetermined"):
                    check_tests = list(all_test_names)
                else:
                    check_tests = list(apt_types.get(type_name) or [])
                    if not check_tests:
                        log(f"  ⚠️  No expected tests configured for type '{type_name}'")


                missing: List[str] = []
                present: List[str] = []


                for test_name in check_tests:
                    td = next((t for t in tests_cfg if t.get("name","") == test_name), None)
                    if not td:
                        log(f"  {test_name}: (not in config — skipped)")
                        continue
                    sheet_id = td.get("google_sheet_id","")
                    ws_name  = td.get("worksheet_name", "Form Responses 1")
                    if not sheet_id:
                        log(f"  {test_name}: (no sheet_id)")
                        continue


                    found = check_patient_in_sheet_with_fallback(
                        self._gspread, sheet_id,
                        patient_email=patient_email,
                        patient_name=patient_name,
                        log=log, worksheet_name=ws_name,
                        email_col=email_col, name_col=name_col,
                    )
                    status = "✅ Complete" if found else "❌ Missing"
                    log(f"  {test_name}: {status}")
                    (present if found else missing).append(test_name)


                    # Find associated workbook in patient folder for clickable link
                    wb_path: Optional[str] = None
                    if found and patient_folder and os.path.isdir(patient_folder):
                        pattern = td.get("file_pattern", "")
                        if pattern:
                            hits = glob.glob(os.path.join(patient_folder, pattern))
                            if hits:
                                wb_path = max(hits, key=os.path.getmtime)
                        if not wb_path:
                            tmpl = td.get("excel_workbook_path", "")
                            if tmpl:
                                base = os.path.basename(tmpl)
                                candidate = os.path.join(patient_folder, base)
                                if os.path.exists(candidate):
                                    wb_path = candidate


                    icon = "✅" if found else "❌"
                    self.after(0, lambda n=patient_name, t=test_name,
                               ic=icon, p=wb_path:
                               self._t3_add_result_row(n, t, ic, p))


                if ins_sheet_id:
                    ins_found = check_patient_in_sheet_with_fallback(
                        self._gspread, ins_sheet_id,
                        patient_email=patient_email,
                        patient_name=patient_name,
                        log=log, worksheet_name=ins_ws_name,
                        email_col=email_col, name_col=name_col,
                    )
                    ins_label = "Insurance Form"
                    status = "✅ Complete" if ins_found else "❌ Missing"
                    log(f"  {ins_label}: {status}")
                    (present if ins_found else missing).append(ins_label)
                    icon = "✅" if ins_found else "❌"
                    self.after(0, lambda n=patient_name, ic=icon:
                               self._t3_add_result_row(n, "Insurance Form", ic, None))
                else:
                    log("  Insurance Form: (no sheet configured — skipped)")


                results.append({"appt": appt, "type": type_name,
                                 "expected": check_tests + (["Insurance Form"] if ins_sheet_id else []),
                                 "present": present, "missing": missing})


            log("\n══ Summary ══")
            need_email = [r for r in results if r["missing"]]
            for r in results:
                a = r["appt"]
                log(f"\n{a['name']} <{a['email']}> [{r['type']}]")
                if r["present"]:
                    log(f"  Present: {', '.join(r['present'])}")
                if r["missing"]:
                    log(f"  MISSING: {', '.join(r['missing'])}")
                else:
                    log("  All items present ✅")


            if need_email and self.smtp_conf:
                self.after(0, lambda: self._t3_offer_missing_emails(need_email))
            elif need_email:
                log("\n(SMTP not configured — cannot send reminder emails)")


            log("\n✅ Test check complete.")
        except Exception as e:
            log(f"❌ {e}\n{traceback.format_exc()}")


    def _t3_offer_missing_emails(self, need_email: List[Dict]):
        names = "\n".join(f"  • {r['appt']['name']} — {', '.join(r['missing'])}"
                          for r in need_email)
        answer = messagebox.askyesno(
            "Send missing-test reminders?",
            f"The following patients have incomplete tests:\n\n{names}\n\n"
            "Send reminder emails now?"
        )
        if answer:
            threading.Thread(target=self._t3_send_missing_worker,
                             args=(need_email,), daemon=True).start()


    def _t3_send_missing_worker(self, need_email: List[Dict]):
        log = self._t3_log
        log("\nSending missing-test reminder emails…")
        for r in need_email:
            a = r["appt"]
            meet_link = get_meet_link_from_event(a.get("event", {}))
            ok = send_missing_tests_email_tc(
                smtp_conf    = self.smtp_conf,
                to_email     = a["email"],
                patient_name = a["name"],
                missing_tests= r["missing"],
                appt_start   = a.get("start_str",""),
                meet_link    = meet_link or "",
                log          = log,
            )
            log(f"  {'✅' if ok else '❌'} {a['name']} <{a['email']}>")
        log("Missing-test emails done.")


    def _t3_send_reminders(self):
        if not self.t3_rows:
            messagebox.showerror("No appointments", "Fetch appointments first.")
            return
        if not self.smtp_conf:
            messagebox.showerror("SMTP not configured", "SMTP settings missing in config.json.")
            return
        reminder_type    = self.t3_reminder_type.get()
        include_insurance = "insurance" in reminder_type.lower()
        names = "\n".join(
            f"  • {r['appt']['name']} <{r['appt']['email']}>"
            for r in self.t3_rows if r["sel_var"].get()
        )
        if not names:
            messagebox.showinfo("None selected", "No appointments selected.")
            return
        if not messagebox.askyesno("Send appointment reminders?",
                                    f"Send '{reminder_type}' to:\n\n{names}\n\nSend now?"):
            return
        threading.Thread(target=self._t3_reminder_worker,
                         args=(include_insurance,), daemon=True).start()


    def _t3_reminder_worker(self, include_insurance: bool):
        log = self._t3_log
        log(f"\nSending appointment reminders (insurance section: {include_insurance})…")
        for row in self.t3_rows:
            if not row["sel_var"].get(): continue
            appt = row["appt"]
            meet_link = get_meet_link_from_event(appt.get("event", {}))
            log(f"\n  {appt['name']} <{appt['email']}> {appt.get('start_str','')}")
            ok = send_appointment_reminder_email_tc(
                smtp_conf        = self.smtp_conf,
                to_email         = appt["email"],
                patient_name     = appt["name"],
                appt_start       = appt.get("start_str",""),
                meet_link        = meet_link or "",
                include_insurance= include_insurance,
                log              = log,
            )
            log(f"  {'✅ Sent' if ok else '❌ Failed'}")
        log("Appointment reminders done.")


    def _t3_send_custom(self):
        subject = self.t3_custom_subject.get().strip()
        body    = self.t3_custom_body.get("1.0", "end").strip()
        if not subject or not body:
            messagebox.showerror("Input error", "Enter subject and body for custom message.")
            return
        threading.Thread(target=self._t3_custom_worker, args=(subject, body), daemon=True).start()


    def _t3_custom_worker(self, subject: str, body: str):
        log = self._t3_log
        log(f"\nSending custom message: {subject!r}")
        for row in self.t3_rows:
            if not row["sel_var"].get(): continue
            email = row["appt"]["email"]
            log(f"  → {email}")
            send_smtp(self.smtp_conf, [email], subject, body, log=log)
        log("Custom send done.")


    def _t3_schedule_reminders(self):
        if not self.t3_appointments:
            messagebox.showerror("No appointments", "Fetch appointments first."); return
        if not self.smtp_conf:
            messagebox.showerror("SMTP not configured", "SMTP settings missing in config.json."); return
        reminder_type     = self.t3_reminder_type.get()
        include_insurance = "insurance" in reminder_type.lower()
        days_prior        = max(0, int(self.t3_days_prior.get() or 0))
        if not messagebox.askyesno("Schedule reminders",
            f"Schedule '{reminder_type}' emails for all loaded appointments\n"
            f"{days_prior} day(s) before each appointment?"):
            return
        self._t3_log(f"\n=== Scheduling {reminder_type} ({days_prior} days prior) ===")
        now = dt.datetime.now().astimezone()
        for appt in self.t3_appointments:
            appt_dt = self._t3_parse_appt_dt(appt["start_str"])
            if not appt_dt:
                self._t3_log(f"  Skipping {appt['name']} – cannot parse time"); continue
            run_at = appt_dt - dt.timedelta(days=days_prior)
            kind   = "reminder_insurance" if include_insurance else "reminder_basic"
            if run_at <= now:
                self._t3_log(f"  {appt['name']}: reminder time in past – sending now")
                threading.Thread(target=lambda a=appt, ins=include_insurance: (
                    send_appointment_reminder_email_tc(
                        self.smtp_conf, a["email"], a["name"], a["start_str"],
                        get_meet_link_from_event(a.get("event",{})) or "",
                        ins, self._t3_log)
                ), daemon=True).start()
            else:
                self.scheduled_tasks.append({"kind": kind, "run_at": run_at,
                                              "appt": appt, "done": False})
                self._t3_log(f"  Scheduled: {appt['name']} at {run_at.strftime('%Y-%m-%d %H:%M')}")
        self._t3_update_sched_status()


    def _t3_schedule_auto_check(self):
        if not self.t3_appointments:
            messagebox.showerror("No appointments", "Fetch appointments first."); return
        if not self.smtp_conf:
            messagebox.showerror("SMTP not configured", "SMTP settings missing in config.json."); return
        days_prior = max(0, int(self.t3_days_prior.get() or 0))
        if not messagebox.askyesno("Schedule auto test-check",
            f"Schedule automatic test checking + missing-test emails\n"
            f"{days_prior} day(s) before each appointment?"):
            return
        self._t3_log(f"\n=== Scheduling Auto Test-Check ({days_prior} days prior) ===")
        now = dt.datetime.now().astimezone()
        for appt in self.t3_appointments:
            appt_dt = self._t3_parse_appt_dt(appt["start_str"])
            if not appt_dt:
                self._t3_log(f"  Skipping {appt['name']} – cannot parse time"); continue
            run_at = appt_dt - dt.timedelta(days=days_prior)
            if run_at <= now:
                self._t3_log(f"  {appt['name']}: check time in past – running now")
                threading.Thread(target=self._t3_auto_check_appt,
                                 args=(appt,), daemon=True).start()
            else:
                self.scheduled_tasks.append({"kind": "auto_check", "run_at": run_at,
                                              "appt": appt, "done": False})
                self._t3_log(f"  Scheduled: {appt['name']} at {run_at.strftime('%Y-%m-%d %H:%M')}")
        self._t3_update_sched_status()


    def _t3_schedule_custom(self):
        subject = self.t3_custom_subject.get().strip()
        body    = self.t3_custom_body.get("1.0", "end").strip()
        if not subject and not body:
            messagebox.showerror("Empty message", "Enter a subject and/or body."); return
        if not self.t3_appointments:
            messagebox.showerror("No appointments", "Fetch appointments first."); return
        if not self.smtp_conf:
            messagebox.showerror("SMTP not configured", "SMTP settings missing."); return
        days_prior = max(0, int(self.t3_days_prior.get() or 0))
        if not messagebox.askyesno("Schedule custom message",
            f"Schedule this custom message for all loaded appointments\n"
            f"{days_prior} day(s) before each appointment?"):
            return
        self._t3_log(f"\n=== Scheduling Custom Message ({days_prior} days prior) ===")
        now = dt.datetime.now().astimezone()
        for appt in self.t3_appointments:
            appt_dt = self._t3_parse_appt_dt(appt["start_str"])
            if not appt_dt:
                self._t3_log(f"  Skipping {appt['name']} – cannot parse time"); continue
            run_at = appt_dt - dt.timedelta(days=days_prior)
            if run_at <= now:
                self._t3_log(f"  {appt['name']}: send time in past – sending now")
                threading.Thread(
                    target=lambda a=appt: send_smtp(
                        self.smtp_conf, [a["email"]], subject, body, log=self._t3_log),
                    daemon=True).start()
            else:
                self.scheduled_tasks.append({"kind": "custom", "run_at": run_at,
                                              "appt": appt, "subject": subject,
                                              "body": body, "done": False})
                self._t3_log(f"  Scheduled: {appt['name']} at {run_at.strftime('%Y-%m-%d %H:%M')}")
        self._t3_update_sched_status()


    def _t3_auto_check_appt(self, appt: Dict):
        log = self._t3_log
        apt_types = self.cfg.get("appointment_types") or {}
        tests_cfg = self.cfg.get("tests") or []
        type_name, _cand = detect_appointment_type(
            appt.get("event",{}).get("summary",""),
            appt.get("event",{}).get("description",""),
            apt_types)
        if not type_name:
            log(f"  [AutoCheck] {appt['name']}: could not determine appointment type"); return
        expected: List[str] = apt_types.get(type_name) or []
        log(f"  [AutoCheck] {appt['name']} — {type_name}: {expected}")
        missing: List[str] = []
        for test_name in expected:
            td = next((t for t in tests_cfg if t.get("name","") == test_name), None)
            if not td: continue
            found = check_patient_in_sheet_with_fallback(
                self._gspread, td.get("google_sheet_id",""),
                patient_email=appt["email"], patient_name=appt.get("name",""),
                log=log, worksheet_name=td.get("worksheet_name","Form Responses 1"))
            (missing if not found else []).append(test_name) if not found else None
            log(f"    {test_name}: {'✅' if found else '❌ MISSING'}")
        if missing:
            meet_link = get_meet_link_from_event(appt.get("event",{}))
            send_missing_tests_email_tc(
                self.smtp_conf, appt["email"], appt["name"],
                missing, appt.get("start_str",""), meet_link or "", log)


    @staticmethod
    def _t3_parse_appt_dt(start_str: str) -> Optional[dt.datetime]:
        if not start_str: return None
        try:
            d = dt.datetime.fromisoformat(start_str)
            return d.astimezone() if d.tzinfo else d.replace(
                tzinfo=dt.timezone.utc).astimezone()
        except Exception:
            return None


    def _t3_update_sched_status(self):
        pending = [t for t in self.scheduled_tasks if not t.get("done")]
        if not pending:
            self.t3_sched_status.set("No scheduled tasks.")
        else:
            next_t = min(pending, key=lambda t: t["run_at"])
            names  = ", ".join(t["appt"]["name"] for t in pending[:3])
            more   = f" + {len(pending)-3} more" if len(pending) > 3 else ""
            self.t3_sched_status.set(
                f"{len(pending)} task(s) pending — next: {next_t['run_at'].strftime('%m-%d %H:%M')} "
                f"({next_t['kind']}) — {names}{more}")


    def _t3_task_ticker(self):
        now     = dt.datetime.now().astimezone()
        pending = [t for t in self.scheduled_tasks if not t.get("done") and t["run_at"] <= now]
        for task in pending:
            appt = task["appt"]
            kind = task["kind"]
            self._t3_log(f"\n[Scheduler] {kind} → {appt['name']} <{appt['email']}>")
            try:
                if kind in ("reminder_basic", "reminder_insurance"):
                    ok = send_appointment_reminder_email_tc(
                        self.smtp_conf, appt["email"], appt["name"],
                        appt.get("start_str",""),
                        get_meet_link_from_event(appt.get("event",{})) or "",
                        kind == "reminder_insurance", self._t3_log)
                elif kind == "custom":
                    ok = send_smtp(self.smtp_conf, [appt["email"]],
                                   task.get("subject",""), task.get("body",""),
                                   log=self._t3_log)
                elif kind == "auto_check":
                    self._t3_auto_check_appt(appt); ok = True
                else:
                    self._t3_log(f"  Unknown task kind '{kind}'"); ok = False
                self._t3_log(f"  {'✅ Done' if ok else '❌ Failed'}")
            except Exception as e:
                self._t3_log(f"  ❌ Error: {e}")
            finally:
                task["done"] = True
        if pending:
            self._t3_update_sched_status()
        self.after(60_000, self._t3_task_ticker)


    # ==================================================================
    # ── TAB 4: BILLING ASSISTANT ──────────────────────────────────────
    # ==================================================================


    def _build_tab4_billing(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="  Billing  ")


        ctrl = ttk.LabelFrame(tab, text="Date of Service", padding=8)
        ctrl.pack(fill="x", padx=8, pady=6)


        today = dt.date.today().strftime("%Y-%m-%d")
        self.t4_start = tk.StringVar(value=today)
        self.t4_end   = tk.StringVar(value=today)


        ttk.Label(ctrl, text="Start:").grid(row=0, column=0, sticky="w")
        ttk.Entry(ctrl, textvariable=self.t4_start, width=14).grid(row=0, column=1, padx=4)
        ttk.Label(ctrl, text="End:").grid(row=0, column=2, padx=(12,4))
        ttk.Entry(ctrl, textvariable=self.t4_end, width=14).grid(row=0, column=3, padx=4)
        ttk.Button(ctrl, text="Load Appointments",
                   command=self._t4_load).grid(row=0, column=4, padx=8)
        ttk.Button(ctrl, text="Clear",
                   command=self._t4_clear).grid(row=0, column=5, padx=4)


        list_lf = ttk.LabelFrame(tab, text="Appointments", padding=4)
        list_lf.pack(fill="x", padx=8, pady=4)


        self.t4_appt_var = tk.StringVar()
        self.t4_appt_list = tk.Listbox(list_lf, listvariable=self.t4_appt_var,
                                        height=6, selectmode="single")
        sb4l = ttk.Scrollbar(list_lf, command=self.t4_appt_list.yview)
        self.t4_appt_list.configure(yscrollcommand=sb4l.set)
        sb4l.pack(side="right", fill="y")
        self.t4_appt_list.pack(fill="x", expand=True)
        self.t4_appt_list.bind("<<ListboxSelect>>", self._t4_on_select)
        self.t4_appointments: List[Dict] = []


        pinfo = ttk.LabelFrame(tab, text="Patient / Insurance", padding=8)
        pinfo.pack(fill="x", padx=8, pady=4)


        ttk.Label(pinfo, text="Patient Email:").grid(row=0, column=0, sticky="w")
        self.t4_patient_email = tk.StringVar()
        ttk.Label(pinfo, textvariable=self.t4_patient_email, foreground="navy"
                  ).grid(row=0, column=1, sticky="w", padx=6)


        ttk.Button(pinfo, text="Load Insurance Form",
                   command=self._t4_load_insurance).grid(row=0, column=2, padx=10)


        self.t4_ins_text = tk.Text(pinfo, height=5, wrap="word", state="disabled",
                                    background="#f5f5f5")
        self.t4_ins_text.grid(row=1, column=0, columnspan=3, sticky="ew", pady=4)
        pinfo.columnconfigure(1, weight=1)


        dx = ttk.LabelFrame(tab, text="Diagnosis (ICD-10)", padding=8)
        dx.pack(fill="x", padx=8, pady=4)


        ttk.Label(dx, text="Favorites:").grid(row=0, column=0, sticky="w")
        self.t4_dx_fav = tk.StringVar()
        cfg_favs = self.cfg.get("icd10_favorites") or ICD_FAVORITES
        fav_combo = ttk.Combobox(dx, textvariable=self.t4_dx_fav, width=60,
                                  state="readonly", values=cfg_favs)
        fav_combo.grid(row=0, column=1, padx=6, sticky="w")
        fav_combo.bind("<<ComboboxSelected>>",
                       lambda e: self.t4_dx_main.set(self.t4_dx_fav.get()))


        ttk.Label(dx, text="Search / Enter:").grid(row=1, column=0, sticky="w", pady=(4,0))
        self.t4_dx_main = tk.StringVar()
        icd_combo = ttk.Combobox(dx, textvariable=self.t4_dx_main, width=70)
        icd_combo.grid(row=1, column=1, padx=6, pady=(4,0), sticky="w")
        icd_codes = load_icd_codes(self._t4_log_stub)
        icd_combo["values"] = icd_codes


        prev = ttk.LabelFrame(tab, text="Billing Email Preview", padding=8)
        prev.pack(fill="x", padx=8, pady=4)


        recip_row = ttk.Frame(prev)
        recip_row.pack(fill="x", pady=(0, 4))
        ttk.Label(recip_row, text="Send To:").pack(side="left", padx=(0, 4))
        self.t4_billing_email_var = tk.StringVar()
        self.t4_billing_email_combo = ttk.Combobox(
            recip_row, textvariable=self.t4_billing_email_var, width=40)
        self.t4_billing_email_combo.pack(side="left", padx=(0, 6))
        saved_billing_emails = self._t4_load_billing_emails()
        cfg_billing_email = self.cfg.get("billing_email", "")
        if cfg_billing_email and cfg_billing_email not in saved_billing_emails:
            saved_billing_emails.insert(0, cfg_billing_email)
        self.t4_billing_email_combo["values"] = saved_billing_emails
        if saved_billing_emails:
            self.t4_billing_email_var.set(saved_billing_emails[0])


        btn_prev = ttk.Frame(prev)
        btn_prev.pack(fill="x")
        ttk.Button(btn_prev, text="Preview Email",
                   command=self._t4_preview).pack(side="left", padx=4)
        ttk.Button(btn_prev, text="Send Billing Email",
                   command=self._t4_send).pack(side="left", padx=4)


        self.t4_preview_text = tk.Text(prev, height=8, wrap="word", state="normal",
                                        background="#fffef0")
        self.t4_preview_text.pack(fill="both", expand=True, pady=4)


        log_frame = ttk.LabelFrame(tab, text="Log", padding=4)
        log_frame.pack(fill="both", expand=True, padx=8, pady=4)
        self.t4_log_widget = tk.Text(log_frame, wrap="word", height=6, font=("Consolas", 9))
        sb4 = ttk.Scrollbar(log_frame, command=self.t4_log_widget.yview)
        self.t4_log_widget.configure(yscrollcommand=sb4.set)
        sb4.pack(side="right", fill="y")
        self.t4_log_widget.pack(fill="both", expand=True)


        self.t4_selected_appt: Optional[Dict] = None
        self.t4_insurance_row: Dict[str, str] = {}


    def _t4_log_stub(self, msg: str): pass


    def _t4_log(self, msg: str):
        self.t4_log_widget.insert("end", msg + "\n")
        self.t4_log_widget.see("end")
        self.t4_log_widget.update_idletasks()


    def _t4_clear(self):
        self.t4_appointments.clear()
        self.t4_appt_list.delete(0, "end")
        self.t4_selected_appt = None
        self.t4_patient_email.set("")
        self.t4_insurance_row = {}


    def _t4_load(self):
        self.t4_log_widget.delete("1.0", "end")
        threading.Thread(target=self._t4_load_worker, daemon=True).start()


    def _t4_load_worker(self):
        log = self._t4_log
        try:
            self._init_google(log)
            cal_id = resolve_calendar_id(self.cfg)
            tz_str = self.cfg.get("calendar_timezone", "America/Chicago")
            start  = dt.datetime.fromisoformat(self.t4_start.get()).date()
            end    = dt.datetime.fromisoformat(self.t4_end.get()).date()
            events = fetch_calendar_events(self._calendar, cal_id, start, end, tz_str, log)
            owner  = self.cfg.get("calendar_owner_email", "")


            self.t4_appointments.clear()
            self.after(0, lambda: self.t4_appt_list.delete(0, "end"))


            for ev in events:
                email = extract_patient_email_from_event(ev, owner)
                if not email: continue
                name   = infer_patient_name_from_event(ev)
                start_s = event_start_str(ev)
                appt = {"event": ev, "start_str": start_s, "name": name, "email": email}
                self.t4_appointments.append(appt)
                self.after(0, lambda a=appt: self.t4_appt_list.insert("end",
                    f"{a['start_str'][:16]}  {a['name']}  <{a['email']}>"))


            log(f"✅ {len(self.t4_appointments)} appointment(s) loaded.")
        except Exception as e:
            log(f"❌ {e}\n{traceback.format_exc()}")


    def _t4_on_select(self, event=None):
        sel = self.t4_appt_list.curselection()
        if not sel: return
        idx = sel[0]
        if idx < len(self.t4_appointments):
            self.t4_selected_appt = self.t4_appointments[idx]
            self.t4_patient_email.set(self.t4_selected_appt.get("email", ""))
            self.t4_insurance_row = {}


    def _t4_load_insurance(self):
        if not self.t4_selected_appt:
            messagebox.showerror("No selection", "Select an appointment first.")
            return
        email = self.t4_selected_appt.get("email", "")
        if not email:
            messagebox.showerror("No email", "No patient email for this appointment.")
            return
        threading.Thread(target=self._t4_insurance_worker, args=(email,), daemon=True).start()


    def _t4_insurance_worker(self, email: str):
        log = self._t4_log
        try:
            self._init_google(log)
            ins_conf = self.cfg.get("insurance_form") or {}
            if not ins_conf:
                log("⚠️  No 'insurance_form' in config.json")
                return
            log(f"Loading insurance form for {email}…")
            row = fetch_insurance_row(self._gspread, ins_conf, email, log)
            self.t4_insurance_row = row
            block = format_insurance_block(row)
            self.after(0, lambda b=block: self._t4_set_ins_text(b))
            log("✅ Insurance form loaded.")
        except Exception as e:
            log(f"❌ {e}")


    def _t4_set_ins_text(self, text: str):
        self.t4_ins_text.configure(state="normal")
        self.t4_ins_text.delete("1.0", "end")
        self.t4_ins_text.insert("end", text)
        self.t4_ins_text.configure(state="disabled")


    def _t4_build_preview(self) -> str:
        if not self.t4_selected_appt:
            return "(No appointment selected)"
        appt = self.t4_selected_appt
        dos  = (appt.get("start_str") or "")[:10]
        dx   = self.t4_dx_main.get().strip() or "(no diagnosis selected)"
        ins_block = format_insurance_block(self.t4_insurance_row) if self.t4_insurance_row else "(Insurance not loaded)"
        return (
            f"Date of Service: {dos}\n"
            f"Patient: {appt['name']}  <{appt['email']}>\n"
            f"Diagnosis: {dx}\n\n"
            f"--- Insurance Form ---\n{ins_block}"
        )


    def _t4_preview(self):
        text = self._t4_build_preview()
        self.t4_preview_text.delete("1.0", "end")
        self.t4_preview_text.insert("end", text)


    _BILLING_EMAILS_PATH = r"C:\Suite\billing_emails.json"


    def _t4_load_billing_emails(self) -> List[str]:
        try:
            if os.path.exists(self._BILLING_EMAILS_PATH):
                with open(self._BILLING_EMAILS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return [e for e in data if isinstance(e, str) and e.strip()]
        except Exception:
            pass
        return []


    def _t4_save_billing_email(self, email: str) -> None:
        email = email.strip()
        if not email:
            return
        emails = self._t4_load_billing_emails()
        if email not in emails:
            emails.insert(0, email)
        try:
            os.makedirs(os.path.dirname(self._BILLING_EMAILS_PATH), exist_ok=True)
            with open(self._BILLING_EMAILS_PATH, "w", encoding="utf-8") as f:
                json.dump(emails, f, indent=2)
        except Exception:
            pass
        self.t4_billing_email_combo["values"] = emails


    def _t4_send(self):
        if not self.t4_selected_appt:
            messagebox.showerror("No selection", "Select an appointment first.")
            return
        appt = self.t4_selected_appt
        billing_email = self.t4_billing_email_var.get().strip()
        if not billing_email:
            messagebox.showerror("No recipient", "Enter a billing email address in the Send To box.")
            return
        self._t4_save_billing_email(billing_email)
        dos  = (appt.get("start_str") or "")[:10]
        subj = f"Billing info (DOS {dos}) - {appt['name']}"
        body = self.t4_preview_text.get("1.0", "end").strip()
        if not body:
            body = self._t4_build_preview()
        threading.Thread(target=lambda: send_smtp(
            self.smtp_conf, [billing_email], subj, body, log=self._t4_log
        ), daemon=True).start()


    # ==================================================================
    # ── TAB 5: REPORT SENDER ──────────────────────────────────────────
    # ==================================================================


    def _build_tab5_sender(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="  Report Sender  ")


        ctrl = ttk.LabelFrame(tab, text="Date Range", padding=8)
        ctrl.pack(fill="x", padx=8, pady=6)


        today = dt.date.today().strftime("%Y-%m-%d")
        self.t5_start = tk.StringVar(value=today)
        self.t5_end   = tk.StringVar(value=today)


        ttk.Label(ctrl, text="Start:").grid(row=0, column=0, sticky="w")
        ttk.Entry(ctrl, textvariable=self.t5_start, width=14).grid(row=0, column=1, padx=4)
        ttk.Label(ctrl, text="End:").grid(row=0, column=2, padx=(12,4))
        ttk.Entry(ctrl, textvariable=self.t5_end, width=14).grid(row=0, column=3, padx=4)
        ttk.Button(ctrl, text="Load Appointments",
                   command=self._t5_load).grid(row=0, column=4, padx=8)


        list_lf = ttk.LabelFrame(tab, text="Appointments", padding=4)
        list_lf.pack(fill="x", padx=8, pady=4)


        self.t5_appt_list = tk.Listbox(list_lf, height=6, selectmode="single")
        sb5l = ttk.Scrollbar(list_lf, command=self.t5_appt_list.yview)
        self.t5_appt_list.configure(yscrollcommand=sb5l.set)
        sb5l.pack(side="right", fill="y")
        self.t5_appt_list.pack(fill="x", expand=True)
        self.t5_appt_list.bind("<<ListboxSelect>>", self._t5_on_select)
        self.t5_appointments: List[Dict] = []
        self.t5_selected_appt: Optional[Dict] = None


        pinfo = ttk.LabelFrame(tab, text="Patient", padding=8)
        pinfo.pack(fill="x", padx=8, pady=4)


        ttk.Label(pinfo, text="Patient Email:").grid(row=0, column=0, sticky="w")
        self.t5_patient_email = tk.StringVar()
        ttk.Label(pinfo, textvariable=self.t5_patient_email, foreground="navy"
                  ).grid(row=0, column=1, sticky="w", padx=6)


        ttk.Label(pinfo, text="Report PDF:").grid(row=1, column=0, sticky="w", pady=(4,0))
        self.t5_report_path = tk.StringVar(value="(auto-detected)")
        ttk.Label(pinfo, textvariable=self.t5_report_path, foreground="darkgreen", wraplength=600
                  ).grid(row=1, column=1, columnspan=3, sticky="w", padx=6)
        ttk.Button(pinfo, text="Browse PDF",
                   command=self._t5_browse_pdf).grid(row=1, column=4, padx=6)


        prov = ttk.LabelFrame(tab, text="Referring Provider", padding=8)
        prov.pack(fill="x", padx=8, pady=4)


        ttk.Label(prov, text="Provider (auto from PDF):").grid(row=0, column=0, sticky="w")
        self.t5_provider = tk.StringVar()
        ttk.Entry(prov, textvariable=self.t5_provider, width=44
                  ).grid(row=0, column=1, padx=6, sticky="w")


        ttk.Label(prov, text="Delivery:").grid(row=0, column=2, padx=(10,4))
        self.t5_delivery = tk.StringVar(value="auto")
        ttk.Combobox(prov, textvariable=self.t5_delivery, width=10, state="readonly",
                     values=["auto", "email", "fax"]).grid(row=0, column=3)


        ttk.Label(prov, text="Manual Email:").grid(row=1, column=0, sticky="w", pady=(4,0))
        self.t5_manual_email = tk.StringVar()
        ttk.Entry(prov, textvariable=self.t5_manual_email, width=36
                  ).grid(row=1, column=1, padx=6, pady=(4,0), sticky="w")


        ttk.Label(prov, text="Manual Fax:").grid(row=1, column=2, padx=(10,4), pady=(4,0))
        self.t5_manual_fax = tk.StringVar()
        ttk.Entry(prov, textvariable=self.t5_manual_fax, width=16
                  ).grid(row=1, column=3, pady=(4,0), sticky="w")


        ttk.Label(prov, text="CC:").grid(row=2, column=0, sticky="w", pady=(4,0))
        self.t5_manual_cc = tk.StringVar()
        ttk.Entry(prov, textvariable=self.t5_manual_cc, width=44
                  ).grid(row=2, column=1, columnspan=3, padx=6, pady=(4,0), sticky="w")


        self.t5_npi_status = tk.StringVar(value="")
        ttk.Label(prov, textvariable=self.t5_npi_status, foreground="gray"
                  ).grid(row=3, column=0, columnspan=4, sticky="w", pady=(2,0))


        ttk.Button(prov, text="Save Manual Contact",
                   command=self._t5_save_contact).grid(row=4, column=0, columnspan=2,
                                                        sticky="w", pady=(6,0))
        ttk.Button(prov, text="Clear Fields",
                   command=self._t5_clear_provider_fields).grid(row=4, column=2, columnspan=2,
                                                                  sticky="w", pady=(6,0))


        send_row = ttk.Frame(tab)
        send_row.pack(fill="x", padx=8, pady=6)
        ttk.Button(send_row, text="📧  Send to Patient",
                   command=self._t5_send_patient).pack(side="left", padx=4)
        ttk.Button(send_row, text="📠  Send to Referrer",
                   command=self._t5_send_referrer).pack(side="left", padx=4)
        ttk.Button(send_row, text="📧📠  Send Both",
                   command=self._t5_send_both).pack(side="left", padx=4)


        # ── Summary review panel (shown after Qwen generates a paragraph) ──
        self._t5_summary_frame = ttk.LabelFrame(
            tab, text="Provider Email — Summary Paragraph  (review & edit before sending)",
            padding=6)
        self._t5_summary_frame.pack(fill="x", padx=8, pady=(0, 4))


        self._t5_summary_text = tk.Text(
            self._t5_summary_frame, height=6, wrap="word",
            font=("Segoe UI", 10), relief="flat", borderwidth=1,
            padx=4, pady=4)
        sum_vsb = ttk.Scrollbar(self._t5_summary_frame, command=self._t5_summary_text.yview)
        self._t5_summary_text.configure(yscrollcommand=sum_vsb.set)
        sum_vsb.pack(side="right", fill="y")
        self._t5_summary_text.pack(fill="x", expand=True)


        sum_btn_row = ttk.Frame(self._t5_summary_frame)
        sum_btn_row.pack(fill="x", pady=(4, 0))
        self._t5_sum_status = tk.StringVar(value="")
        ttk.Label(sum_btn_row, textvariable=self._t5_sum_status,
                  foreground="gray").pack(side="left", padx=4)
        ttk.Button(sum_btn_row, text="↺ Regenerate",
                   command=self._t5_regenerate_summary).pack(side="right", padx=4)
        self._t5_approve_btn = ttk.Button(
            sum_btn_row, text="✅  Approve & Send to Referrer",
            command=self._t5_approve_and_send)
        self._t5_approve_btn.pack(side="right", padx=4)


        # Hide panel until a summary is generated
        self._t5_summary_frame.pack_forget()


        log_frame = ttk.LabelFrame(tab, text="Log", padding=4)
        log_frame.pack(fill="both", expand=True, padx=8, pady=4)
        self.t5_log = tk.Text(log_frame, wrap="word", font=("Consolas", 9))
        sb5 = ttk.Scrollbar(log_frame, command=self.t5_log.yview)
        self.t5_log.configure(yscrollcommand=sb5.set)
        sb5.pack(side="right", fill="y")
        self.t5_log.pack(fill="both", expand=True)


        self._t5_pdf_override: Optional[str] = None
        # Pending referrer send state (populated when summary is approved)
        self._t5_pending_referrer: Optional[Dict] = None


    def _t5_log(self, msg: str):
        self.t5_log.insert("end", msg + "\n")
        self.t5_log.see("end")
        self.t5_log.update_idletasks()


    def _t5_load(self):
        self.t5_log.delete("1.0", "end")
        threading.Thread(target=self._t5_load_worker, daemon=True).start()


    def _t5_load_worker(self):
        log = self._t5_log
        try:
            self._init_google(log)
            cal_id = resolve_calendar_id(self.cfg)
            tz_str = self.cfg.get("calendar_timezone", "America/Chicago")
            start  = dt.datetime.fromisoformat(self.t5_start.get()).date()
            end    = dt.datetime.fromisoformat(self.t5_end.get()).date()
            events = fetch_calendar_events(self._calendar, cal_id, start, end, tz_str, log)
            owner  = self.cfg.get("calendar_owner_email", "")


            self.t5_appointments.clear()
            self.after(0, lambda: self.t5_appt_list.delete(0, "end"))


            for ev in events:
                email = extract_patient_email_from_event(ev, owner)
                if not email: continue
                name   = infer_patient_name_from_event(ev)
                start_s = event_start_str(ev)
                appt = {"event": ev, "start_str": start_s, "name": name, "email": email}
                self.t5_appointments.append(appt)
                self.after(0, lambda a=appt: self.t5_appt_list.insert("end",
                    f"{a['start_str'][:16]}  {a['name']}  <{a['email']}>"))


            log(f"✅ {len(self.t5_appointments)} appointment(s) loaded.")
        except Exception as e:
            log(f"❌ {e}\n{traceback.format_exc()}")


    def _t5_on_select(self, event=None):
        sel = self.t5_appt_list.curselection()
        if not sel: return
        idx = sel[0]
        if idx >= len(self.t5_appointments): return
        appt = self.t5_appointments[idx]
        self.t5_selected_appt = appt
        self._t5_pdf_override = None
        self.t5_patient_email.set(appt.get("email", ""))


        pdf, err = find_report_pdf(self.patients_root, appt["name"])
        if pdf:
            self.t5_report_path.set(pdf)
            threading.Thread(target=self._t5_extract_referrer, args=(pdf,), daemon=True).start()
        else:
            self.t5_report_path.set(f"(not found: {err})")


    def _t5_extract_referrer(self, pdf_path: str):
        referred_by = extract_referred_by_from_pdf(pdf_path)
        if referred_by:
            self.after(0, lambda: self.t5_provider.set(referred_by))
            self._t5_log(f"Referred by (from PDF): {referred_by}")
            stored_emails, _ = self.contacts.get_emails(referred_by)
            stored_fax       = self.contacts.get_fax(referred_by)
            if stored_emails:
                self.after(0, lambda: self.t5_manual_email.set(stored_emails[0]))
                self._t5_log(f"Stored email for provider: {stored_emails[0]}")
            elif stored_fax:
                self.after(0, lambda: self.t5_manual_fax.set(stored_fax))
                self._t5_log(f"Stored fax for provider: {stored_fax}")


    def _t5_browse_pdf(self):
        path = filedialog.askopenfilename(
            title="Select report PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*")])
        if path:
            self._t5_pdf_override = path
            self.t5_report_path.set(path)


    def _t5_get_pdf(self) -> Optional[str]:
        if self._t5_pdf_override and os.path.exists(self._t5_pdf_override):
            return self._t5_pdf_override
        if not self.t5_selected_appt:
            messagebox.showerror("No selection", "Select an appointment first.")
            return None
        pdf, err = find_report_pdf(self.patients_root, self.t5_selected_appt["name"])
        if not pdf:
            messagebox.showerror("PDF not found", f"{err}\n\nUse Browse to select manually.")
            return None
        return pdf


    def _t5_send_patient(self):
        if not self.t5_selected_appt:
            messagebox.showerror("No selection", "Select an appointment first.")
            return
        email = self.t5_patient_email.get().strip()
        if not email or "@" not in email:
            messagebox.showerror("No email", "No patient email for this appointment.")
            return
        pdf = self._t5_get_pdf()
        if not pdf: return
        threading.Thread(target=lambda: self._t5_do_send_patient(email, pdf), daemon=True).start()


    def _t5_do_send_patient(self, email: str, pdf: str):
        self._t5_log(f"Sending report to patient: {email}")
        patient_name = (self.t5_selected_appt or {}).get("name", "")
        first = patient_name.split()[0] if patient_name else "Patient"
        body = (
            f"Dear {first},\n\n"
            "Please find a copy of your evaluation report attached.\n\n"
            "If you found our services helpful, we would greatly appreciate "
            "if you took a moment to leave us a Google review using the link below — "
            "it helps others in the community find our practice:\n\n"
            "    https://g.page/r/CVlL6JJnFubNEAI/review\n\n"
            "Thank you,\n"
            f"{self.smtp_conf.get('from_name', 'Noll Psych Group')}"
        )
        ok = send_smtp(
            self.smtp_conf, [email],
            subject="Your Evaluation Report",
            body=body,
            attachments=[pdf],
            log=self._t5_log,
        )
        if ok:
            self.after(0, lambda: messagebox.showinfo("Sent", "Patient email sent successfully."))


    def _t5_send_referrer(self):
        if not self.t5_selected_appt:
            messagebox.showerror("No selection", "Select an appointment first.")
            return
        pdf = self._t5_get_pdf()
        if not pdf: return
        threading.Thread(target=self._t5_referrer_worker, args=(pdf,), daemon=True).start()


    def _t5_referrer_worker(self, pdf: str):
        log = self._t5_log
        appt         = self.t5_selected_appt
        provider     = self.t5_provider.get().strip()
        mode         = self.t5_delivery.get().lower()
        manual_email = self.t5_manual_email.get().strip()
        manual_fax   = digits_only(self.t5_manual_fax.get())
        manual_cc    = parse_cc_list(self.t5_manual_cc.get())
        subject      = f"{appt['name']} Evaluation"
        rapidfax_dom = (self.cfg.get("rapidfax") or {}).get("domain", "rapidfax.com")


        stored_emails, stored_cc = self.contacts.get_emails(provider) if provider else ([], [])
        stored_fax               = self.contacts.get_fax(provider)    if provider else ""


        use_email: Optional[str] = None
        use_fax:   Optional[str] = None
        use_cc: List[str]        = []


        if mode == "email":
            use_email = manual_email or (stored_emails[0] if stored_emails else None)
            use_cc    = manual_cc or stored_cc
        elif mode == "fax":
            use_fax = manual_fax or stored_fax or ""
        else:
            if stored_emails:
                use_email = stored_emails[0]; use_cc = stored_cc
            elif manual_email:
                use_email = manual_email; use_cc = manual_cc
            elif stored_fax:
                use_fax = stored_fax
            elif manual_fax:
                use_fax = manual_fax


        if use_email:
            log(f"Generating referrer email body for: {use_email}"
                + (f" (cc: {use_cc})" if use_cc else ""))
            # Build summary paragraph via Qwen and present for review
            summary = self._t5_generate_summary_paragraph(pdf, appt, provider, log)
            provider_salutation = provider.strip() if provider else "Doctor"
            from_name = self.smtp_conf.get("from_name", "Noll Psych Group")
            body = (
                f"Dear {provider_salutation},\n\n"
                f"{summary}\n\n"
                "The full report is attached for your records. "
                "Please do not hesitate to contact our office if you have any questions.\n\n"
                f"Sincerely,\n{from_name}"
            )
            # Store pending state and show the review panel on the main thread
            self._t5_pending_referrer = {
                "use_email": use_email, "use_cc": use_cc,
                "subject": subject, "pdf": pdf,
                "provider": provider, "manual_email": manual_email,
                "manual_cc": manual_cc, "full_body": body,
                "summary": summary,
                "provider_salutation": provider_salutation,
                "from_name": from_name,
            }
            self.after(0, lambda s=summary: self._t5_show_summary_panel(s))
            return


        if use_fax:
            fax_body = "Please find attached. Thanks for the referral."
            fax_addr = f"{use_fax}@{rapidfax_dom}"
            log(f"Sending to referrer by fax via RapidFax: {fax_addr}")
            ok = send_smtp(self.smtp_conf, [fax_addr], subject, fax_body,
                           attachments=[pdf], log=log)
            if ok:
                if provider and manual_fax and messagebox.askyesno(
                        "Save fax?", f"Save {manual_fax!r} for '{provider}'?"):
                    self.contacts.upsert_fax(provider, manual_fax)
                self.after(0, lambda: self.t5_manual_fax.set(""))
                self.after(0, lambda: messagebox.showinfo("Sent", "Referrer fax sent via RapidFax."))
            return


        if provider:
            log(f"No email/fax found — searching NPI registry for: {provider}")
            self.after(0, lambda: self.t5_npi_status.set("🔍 Searching NPI registry…"))
            fax_body = "Please find attached. Thanks for the referral."


            def _npi_done():
                results = lookup_fax_npi(provider, log)
                self.after(0, lambda: self.t5_npi_status.set(""))
                if not results:
                    self.after(0, lambda: messagebox.showerror("Not found",
                        "No fax found in NPI registry. Enter a fax number manually."))
                    return
                self.after(0, lambda r=results: self._t5_pick_fax(
                    r, provider, pdf, subject, fax_body, rapidfax_dom))


            threading.Thread(target=_npi_done, daemon=True).start()
        else:
            messagebox.showerror("No target",
                "Enter provider email, fax, or provider name for NPI lookup.")


    def _t5_pick_fax(self, results: List[Dict], provider: str, pdf: str,
                      subject: str, body: str, rapidfax_dom: str):
        win = tk.Toplevel(self)
        win.title("Select Fax Number")
        win.geometry("580x300")
        ttk.Label(win, text="Select a fax number from NPI results:").pack(anchor="w", padx=8, pady=6)


        lb = tk.Listbox(win, height=8)
        lb.pack(fill="both", expand=True, padx=8, pady=4)
        for r in results:
            lb.insert("end", f"{r['fax']}  —  {r['name']}  ({r.get('address','')})")


        def _use():
            sel = lb.curselection()
            if not sel: return
            fax_digits = results[sel[0]]["fax"]
            self.t5_manual_fax.set(fax_digits)
            win.destroy()
            fax_addr = f"{fax_digits}@{rapidfax_dom}"
            self._t5_log(f"Sending via RapidFax: {fax_addr}")
            ok = send_smtp(self.smtp_conf, [fax_addr], subject, body,
                           attachments=[pdf], log=self._t5_log)
            if ok:
                if messagebox.askyesno("Save fax?", f"Save fax {fax_digits!r} for '{provider}'?"):
                    self.contacts.upsert_fax(provider, fax_digits)
                messagebox.showinfo("Sent", "Referrer fax sent via RapidFax.")


        ttk.Button(win, text="Use Selected", command=_use).pack(pady=6)


    def _t5_send_both(self):
        self._t5_send_patient()
        self._t5_send_referrer()


    def _t5_save_contact(self):
        provider     = self.t5_provider.get().strip()
        manual_email = self.t5_manual_email.get().strip()
        manual_fax   = digits_only(self.t5_manual_fax.get())
        manual_cc    = parse_cc_list(self.t5_manual_cc.get())
        if not provider:
            messagebox.showerror("Input error", "Enter a provider name first.")
            return
        existing = self.contacts.find(provider)
        if manual_email:
            self.contacts.upsert_email(provider, manual_email, manual_cc)
            self._t5_log(f"✅ Saved email {manual_email!r} for '{provider}'")
            if existing and not self.contacts.contact_has_alias(existing, provider):
                if messagebox.askyesno("Add alias?", f"Add '{provider}' as alias to existing contact?"):
                    self.contacts.add_alias(existing, provider)
        if manual_fax:
            self.contacts.upsert_fax(provider, manual_fax)
            self._t5_log(f"✅ Saved fax {manual_fax!r} for '{provider}'")
        if not manual_email and not manual_fax:
            messagebox.showwarning("Nothing to save", "Enter an email or fax number to save.")


    def _t5_clear_provider_fields(self):
        """Clear all provider contact fields and hide the summary panel."""
        self.t5_provider.set("")
        self.t5_manual_email.set("")
        self.t5_manual_fax.set("")
        self.t5_manual_cc.set("")
        self.t5_delivery.set("auto")
        self.t5_npi_status.set("")
        self._t5_hide_summary_panel()
        self._t5_log("Provider fields cleared.")


    def _t5_show_summary_panel(self, summary: str):
        """Populate the summary panel and make it visible."""
        self._t5_summary_text.delete("1.0", "end")
        self._t5_summary_text.insert("1.0", summary)
        self._t5_sum_status.set("Edit the paragraph above if needed, then click Approve & Send.")
        self._t5_summary_frame.pack(fill="x", padx=8, pady=(0, 4),
                                    before=self.t5_log.master)
        self._t5_log("✏️  Summary paragraph ready — review in the panel above, then approve.")


    def _t5_hide_summary_panel(self):
        self._t5_summary_frame.pack_forget()
        self._t5_pending_referrer = None


    def _t5_approve_and_send(self):
        """Send the referrer email using the (possibly edited) summary paragraph."""
        pending = self._t5_pending_referrer
        if not pending:
            messagebox.showerror("Nothing pending", "No referrer send is waiting for approval.")
            return
        edited_summary = self._t5_summary_text.get("1.0", "end").strip()
        if not edited_summary:
            messagebox.showwarning("Empty summary", "The summary paragraph is empty.")
            return
        # Rebuild full body with the edited paragraph
        body = (
            f"Dear {pending['provider_salutation']},\n\n"
            f"{edited_summary}\n\n"
            "The full report is attached for your records. "
            "Please do not hesitate to contact our office if you have any questions.\n\n"
            f"Sincerely,\n{pending['from_name']}"
        )
        use_email  = pending["use_email"]
        use_cc     = pending["use_cc"]
        subject    = pending["subject"]
        pdf        = pending["pdf"]
        provider   = pending["provider"]
        manual_email = pending["manual_email"]
        manual_cc  = pending["manual_cc"]


        self._t5_hide_summary_panel()
        self._t5_sum_status.set("")
        self._t5_log(f"Sending referrer email to: {use_email}")


        def _do_send():
            ok = send_smtp(self.smtp_conf, [use_email], subject, body,
                           attachments=[pdf], cc_emails=use_cc, log=self._t5_log)
            if ok:
                if provider and manual_email and messagebox.askyesno(
                        "Save email?", f"Save {manual_email!r} for '{provider}'?"):
                    self.contacts.upsert_email(provider, manual_email, manual_cc)
                # Clear manual fields and summary after successful send
                self.after(0, lambda: (
                    self.t5_manual_email.set(""),
                    self.t5_manual_fax.set(""),
                    self._t5_summary_text.delete("1.0", "end"),
                ))
                self.after(0, lambda: messagebox.showinfo("Sent", "Referrer email sent."))


        threading.Thread(target=_do_send, daemon=True).start()


    def _t5_regenerate_summary(self):
        """Re-run Qwen for a fresh summary paragraph."""
        pending = self._t5_pending_referrer
        if not pending:
            messagebox.showerror("Nothing pending", "Send to Referrer first to generate a summary.")
            return
        self._t5_sum_status.set("Regenerating…")
        self._t5_approve_btn.state(["disabled"])


        def _regen():
            new_summary = self._t5_generate_summary_paragraph(
                pending["pdf"], self.t5_selected_appt,
                pending["provider"], self._t5_log)
            pending["summary"] = new_summary
            # Rebuild body
            body = (
                f"Dear {pending['provider_salutation']},\n\n"
                f"{new_summary}\n\n"
                "The full report is attached for your records. "
                "Please do not hesitate to contact our office if you have any questions.\n\n"
                f"Sincerely,\n{pending['from_name']}"
            )
            pending["full_body"] = body
            self.after(0, lambda s=new_summary: (
                self._t5_summary_text.delete("1.0", "end"),
                self._t5_summary_text.insert("1.0", s),
                self._t5_sum_status.set("Regenerated — review and approve."),
                self._t5_approve_btn.state(["!disabled"]),
            ))


        threading.Thread(target=_regen, daemon=True).start()


    def _t5_generate_summary_paragraph(self, pdf: str, appt: Dict,
                                        provider: str, log) -> str:
        """
        Generate and return just the summary paragraph text (no salutation/sign-off).
        Falls back to a plain sentence if Qwen is unavailable or fails.
        """
        patient_name = appt.get("name", "the patient")
        appt_date_str = ""
        try:
            appt_date_str = dt.datetime.fromisoformat(
                appt.get("start_str", "").replace("Z", "+00:00")
            ).astimezone().strftime("%B %-d, %Y")
        except Exception:
            try:
                appt_date_str = appt.get("start_str", "")[:10]
            except Exception:
                pass


        provider_salutation = provider.strip() if provider else "Doctor"


        fallback = (
            f"Thank you for referring {patient_name} to our practice. "
            f"Please find the completed evaluation report attached"
            + (f", pertaining to the telemedicine session conducted on {appt_date_str}"
               if appt_date_str else "")
            + ". We appreciate the referral and hope the report is helpful."
        )


        if PdfReader is None:
            log("  (pypdf not installed — using fallback summary)")
            return fallback


        try:
            reader = PdfReader(pdf)
            all_pages = []
            for page in reader.pages:
                try:
                    all_pages.append(page.extract_text() or "")
                except Exception:
                    pass
            report_text = "\n".join(all_pages).strip()
        except Exception as e:
            log(f"  ⚠️  Could not read PDF: {e} — using fallback summary.")
            return fallback


        if not report_text:
            log("  ⚠️  No text extracted from PDF — using fallback summary.")
            return fallback


        extract = self._t5_extract_summary_section(report_text)
        log(f"  Calling Qwen for referrer summary ({len(extract):,} chars of report)…")


        system_prompt = (
            "You are a clinical assistant helping a neuropsychologist write a brief, "
            "professional email to a referring provider.\n\n"
            "Write exactly ONE paragraph — no bullet points, no numbered lists, no markdown "
            "formatting, no bold or italic text, no headers. Plain prose only.\n\n"
            "The paragraph should:\n"
            "  1. Thank the provider for the referral.\n"
            "  2. Mention the patient's name and the date of the telemedicine evaluation.\n"
            "  3. Briefly state the primary diagnoses reached.\n"
            "  4. Provide a concise summary of the key clinical recommendations.\n\n"
            "The paragraph should read naturally and professionally, as if written by "
            "the evaluating psychologist. Do not include any salutation or sign-off — "
            "only the paragraph itself."
        )
        user_msg = (
            f"Patient: {patient_name}\n"
            f"Telemedicine date: {appt_date_str or 'see report'}\n"
            f"Referring provider: {provider_salutation}\n\n"
            f"Report excerpt:\n{extract}"
        )


        try:
            hcfg = load_qwen_config(self.rcfg)
            t2_key = self.t2_webui_key.get().strip() if hasattr(self, "t2_webui_key") else ""
            if t2_key:
                hcfg.api_key = t2_key


            url      = hcfg.base_url.rstrip("/") + hcfg.api_path
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_msg},
            ]
            raw, finish = _webui_call(url, hcfg.model, 0.3, 120, messages,
                                      max_tokens=800, api_key=hcfg.api_key)
            summary = raw.strip()


            for _ in range(3):
                if finish != "length" and not _looks_truncated(summary):
                    break
                log("  → summary looks incomplete — continuing…")
                messages.append({"role": "assistant", "content": summary})
                messages.append({"role": "user", "content":
                    "Please complete the sentence you were writing. "
                    "Continue exactly where you left off — do not repeat anything. "
                    "End with a period."})
                more, finish = _webui_call(url, hcfg.model, 0.3, 60, messages,
                                           max_tokens=300, api_key=hcfg.api_key)
                if not more:
                    break
                summary = (summary.rstrip() + " " + more.strip()).strip()


            summary = re.sub(r"\*+", "", summary)
            summary = re.sub(r"#+\s*", "", summary)
            summary = re.sub(r"\n{3,}", "\n\n", summary).strip()


            if _looks_truncated(summary):
                log("  ⚠️  Summary still looks truncated — trimming to last complete sentence.")
                for end_char in [".", "!", "?"]:
                    last = summary.rfind(end_char)
                    if last != -1:
                        summary = summary[:last + 1].strip()
                        break


            if not summary:
                raise ValueError("Empty LLM response")


            log(f"  ✅ Summary paragraph generated ({len(summary)} chars).")
            return summary


        except Exception as e:
            log(f"  ⚠️  Qwen call failed ({e}) — using fallback summary.")
            return fallback


    def _t5_build_referrer_body(self, pdf: str, appt: Dict, provider: str, log) -> str:
        """Legacy compatibility wrapper — assembles full body from generated summary."""
        summary = self._t5_generate_summary_paragraph(pdf, appt, provider, log)
        provider_salutation = provider.strip() if provider else "Doctor"
        from_name = self.smtp_conf.get("from_name", "Noll Psych Group")
        return (
            f"Dear {provider_salutation},\n\n"
            f"{summary}\n\n"
            "The full report is attached for your records. "
            "Please do not hesitate to contact our office if you have any questions.\n\n"
            f"Sincerely,\n{from_name}"
        )


    @staticmethod
    def _t5_extract_summary_section(full_text: str, max_chars: int = 5000) -> str:
        patterns = [
            r"(?is)(diagnostic\s+impression[s]?.{0,6000})",
            r"(?is)(impression[s]?\s*\n.{0,6000})",
            r"(?is)(summary\s+and\s+(?:conclusion[s]?|recommendation[s]?).{0,6000})",
            r"(?is)(recommendation[s]?\s*\n.{0,6000})",
            r"(?is)(conclusion[s]?\s*\n.{0,6000})",
        ]
        for pat in patterns:
            m = re.search(pat, full_text)
            if m:
                return m.group(1)[:max_chars]
        return full_text[max(0, len(full_text) - max_chars):]


    # ==================================================================
    # ── TAB 6: SUPERBILL ──────────────────────────────────────────────
    # ==================================================================


    _SB_CHARGES_STANDARD = [
        (90791, "Diagnostic Interview",                      1, 165),
        (96132, "Psychological Testing (initial unit)",      1, 150),
        (96133, "Psych Testing (additional units)",          6, 100),
    ]
    _SB_CHARGES_SELFPAY_STANDARD = [
        (90791, "Diagnostic Interview",                      1, 149),
        (96132, "Psychological Testing (initial unit)",      1, 100),
        (96133, "Psych Testing (additional units)",          2, 100),
    ]
    _SB_CHARGES_SELFPAY_COURT = [
        (90791, "Diagnostic Interview",                      1, 150),
        (96132, "Psychological Testing (initial unit)",      1, 100),
        (96133, "Psych Testing (additional units)",          5, 100),
    ]


    def _build_tab6_superbill(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="  Superbill  ")


        today = dt.date.today().strftime("%Y-%m-%d")


        log_frame = ttk.LabelFrame(tab, text="Log", padding=4)
        log_frame.pack(side="bottom", fill="both", expand=True, padx=8, pady=(0, 4))
        self.t6_log_text = tk.Text(log_frame, wrap="word", height=5, font=("Consolas", 9))
        sb6 = ttk.Scrollbar(log_frame, command=self.t6_log_text.yview)
        self.t6_log_text.configure(yscrollcommand=sb6.set)
        sb6.pack(side="right", fill="y")
        self.t6_log_text.pack(fill="both", expand=True)


        act_row = ttk.Frame(tab)
        act_row.pack(side="bottom", fill="x", padx=8, pady=4)
        ttk.Button(act_row, text="📄  Generate Superbill PDF",
                   command=self._t6_generate).pack(side="left", padx=4)
        ttk.Button(act_row, text="✉  Email Superbill to Patient",
                   command=self._t6_email_patient).pack(side="left", padx=4)
        ttk.Button(act_row, text="Clear",
                   command=self._t6_clear).pack(side="left", padx=4)


        out_frame = ttk.LabelFrame(tab, text="Output", padding=6)
        out_frame.pack(side="bottom", fill="x", padx=8, pady=(0, 2))
        self.t6_out_dir = tk.StringVar(value=self.patients_root)
        ttk.Label(out_frame, text="Save to:").grid(row=0, column=0, sticky="w")
        ttk.Entry(out_frame, textvariable=self.t6_out_dir, width=64).grid(row=0, column=1, padx=6, sticky="w")
        ttk.Button(out_frame, text="Browse…",
                   command=self._t6_browse_out).grid(row=0, column=2, padx=4)


        self.t6_last_pdf: Optional[str] = None


        top_canvas = tk.Canvas(tab, borderwidth=0, highlightthickness=0)
        top_vsb    = ttk.Scrollbar(tab, orient="vertical", command=top_canvas.yview)
        top_canvas.configure(yscrollcommand=top_vsb.set)
        top_inner  = ttk.Frame(top_canvas)
        top_inner.bind("<Configure>",
            lambda e: top_canvas.configure(scrollregion=top_canvas.bbox("all")))
        top_canvas.create_window((0, 0), window=top_inner, anchor="nw")
        top_vsb.pack(side="right", fill="y")
        top_canvas.pack(side="top", fill="both", expand=True)


        def _mw(e): top_canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        top_canvas.bind("<MouseWheel>", _mw)
        top_inner.bind("<MouseWheel>", _mw)


        fa_frame = ttk.LabelFrame(top_inner, text="Appointments", padding=6)
        fa_frame.pack(fill="x", padx=8, pady=(6, 3))


        fa_top = ttk.Frame(fa_frame)
        fa_top.pack(fill="x")
        self.t6_fa_start = tk.StringVar(value=today)
        self.t6_fa_end   = tk.StringVar(value=today)
        ttk.Label(fa_top, text="Start:").pack(side="left")
        ttk.Entry(fa_top, textvariable=self.t6_fa_start, width=13).pack(side="left", padx=4)
        ttk.Label(fa_top, text="End:").pack(side="left")
        ttk.Entry(fa_top, textvariable=self.t6_fa_end, width=13).pack(side="left", padx=4)
        ttk.Button(fa_top, text="Fetch Appointments",
                   command=self._t6_fetch_appts).pack(side="left", padx=8)
        ttk.Label(fa_top, text="← Click a row to populate Patient Name & Email",
                  foreground="gray").pack(side="left", padx=4)


        canvas_wrap = ttk.Frame(fa_frame)
        canvas_wrap.pack(fill="x", pady=(4, 0))
        self.t6_appt_canvas = tk.Canvas(canvas_wrap, height=90, borderwidth=0, highlightthickness=0)
        fa_vsb = ttk.Scrollbar(canvas_wrap, orient="vertical", command=self.t6_appt_canvas.yview)
        self.t6_appt_canvas.configure(yscrollcommand=fa_vsb.set)
        self.t6_appt_inner = ttk.Frame(self.t6_appt_canvas)
        self.t6_appt_inner.bind("<Configure>",
            lambda e: self.t6_appt_canvas.configure(
                scrollregion=self.t6_appt_canvas.bbox("all")))
        self.t6_appt_canvas.create_window((0, 0), window=self.t6_appt_inner, anchor="nw")
        self.t6_appt_canvas.pack(side="left", fill="both", expand=True)
        fa_vsb.pack(side="right", fill="y")
        self.t6_appts_data: List[Dict] = []
        self.t6_appt_rows:  List[Dict] = []


        ctrl = ttk.LabelFrame(top_inner, text="Patient", padding=6)
        ctrl.pack(fill="x", padx=8, pady=3)
        ttk.Label(ctrl, text="Patient Name:").grid(row=0, column=0, sticky="w")
        self.t6_patient = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self.t6_patient, width=38).grid(row=0, column=1, padx=6, sticky="w")
        ttk.Label(ctrl, text="Patient Email:").grid(row=0, column=2, sticky="w", padx=(12, 0))
        self.t6_email = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self.t6_email, width=36).grid(row=0, column=3, padx=6, sticky="w")


        bd_row = ttk.Frame(top_inner)
        bd_row.pack(fill="x", padx=8, pady=3)


        bt_frame = ttk.LabelFrame(bd_row, text="Billing Type", padding=6)
        bt_frame.pack(side="left", fill="x", expand=True)
        self.t6_billing_type = tk.StringVar(value="standard")
        ttk.Radiobutton(bt_frame, text="Standard / Insurance / Medicare",
                        variable=self.t6_billing_type, value="standard",
                        command=self._t6_update_charges_preview).pack(side="left", padx=6)
        ttk.Radiobutton(bt_frame, text="Self-Pay — Standard (49)",
                        variable=self.t6_billing_type, value="selfpay_standard",
                        command=self._t6_update_charges_preview).pack(side="left", padx=6)
        ttk.Radiobutton(bt_frame, text="Self-Pay — Court / Disability (50)",
                        variable=self.t6_billing_type, value="selfpay_court",
                        command=self._t6_update_charges_preview).pack(side="left", padx=6)


        dos_frame = ttk.LabelFrame(bd_row, text="Date of Service", padding=6)
        dos_frame.pack(side="left", padx=(6, 0))
        self.t6_dos = tk.StringVar(value=today)
        ttk.Label(dos_frame, text="Date:").pack(side="left")
        ttk.Entry(dos_frame, textvariable=self.t6_dos, width=13).pack(side="left", padx=4)


        dx_outer = ttk.LabelFrame(top_inner, text="ICD-10 Diagnoses", padding=6)
        dx_outer.pack(fill="x", padx=8, pady=3)


        dx_btn_row = ttk.Frame(dx_outer)
        dx_btn_row.pack(fill="x", pady=(0, 4))
        ttk.Button(dx_btn_row, text="🔍  Infer from Report PDF",
                   command=self._t6_infer_diagnoses).pack(side="left", padx=4)
        ttk.Button(dx_btn_row, text="+ Add Row",
                   command=self._t6_add_dx_row).pack(side="left", padx=4)
        ttk.Button(dx_btn_row, text="Clear All",
                   command=self._t6_clear_dx_rows).pack(side="left", padx=4)
        ttk.Label(dx_btn_row, text="Infer reads the report PDF and calls Qwen to suggest codes.",
                  foreground="gray").pack(side="left", padx=8)


        hdr = ttk.Frame(dx_outer)
        hdr.pack(fill="x")
        ttk.Label(hdr, text="#",    width=3,  anchor="w", font=("Segoe UI", 8, "bold")).grid(row=0, column=0, padx=2)
        ttk.Label(hdr, text="ICD-10 Code / Description (editable)", width=42,
                  anchor="w", font=("Segoe UI", 8, "bold")).grid(row=0, column=1, padx=4)
        ttk.Label(hdr, text="Override from favorites ↓", width=38,
                  anchor="w", font=("Segoe UI", 8, "bold")).grid(row=0, column=2, padx=4)


        dx_canvas_wrap = ttk.Frame(dx_outer)
        dx_canvas_wrap.pack(fill="x", pady=(2, 0))
        self.t6_dx_canvas = tk.Canvas(dx_canvas_wrap, height=90, borderwidth=0, highlightthickness=0)
        dx_vsb = ttk.Scrollbar(dx_canvas_wrap, orient="vertical", command=self.t6_dx_canvas.yview)
        self.t6_dx_canvas.configure(yscrollcommand=dx_vsb.set)
        self.t6_dx_inner = ttk.Frame(self.t6_dx_canvas)
        self.t6_dx_inner.bind("<Configure>",
            lambda e: self.t6_dx_canvas.configure(
                scrollregion=self.t6_dx_canvas.bbox("all")))
        self.t6_dx_canvas.create_window((0, 0), window=self.t6_dx_inner, anchor="nw")
        self.t6_dx_canvas.pack(side="left", fill="both", expand=True)
        dx_vsb.pack(side="right", fill="y")


        self.t6_dx_rows: List[Dict] = []
        self._t6_icd_options: List[str] = load_icd_codes(lambda _: None)
        self._t6_add_dx_row(initial_value="F33.2 - Major depressive disorder, recurrent, severe")


        prev_frame = ttk.LabelFrame(top_inner, text="Charges Preview", padding=6)
        prev_frame.pack(fill="x", padx=8, pady=3)
        self.t6_charges_preview = tk.Text(prev_frame, height=5, state="disabled",
                                           font=("Consolas", 9), wrap="none")
        prev_sb = ttk.Scrollbar(prev_frame, command=self.t6_charges_preview.yview)
        self.t6_charges_preview.configure(yscrollcommand=prev_sb.set)
        prev_sb.pack(side="right", fill="y")
        self.t6_charges_preview.pack(fill="x")
        self._t6_update_charges_preview()


    def _t6_log(self, msg: str):
        self.t6_log_text.insert("end", msg + "\n")
        self.t6_log_text.see("end")
        self.t6_log_text.update_idletasks()


    def _t6_clear(self):
        self.t6_patient.set("")
        self.t6_email.set("")
        self.t6_log_text.delete("1.0", "end")
        self._t6_clear_appt_rows()
        self._t6_clear_dx_rows()
        self._t6_add_dx_row(initial_value="F33.2 - Major depressive disorder, recurrent, severe")
        self.t6_last_pdf = None


    def _t6_clear_appt_rows(self):
        for r in self.t6_appt_rows:
            r["frame"].destroy()
        self.t6_appt_rows.clear()
        self.t6_appts_data.clear()


    def _t6_browse_out(self):
        d = filedialog.askdirectory(title="Select output root folder")
        if d:
            self.t6_out_dir.set(d)


    def _t6_update_charges_preview(self):
        btype = self.t6_billing_type.get()
        if btype == "selfpay_standard":
            rows = self._SB_CHARGES_SELFPAY_STANDARD
        elif btype == "selfpay_court":
            rows = self._SB_CHARGES_SELFPAY_COURT
        else:
            rows = self._SB_CHARGES_STANDARD
        total = sum(r[2] * r[3] for r in rows)
        lines = [f"{'CPT':<8}{'Description':<42}{'Units':>5}{'Charge':>8}{'Total':>8}"]
        lines.append("-" * 71)
        for cpt, desc, units, charge in rows:
            lines.append(f"{cpt:<8}{desc:<42}{units:>5}{charge:>8}{units*charge:>8}")
        lines.append("-" * 71)
        lines.append(f"{'':50}{'Grand Total:':>13}{total:>8}")
        self.t6_charges_preview.configure(state="normal")
        self.t6_charges_preview.delete("1.0", "end")
        self.t6_charges_preview.insert("end", "\n".join(lines))
        self.t6_charges_preview.configure(state="disabled")


    def _t6_fetch_appts(self):
        self.t6_log_text.delete("1.0", "end")
        threading.Thread(target=self._t6_fetch_appts_worker, daemon=True).start()


    def _t6_fetch_appts_worker(self):
        log = self._t6_log
        try:
            self._init_google(log)
            cfg    = self.cfg
            cal_id = resolve_calendar_id(cfg)
            tz_str = cfg.get("calendar_timezone", "America/Chicago")
            start  = dt.datetime.fromisoformat(self.t6_fa_start.get()).date()
            end    = dt.datetime.fromisoformat(self.t6_fa_end.get()).date()
            events = fetch_calendar_events(self._calendar, cal_id, start, end, tz_str, log)
            owner  = cfg.get("calendar_owner_email", "")


            appts: List[Dict] = []
            for ev in events:
                email = extract_patient_email_from_event(ev, owner)
                if not email:
                    continue
                name    = extract_patient_name_tc(ev, email, owner)
                start_s = event_start_str(ev)
                label_dt = ""
                try:
                    label_dt = dt.datetime.fromisoformat(
                        start_s.replace("Z", "+00:00")).astimezone().strftime("%m/%d/%Y  %I:%M %p")
                except Exception:
                    label_dt = start_s[:16]
                appts.append({"name": name, "email": email,
                               "start_str": start_s, "label": label_dt})


            def _populate():
                self.after(0, self._t6_clear_appt_rows)
                time.sleep(0.05)
                for a in appts:
                    self.after(0, lambda appt=a: self._t6_add_appt_row(appt))
                self.after(0, lambda: log(f"✅ {len(appts)} appointment(s) loaded — click a row to select."))


            _populate()
        except Exception as e:
            log(f"❌ Fetch Appointments error: {e}\n{traceback.format_exc()}")


    def _t6_add_appt_row(self, appt: Dict):
        self.t6_appts_data.append(appt)
        idx = len(self.t6_appt_rows)


        frame = ttk.Frame(self.t6_appt_inner, relief="flat", cursor="hand2")
        frame.grid(row=idx, column=0, sticky="ew", pady=1, padx=2)


        bg = "#EEF4FB" if idx % 2 == 0 else "#FFFFFF"


        lbl_dt   = tk.Label(frame, text=appt["label"], width=20, anchor="w",
                             font=("Segoe UI", 9), bg=bg)
        lbl_name = tk.Label(frame, text=appt["name"], width=28, anchor="w",
                             font=("Segoe UI", 9), bg=bg)
        lbl_mail = tk.Label(frame, text=appt["email"], width=34, anchor="w",
                             font=("Segoe UI", 9), fg="#555555", bg=bg)


        lbl_dt.grid(row=0, column=0, padx=(4, 6), pady=2)
        lbl_name.grid(row=0, column=1, padx=4, pady=2)
        lbl_mail.grid(row=0, column=2, padx=4, pady=2)


        def _select(a=appt, f=frame):
            for r in self.t6_appt_rows:
                for child in r["frame"].winfo_children():
                    child.configure(bg="#FFFFFF" if self.t6_appt_rows.index(r) % 2 else "#EEF4FB")
            for child in f.winfo_children():
                child.configure(bg="#C8DCF5")
            self.t6_patient.set(a["name"])
            self.t6_email.set(a["email"])
            try:
                d = dt.datetime.fromisoformat(a["start_str"].replace("Z", "+00:00")).date()
                self.t6_dos.set(d.strftime("%Y-%m-%d"))
            except Exception:
                pass


        for w in (frame, lbl_dt, lbl_name, lbl_mail):
            w.bind("<Button-1>", lambda e, fn=_select: fn())


        self.t6_appt_rows.append({"frame": frame, "appt": appt})


    def _t6_appt_selected(self, _event=None):
        pass


    def _t6_add_dx_row(self, initial_value: str = ""):
        idx = len(self.t6_dx_rows)
        frame = ttk.Frame(self.t6_dx_inner)
        frame.grid(row=idx, column=0, sticky="ew", pady=1, padx=2)


        ttk.Label(frame, text=str(idx + 1), width=3).grid(row=0, column=0, padx=2)


        code_var = tk.StringVar(value=initial_value)
        entry = ttk.Entry(frame, textvariable=code_var, width=44)
        entry.grid(row=0, column=1, padx=4)


        override_var = tk.StringVar()
        combo = ttk.Combobox(frame, textvariable=override_var, width=40, state="readonly",
                             values=self._t6_icd_options)
        combo.grid(row=0, column=2, padx=4)


        def _apply_override(*_):
            chosen = override_var.get()
            if chosen:
                code_var.set(chosen)


        combo.bind("<<ComboboxSelected>>", _apply_override)


        def _remove(f=frame, row_dict=None):
            f.destroy()
            if row_dict in self.t6_dx_rows:
                self.t6_dx_rows.remove(row_dict)
            self._t6_renumber_dx_rows()


        row_dict: Dict = {"frame": frame, "code_var": code_var, "override_var": override_var}
        row_dict["remove_fn"] = lambda rd=row_dict: _remove(frame, rd)
        ttk.Button(frame, text="✕", width=2,
                   command=row_dict["remove_fn"]).grid(row=0, column=3, padx=2)


        self.t6_dx_rows.append(row_dict)


    def _t6_renumber_dx_rows(self):
        for i, r in enumerate(self.t6_dx_rows):
            r["frame"].grid(row=i, column=0, sticky="ew", pady=1, padx=2)


    def _t6_clear_dx_rows(self):
        for r in self.t6_dx_rows:
            r["frame"].destroy()
        self.t6_dx_rows.clear()


    def _t6_set_dx_codes(self, codes: List[str]):
        self._t6_clear_dx_rows()
        for c in codes:
            self._t6_add_dx_row(initial_value=c)
        if not codes:
            self._t6_add_dx_row()


    def _t6_get_dx_codes(self) -> List[str]:
        return [r["code_var"].get().strip() for r in self.t6_dx_rows
                if r["code_var"].get().strip()]


    def _t6_infer_diagnoses(self):
        name = self.t6_patient.get().strip()
        if not name:
            messagebox.showerror("No patient", "Select or enter a patient name first.")
            return
        threading.Thread(target=self._t6_infer_worker, args=(name,), daemon=True).start()


    def _t6_infer_worker(self, patient_name: str):
        log = self._t6_log
        log(f"\n🔍 Inferring diagnoses from report PDF for: {patient_name}")
        try:
            out_root = self.t6_out_dir.get().strip() or self.patients_root
            pdf_path, err = find_report_pdf(out_root, patient_name)
            if not pdf_path:
                pdf_path, err = find_report_pdf(self.patients_root, patient_name)
            if not pdf_path:
                log(f"❌ Report PDF not found: {err}")
                log("   Tip: ensure the report PDF is in the patient's folder.")
                return


            log(f"  Found report: {os.path.basename(pdf_path)}")


            if PdfReader is None:
                log("❌ pypdf not installed — cannot read PDF.")
                return
            try:
                reader = PdfReader(pdf_path)
                pages_text = []
                for page in reader.pages:
                    try:
                        pages_text.append(page.extract_text() or "")
                    except Exception:
                        pass
                report_text = "\n".join(pages_text).strip()
            except Exception as e:
                log(f"❌ Could not read PDF: {e}")
                return


            if not report_text:
                log("❌ No text could be extracted from the PDF.")
                return


            log(f"  Extracted {len(report_text):,} characters from {len(reader.pages)} page(s).")


            extract = self._t6_extract_diagnostic_section(report_text)
            log(f"  Sending {len(extract):,} chars to Qwen for diagnosis inference…")


            icd_list = "\n".join(f"  {c}" for c in self._t6_icd_options[:60])


            system_prompt = (
                "You are a clinical assistant helping a neuropsychologist write a brief, "
            "professional email to a referring provider.\n\n"
            "Write exactly ONE paragraph — no bullet points, no numbered lists, no markdown "
            "formatting, no bold or italic text, no headers. Plain prose only.\n\n"
            "The paragraph should:\n"
            "  1. Thank the provider for the referral.\n"
            "  2. Mention the patient's name and the date of the telemedicine evaluation.\n"
            "  3. Briefly state the primary diagnoses reached.\n"
            "  4. Provide a concise summary of the key clinical recommendations.\n\n"
            "Important constraints:\n"
            "  - Do NOT suggest or recommend any follow-up appointments. "
            "This practice does not schedule follow-up visits.\n"
            "  - Do NOT advise the referring provider on when or how to schedule "
            "follow-up care for their patient. That is entirely at the provider's discretion.\n\n"
            "The paragraph should read naturally and professionally, as if written by "
            "the evaluating psychologist. Do not include any salutation or sign-off — "
            "only the paragraph itself."
            )


            user_msg = (
                f"Report excerpt for {patient_name}:\n\n"
                f"{extract}\n\n"
                "Please identify the appropriate ICD-10 diagnostic codes for this patient's superbill."
            )


            hcfg = load_qwen_config(self.rcfg)
            t2_key = self.t2_webui_key.get().strip() if hasattr(self, "t2_webui_key") else ""
            if t2_key:
                hcfg.api_key = t2_key


            url = hcfg.base_url.rstrip("/") + hcfg.api_path
            log(f"  Qwen URL: {url}")
            log(f"  Model: {hcfg.model}")
            log(f"  API key: {'set (' + str(len(hcfg.api_key)) + ' chars)' if hcfg.api_key else '⚠️  NOT SET'}")


            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_msg},
            ]
            raw, finish = _webui_call(url, hcfg.model, 0.1, 60, messages,
                                      max_tokens=512, api_key=hcfg.api_key)
            log(f"  Response length: {len(raw)} chars  |  finish_reason: {finish}")
            if not raw:
                log("⚠️  Empty response from Qwen — check URL, model name, and API key.")
                return


            codes = self._t6_parse_dx_response(raw, log)
            if not codes:
                log("⚠️  Could not parse a valid diagnosis list from the LLM response.")
                log(f"   Raw response: {raw[:300]}")
                return


            log(f"✅ {len(codes)} diagnosis code(s) inferred:")
            for c in codes:
                log(f"   • {c}")


            self.after(0, lambda c=codes: self._t6_set_dx_codes(c))


        except Exception as e:
            log(f"❌ Inference error: {e}\n{traceback.format_exc()}")


    @staticmethod
    def _t6_extract_diagnostic_section(full_text: str, max_chars: int = 6000) -> str:
        patterns = [
            r"(?is)(diagnostic\s+impression[s]?.{0,8000})",
            r"(?is)(impression[s]?\s*\n.{0,8000})",
            r"(?is)(summary\s+and\s+conclusion[s]?.{0,8000})",
            r"(?is)(conclusion[s]?\s*\n.{0,8000})",
            r"(?is)(diagnos[ei][s]?\s*\n.{0,8000})",
            r"(?is)(recommendation[s]?.{0,8000})",
        ]
        for pat in patterns:
            m = re.search(pat, full_text)
            if m:
                return m.group(1)[:max_chars]
        start = max(0, len(full_text) - max_chars)
        return full_text[start:]


    @staticmethod
    def _t6_parse_dx_response(raw: str, log) -> List[str]:
        raw = raw.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
        raw = raw.strip()
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except json.JSONDecodeError:
            pass
        m = re.search(r"\[.*?\]", raw, re.DOTALL)
        if m:
            try:
                parsed = json.loads(m.group(0))
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
        codes = re.findall(r'"([A-Z]\d+[\d.]*\s*[-–]\s*[^"]+)"', raw)
        return [c.strip() for c in codes if c.strip()]


    def _t6_generate(self):
        name = self.t6_patient.get().strip()
        if not name:
            messagebox.showerror("Input error", "Enter or select a patient name.")
            return
        threading.Thread(target=self._t6_generate_worker, daemon=True).start()


    def _t6_generate_worker(self):
        log = self._t6_log
        try:
            if not REPORTLAB_OK:
                log("❌ reportlab is not installed. Run: pip install reportlab")
                return


            self._init_google(log)


            patient_name  = self.t6_patient.get().strip()
            patient_email = self.t6_email.get().strip()
            billing_type  = self.t6_billing_type.get()
            dos_str       = self.t6_dos.get().strip()
            dx_codes      = self._t6_get_dx_codes()
            out_root      = self.t6_out_dir.get().strip() or self.patients_root


            if not dx_codes:
                dx_codes = ["F33.2 - Major depressive disorder, recurrent, severe"]


            try:
                dos_date = dt.datetime.strptime(dos_str, "%Y-%m-%d").date()
            except Exception:
                dos_date = dt.date.today()


            if billing_type == "selfpay_standard":
                charges = self._SB_CHARGES_SELFPAY_STANDARD
            elif billing_type == "selfpay_court":
                charges = self._SB_CHARGES_SELFPAY_COURT
            else:
                charges = self._SB_CHARGES_STANDARD


            log(f"Loading patient data for: {patient_name}")
            pdata = self._t6_resolve_patient_data(patient_name, patient_email, log)


            patient_folder = ensure_patient_folder(out_root, patient_name)
            safe_name = re.sub(r"[^\w\s\-]", "", patient_name).strip().replace(" ", "_")
            pdf_name  = f"Superbill_{safe_name}_{dos_date.strftime('%Y%m%d')}.pdf"
            pdf_path  = os.path.join(patient_folder, pdf_name)


            log(f"Generating PDF: {pdf_path}")
            self._t6_build_pdf(pdf_path, patient_name, pdata, dos_date, dx_codes, charges, billing_type)
            self.t6_last_pdf = pdf_path
            log(f"✅ Superbill saved: {pdf_path}")


            self.after(0, lambda: open_file_os(pdf_path))


        except Exception as e:
            log(f"❌ {e}\n{traceback.format_exc()}")


    def _t6_email_patient(self):
        email = self.t6_email.get().strip()
        name  = self.t6_patient.get().strip()


        self._t6_log("─── Email Superbill ───")


        if not email or "@" not in email:
            self._t6_log("❌ No patient email address — enter or select one first.")
            messagebox.showerror("No email", "Enter or select a patient email address first.")
            return


        smtp_host = (self.smtp_conf or {}).get("host", "")
        smtp_user = (self.smtp_conf or {}).get("username", "")
        if not smtp_host or not smtp_user:
            self._t6_log("❌ SMTP not configured (host/username missing in config.json).")
            messagebox.showerror(
                "SMTP not configured",
                "SMTP settings (host / username) are missing in config.json.\n"
                "Check the 'smtp' section of your config.")
            return


        self._t6_log(f"   To: {email}")


        pdf_path = self.t6_last_pdf if self.t6_last_pdf and os.path.exists(self.t6_last_pdf) else None
        if not pdf_path:
            self._t6_log("   No recent PDF in memory — searching patient folder…")
            pdf_path = self._t6_find_latest_superbill(name)


        if not pdf_path:
            self._t6_log(f"❌ No Superbill PDF found for {name!r}.")
            if messagebox.askyesno(
                    "No Superbill found",
                    f"No Superbill PDF found for {name!r}.\n\n"
                    "Generate one now, then click Email again to send."):
                self._t6_generate()
            return


        self._t6_log(f"   PDF: {os.path.basename(pdf_path)}")
        threading.Thread(
            target=self._t6_do_email_patient,
            args=(email, name, pdf_path),
            daemon=True,
        ).start()


    def _t6_find_latest_superbill(self, patient_name: str) -> Optional[str]:
        out_root = (self.t6_out_dir.get().strip()
                    if hasattr(self, "t6_out_dir") else "") or self.patients_root
        for root in [out_root, self.patients_root]:
            if not patient_name or not root:
                continue
            folder = os.path.join(root, patient_name)
            if os.path.isdir(folder):
                matches = glob.glob(os.path.join(folder, "Superbill_*.pdf"))
                if matches:
                    return max(matches, key=os.path.getmtime)
        return None


    def _t6_do_email_patient(self, email: str, patient_name: str, pdf_path: str):
        log = self._t6_log
        log(f"Connecting to SMTP ({self.smtp_conf.get('host','?')})…")
        subject = f"Superbill — {patient_name}"
        body = (
            f"Dear {patient_name.split()[0] if patient_name else 'Patient'},\n\n"
            "Please find your Superbill attached. You may submit this document "
            "to your insurance company for reimbursement.\n\n"
            "If you have any questions, please don't hesitate to contact our office.\n\n"
            f"Thank you,\n{self.smtp_conf.get('from_name', 'Noll Psych Group')}"
        )
        ok = send_smtp(
            self.smtp_conf,
            [email],
            subject=subject,
            body=body,
            attachments=[pdf_path],
            log=log,
        )
        if ok:
            self.after(0, lambda: messagebox.showinfo(
                "Sent", f"Superbill emailed successfully to {email}."))


    def _t6_resolve_patient_data(self, patient_name: str, patient_email: str, log) -> Dict[str, str]:
        ins_conf = self.cfg.get("insurance_form") or {}
        sheet_id = ins_conf.get("google_sheet_id") or ins_conf.get("sheet_id", "")


        data: Dict[str, str] = {}


        if sheet_id and patient_email:
            try:
                row_dict = fetch_insurance_row(self._gspread, ins_conf, patient_email, log)
                key_map = {
                    "patient's first name":  "first_name",
                    "patient's last name":   "last_name",
                    "street address":        "address_street",
                    "city":                  "address_city",
                    "state":                 "address_state",
                    "zip code":              "address_zip",
                    "patient's date of birth": "dob",
                    "telephone number":      "phone",
                    "insured's first and last name (if different than patient)": "subscriber",
                    "insurance carrier":     "insurance_carrier",
                    "insurance id number":   "insurance_id",
                }
                for raw_key, mapped in key_map.items():
                    for k, v in row_dict.items():
                        if k.strip().lower() == raw_key:
                            data[mapped] = str(v or "").strip()
                            break
                log(f"✅ Insurance form data loaded for {patient_email}")
            except Exception as e:
                log(f"⚠️  Could not load insurance form data: {e} — using name/email only.")


        if not data.get("first_name") and patient_name:
            parts = patient_name.strip().split()
            data["first_name"] = parts[0] if parts else patient_name
            data["last_name"]  = parts[-1] if len(parts) > 1 else ""


        return data


    @staticmethod
    def _t6_build_pdf(pdf_path: str, patient_name: str, pdata: Dict[str, str],
                      dos_date: dt.date, dx_codes: List[str], charges: list, billing_type: str):
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )
        styles = getSampleStyleSheet()
        story  = []


        def _h(text, size=12, bold=True, space_before=6, space_after=2):
            st = ParagraphStyle("_h", parent=styles["Normal"],
                                fontSize=size, fontName="Helvetica-Bold" if bold else "Helvetica",
                                spaceBefore=space_before, spaceAfter=space_after)
            return Paragraph(text, st)


        def _p(text, size=10, indent=0, space_after=2):
            st = ParagraphStyle("_p", parent=styles["Normal"],
                                fontSize=size, fontName="Helvetica",
                                leftIndent=indent, spaceAfter=space_after)
            return Paragraph(text, st)


        def _label_val(label, value, label_width=130):
            tbl = Table([[_p(f"<b>{label}</b>", size=9), _p(str(value or ""), size=9)]],
                        colWidths=[label_width, 5.5 * inch - label_width])
            tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            return tbl


        story.append(_h("Neuropsychological Services", size=14, space_before=0))
        story.append(HRFlowable(width="100%", thickness=1,
                                color=rl_colors.black, spaceAfter=6))


        story.append(_h("Provider Information", size=11, space_before=4, space_after=2))
        prov_data = [
            ["Provider:", "Nicholas Noll, Ph.D."],
            ["", "NPI 1407854292"],
            ["Group:", "Noll Psychological Group Inc."],
            ["", "NPI 1083612865"],
            ["", "EIN 76-0741162"],
            ["Address:", "15515 N. Mount Olivet Road"],
            ["", "Smithville, MO 64089"],
            ["Phone:", "816-835-9882"],
        ]
        for label, val in prov_data:
            story.append(_label_val(label, val))


        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=rl_colors.grey, spaceAfter=6))


        story.append(_h("Patient Information", size=11, space_before=4, space_after=2))


        first   = pdata.get("first_name", "")
        last    = pdata.get("last_name", "")
        dob     = pdata.get("dob", "")
        street  = pdata.get("address_street", "")
        city    = pdata.get("address_city", "")
        state   = pdata.get("address_state", "")
        zipcode = pdata.get("address_zip", "")
        phone   = pdata.get("phone", "")
        subscriber    = pdata.get("subscriber", "Subscriber")
        ins_carrier   = pdata.get("insurance_carrier", "")
        ins_id        = pdata.get("insurance_id", "")


        addr_line2 = " ".join(filter(None, [city, state, str(zipcode)]))


        story.append(_label_val("Patient First Name:", first))
        story.append(_label_val("Patient Last Name:", last))
        story.append(_label_val("Date of Birth:", dob))
        story.append(_label_val("Address:", street))
        if addr_line2:
            story.append(_label_val("", addr_line2))
        story.append(_label_val("Phone:", phone))
        story.append(_label_val("Responsible Party:", "Subscriber"))
        story.append(_label_val("Ins. Subscriber:", subscriber))


        if billing_type == "standard":
            story.append(_label_val("Insurance Carrier:", ins_carrier))
            story.append(_label_val("Insurance ID:", ins_id))
        else:
            label_text = "Self-Pay — Standard" if billing_type == "selfpay_standard" else "Self-Pay — Court/Disability"
            story.append(_label_val("Billing Type:", label_text))


        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=rl_colors.grey, spaceAfter=6))


        story.append(_h("ICD-10 Diagnoses", size=11, space_before=4, space_after=2))
        if not dx_codes:
            dx_codes = ["(no diagnosis specified)"]
        for i, code in enumerate(dx_codes):
            label = "Primary Diagnosis:" if i == 0 else f"Diagnosis {i + 1}:"
            story.append(_label_val(label, code))


        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=rl_colors.grey, spaceAfter=8))


        story.append(_h("Charges", size=11, space_before=4, space_after=6))


        dos_display = dos_date.strftime("%m/%d/%Y")
        col_widths  = [1.1 * inch, 0.85 * inch, 2.8 * inch, 0.55 * inch, 0.7 * inch, 0.7 * inch]


        header_style = ParagraphStyle("ch", parent=styles["Normal"],
                                      fontSize=9, fontName="Helvetica-Bold",
                                      textColor=rl_colors.white)
        cell_style   = ParagraphStyle("cc", parent=styles["Normal"],
                                      fontSize=9, fontName="Helvetica")


        tbl_data = [[
            Paragraph("Date", header_style),
            Paragraph("CPT Code", header_style),
            Paragraph("Description", header_style),
            Paragraph("Units", header_style),
            Paragraph("Charge", header_style),
            Paragraph("Total", header_style),
        ]]


        grand_total = 0
        for cpt, desc, units, unit_charge in charges:
            row_total = units * unit_charge
            grand_total += row_total
            tbl_data.append([
                Paragraph(dos_display, cell_style),
                Paragraph(str(cpt), cell_style),
                Paragraph(desc, cell_style),
                Paragraph(str(units), cell_style),
                Paragraph(f"${unit_charge:,}", cell_style),
                Paragraph(f"${row_total:,}", cell_style),
            ])


        empty = Paragraph("", cell_style)
        bold9 = ParagraphStyle("b9", parent=styles["Normal"], fontSize=9, fontName="Helvetica-Bold")
        tbl_data.append([empty, empty, empty, empty,
                         Paragraph("Total", bold9), Paragraph(f"${grand_total:,}", bold9)])
        tbl_data.append([empty, empty, empty, empty,
                         Paragraph("Paid", bold9), Paragraph("$0", bold9)])
        tbl_data.append([empty, empty, empty, empty,
                         Paragraph("Balance", bold9), Paragraph(f"${grand_total:,}", bold9)])


        tbl = Table(tbl_data, colWidths=col_widths)
        n_data_rows = len(charges)
        tbl_style = TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), rl_colors.HexColor("#2C5F8A")),
            ("TEXTCOLOR",    (0, 0), (-1, 0), rl_colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, n_data_rows),
             [rl_colors.white, rl_colors.HexColor("#F0F4F8")]),
            ("GRID",         (0, 0), (-1, n_data_rows), 0.5, rl_colors.HexColor("#AAAAAA")),
            ("BOX",          (0, 0), (-1, n_data_rows), 0.75, rl_colors.HexColor("#555555")),
            ("LINEABOVE",    (4, n_data_rows + 1), (-1, n_data_rows + 1), 0.5, rl_colors.black),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ("LEFTPADDING",  (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ])
        tbl.setStyle(tbl_style)
        story.append(tbl)


        story.append(Spacer(1, 24))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=rl_colors.grey, spaceAfter=6))
        today_str = dt.date.today().strftime("%m/%d/%Y")
        sig_data = [[
            _p("Nicholas Noll, Ph.D.", size=10),
            _p(f"Date: {today_str}", size=10),
        ]]
        sig_tbl = Table(sig_data, colWidths=[3.5 * inch, 3 * inch])
        sig_tbl.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.append(sig_tbl)


        doc.build(story)




    # ==================================================================
    # ── TAB 7: REPORT EDITOR ──────────────────────────────────────────
    # ==================================================================


    def _build_tab7_report_editor(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="  Report Editor  ")
        self._t7_tab = tab


        # ── Toolbar ───────────────────────────────────────────────────
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill="x", padx=8, pady=(8, 2))


        ttk.Label(toolbar, text="Report Editor",
                  font=("Segoe UI", 10, "bold")).pack(side="left")


        self._t7_status = tk.StringVar(value="No report loaded.")
        ttk.Label(toolbar, textvariable=self._t7_status,
                  foreground="#555555").pack(side="left", padx=14)


        ttk.Button(toolbar, text="Save as PDF",
                   command=self._t7_save_pdf).pack(side="right", padx=4)
        ttk.Button(toolbar, text="Load draft_report.txt",
                   command=self._t7_load_from_file).pack(side="right", padx=4)
        ttk.Button(toolbar, text="Clear",
                   command=self._t7_clear).pack(side="right", padx=4)


        # ── Patient / metadata info bar ───────────────────────────────
        info = ttk.LabelFrame(tab, text="Patient / Report Metadata", padding=6)
        info.pack(fill="x", padx=8, pady=(0, 4))


        ttk.Label(info, text="Patient Name:").grid(row=0, column=0, sticky="w")
        self._t7_name = tk.StringVar()
        ttk.Entry(info, textvariable=self._t7_name, width=30
                  ).grid(row=0, column=1, padx=(2, 12), sticky="w")


        ttk.Label(info, text="DOB:").grid(row=0, column=2, sticky="w")
        self._t7_dob = tk.StringVar()
        ttk.Entry(info, textvariable=self._t7_dob, width=12
                  ).grid(row=0, column=3, padx=(2, 12), sticky="w")


        ttk.Label(info, text="Age:").grid(row=0, column=4, sticky="w")
        self._t7_age = tk.StringVar()
        ttk.Entry(info, textvariable=self._t7_age, width=5
                  ).grid(row=0, column=5, padx=(2, 12), sticky="w")


        ttk.Label(info, text="Eval Date:").grid(row=0, column=6, sticky="w")
        self._t7_eval_date = tk.StringVar()
        ttk.Entry(info, textvariable=self._t7_eval_date, width=12
                  ).grid(row=0, column=7, padx=(2, 0), sticky="w")


        ttk.Label(info, text="Referred By:").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self._t7_referred_by = tk.StringVar()
        ttk.Entry(info, textvariable=self._t7_referred_by, width=68
                  ).grid(row=1, column=1, columnspan=7, padx=(2, 0),
                         sticky="w", pady=(4, 0))


        # ── Text editor ───────────────────────────────────────────────
        editor_frame = ttk.LabelFrame(
            tab, text="Report Text  (Ctrl+S to save PDF)", padding=4)
        editor_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))


        self._t7_text = tk.Text(
            editor_frame,
            wrap="word",
            font=("Consolas", 10),
            undo=True,
            relief="flat",
            borderwidth=1,
            padx=6, pady=6,
        )
        vsb = ttk.Scrollbar(editor_frame, command=self._t7_text.yview)
        self._t7_text.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._t7_text.pack(side="left", fill="both", expand=True)


        self._t7_text.bind("<Control-s>", lambda e: self._t7_save_pdf())


    def _t7_load_from_builder(self, patient_name: str, draft_text: str):
        """Called by Report Builder after generation — populates editor and switches to it."""
        self._t7_name.set(patient_name)
        dob, age, eval_date, referred_by = "", "", "", ""
        for line in draft_text.splitlines():
            ls = line.strip()
            def _after(prefix, s=ls):
                return s[len(prefix):].strip() if s.lower().startswith(prefix.lower()) else None
            v = _after("Referred By:");      referred_by = v if v is not None else referred_by
            v = _after("Date of Birth:");    dob         = v if v is not None else dob
            v = _after("Age:");              age         = v if v is not None else age
            v = _after("Date of Evaluation:"); eval_date = v if v is not None else eval_date


        self._t7_dob.set(dob)
        self._t7_age.set(age)
        self._t7_eval_date.set(eval_date)
        self._t7_referred_by.set(referred_by)


        self._t7_text.delete("1.0", "end")
        self._t7_text.insert("1.0", draft_text)
        self._t7_text.edit_reset()
        self._t7_status.set(f"Draft loaded from Report Builder: {patient_name}")


        try:
            self.nb.select(self.nb.index(self._t7_tab))
        except Exception:
            pass


    def _t7_load_from_file(self):
        name = self._t7_name.get().strip() or self.t2_patient.get().strip()
        initial = os.path.join(self.patients_root, name) if name else self.patients_root
        path = filedialog.askopenfilename(
            title="Select report text file",
            initialdir=initial if os.path.isdir(initial) else self.patients_root,
            filetypes=[("Text files", "*.txt"), ("All files", "*")],
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            self._t7_text.delete("1.0", "end")
            self._t7_text.insert("1.0", text)
            self._t7_text.edit_reset()
            self._t7_status.set(f"Loaded: {path}")
        except Exception as e:
            messagebox.showerror("Load failed", str(e))


    def _t7_clear(self):
        if messagebox.askyesno("Clear editor", "Clear all editor content?"):
            self._t7_text.delete("1.0", "end")
            self._t7_status.set("Editor cleared.")


    def _t7_save_pdf(self):
        if not REPORTLAB_OK:
            messagebox.showerror("Missing library",
                                 "reportlab is not installed. Cannot generate PDF.")
            return
        patient_name = self._t7_name.get().strip()
        if not patient_name:
            messagebox.showwarning("Missing info",
                                   "Enter a patient name in the metadata bar above.")
            return
        report_text = self._t7_text.get("1.0", "end").strip()
        if not report_text:
            messagebox.showwarning("Empty report", "The editor is empty. Nothing to save.")
            return


        # Build final destination path
        safe     = _re_patient_filename(patient_name)
        out_dir  = os.path.join(self.patients_root, patient_name)
        out_path = os.path.join(out_dir, f"{safe}.pdf")


        # Render to a temp file first so we can preview before committing
        import tempfile
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf", prefix="npg_preview_")
        os.close(tmp_fd)


        try:
            generate_report_pdf(
                out_path     = tmp_path,
                report_text  = report_text,
                patient_name = patient_name,
                dob          = self._t7_dob.get().strip(),
                referred_by  = self._t7_referred_by.get().strip(),
                age          = self._t7_age.get().strip(),
                eval_date    = self._t7_eval_date.get().strip(),
            )
        except Exception as exc:
            try: os.unlink(tmp_path)
            except Exception: pass
            messagebox.showerror("Generation failed", f"Could not render PDF:\n\n{exc}")
            return


        self._t7_show_preview(tmp_path, out_path, patient_name)


    def _t7_show_preview(self, tmp_path: str, out_path: str, patient_name: str):
        """Modal window: preview the PDF then approve to save or discard."""
        win = tk.Toplevel(self)
        win.title(f"PDF Preview — {patient_name}")
        win.geometry("640x240")
        win.resizable(False, False)
        win.grab_set()


        ttk.Label(
            win,
            text=f"Report PDF generated for {patient_name}.\n"
                 "Review it in your PDF viewer, then approve to save to the patient "
                 "folder or discard to return to the editor.",
            wraplength=600, justify="left",
        ).pack(padx=16, pady=(18, 8), anchor="w")


        path_frame = ttk.Frame(win)
        path_frame.pack(fill="x", padx=16, pady=(0, 4))
        ttk.Label(path_frame, text="Save to:", width=9, anchor="e").pack(side="left")
        path_var = tk.StringVar(value=out_path)
        ttk.Entry(path_frame, textvariable=path_var, width=62).pack(side="left", padx=4)


        btn_frame = ttk.Frame(win)
        btn_frame.pack(pady=14)


        def _open():
            open_file_os(tmp_path)


        def _approve():
            final = path_var.get().strip()
            if not final:
                messagebox.showwarning("No path", "Enter a destination path.", parent=win)
                return
            try:
                import shutil as _shutil
                os.makedirs(os.path.dirname(final), exist_ok=True)
                _shutil.copy2(tmp_path, final)
                try: os.unlink(tmp_path)
                except Exception: pass
                self._t7_status.set(f"Saved → {final}")
                win.destroy()
                messagebox.showinfo("PDF Saved", f"Report saved successfully:\n\n{final}")
                if self.t1_patient.get().strip() == patient_name:
                    self._t1_refresh_folder()
            except Exception as exc:
                messagebox.showerror("Save failed", str(exc), parent=win)


        def _discard():
            try: os.unlink(tmp_path)
            except Exception: pass
            win.destroy()
            self._t7_status.set("Preview discarded — no file saved.")


        ttk.Button(btn_frame, text="🔍  Open Preview",
                   command=_open).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="✅  Approve & Save",
                   command=_approve).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="✗  Discard",
                   command=_discard).pack(side="left", padx=10)


        _open()




    # ==================================================================
    # ── TAB 8: LETTER GENERATOR ───────────────────────────────────────
    # ==================================================================


    def _build_tab8_letters(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="  Letter Generator  ")
        self._t8_tab = tab


        # ── Appointment fetcher ───────────────────────────────────────
        fa = ttk.LabelFrame(tab, text="Fetch Appointments (click to populate patient)", padding=6)
        fa.pack(fill="x", padx=8, pady=6)


        fa_top = ttk.Frame(fa)
        fa_top.pack(fill="x")
        today = dt.date.today().strftime("%Y-%m-%d")
        self.t8_fa_start = tk.StringVar(value=today)
        self.t8_fa_end   = tk.StringVar(value=today)
        ttk.Label(fa_top, text="Start:").pack(side="left")
        ttk.Entry(fa_top, textvariable=self.t8_fa_start, width=12).pack(side="left", padx=4)
        ttk.Label(fa_top, text="End:").pack(side="left")
        ttk.Entry(fa_top, textvariable=self.t8_fa_end, width=12).pack(side="left", padx=4)
        ttk.Button(fa_top, text="Fetch Appointments",
                   command=self._t8_fetch_appts).pack(side="left", padx=8)


        self.t8_appt_lb = tk.Listbox(fa, height=4, font=("Consolas", 9),
                                      selectmode="browse", activestyle="dotbox")
        fa_sb = ttk.Scrollbar(fa, command=self.t8_appt_lb.yview)
        self.t8_appt_lb.configure(yscrollcommand=fa_sb.set)
        fa_sb.pack(side="right", fill="y")
        self.t8_appt_lb.pack(fill="x", expand=True, pady=(4, 0))
        self.t8_appt_lb.bind("<<ListboxSelect>>", self._t8_appt_selected)
        self.t8_appts_data: List[Dict] = []


        # ── Patient info row ──────────────────────────────────────────
        pinfo = ttk.LabelFrame(tab, text="Patient", padding=6)
        pinfo.pack(fill="x", padx=8, pady=4)


        ttk.Label(pinfo, text="Name:").grid(row=0, column=0, sticky="w")
        self.t8_patient = tk.StringVar()
        ttk.Entry(pinfo, textvariable=self.t8_patient, width=34
                  ).grid(row=0, column=1, padx=6, sticky="w")


        ttk.Label(pinfo, text="Patient Email:").grid(row=0, column=2, padx=(12, 4), sticky="w")
        self.t8_patient_email = tk.StringVar()
        ttk.Entry(pinfo, textvariable=self.t8_patient_email, width=34
                  ).grid(row=0, column=3, padx=6, sticky="w")


        # ── Letter type ───────────────────────────────────────────────
        ltype = ttk.LabelFrame(tab, text="Letter Type", padding=6)
        ltype.pack(fill="x", padx=8, pady=4)


        self.t8_letter_type = tk.StringVar(value="fitness")
        ttk.Radiobutton(ltype, text="Employment Fitness for Duty",
                        variable=self.t8_letter_type, value="fitness",
                        command=self._t8_on_type_change
                        ).grid(row=0, column=0, sticky="w", padx=6)
        ttk.Radiobutton(ltype, text="Medical Absence Excuse",
                        variable=self.t8_letter_type, value="absence",
                        command=self._t8_on_type_change
                        ).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Radiobutton(ltype, text="Other (custom instructions)",
                        variable=self.t8_letter_type, value="other",
                        command=self._t8_on_type_change
                        ).grid(row=0, column=2, sticky="w", padx=6)


        # ── Instructions / modifications ──────────────────────────────
        inst_lf = ttk.LabelFrame(tab, text="Instructions / Modifications for LLM", padding=6)
        inst_lf.pack(fill="x", padx=8, pady=4)


        self.t8_instructions = tk.Text(inst_lf, height=4, wrap="word",
                                        font=("Segoe UI", 10), relief="flat", borderwidth=1)
        inst_vsb = ttk.Scrollbar(inst_lf, command=self.t8_instructions.yview)
        self.t8_instructions.configure(yscrollcommand=inst_vsb.set)
        inst_vsb.pack(side="right", fill="y")
        self.t8_instructions.pack(fill="x", expand=True)


        self.t8_instructions.insert("1.0",
            "Leave blank to use the standard letter format for the selected type.\n"
            "Add notes here to modify the default, e.g.:\n"
            "  'Patient name is John Smith, seen on April 14, 2026.'\n"
            "  'The fitness determination was UNFIT due to active psychosis.'")


        # ── Additional recipient ──────────────────────────────────────
        recip_lf = ttk.LabelFrame(
            tab,
            text="Also Send To (Employer / School / Other Entity — optional)",
            padding=6,
        )
        recip_lf.pack(fill="x", padx=8, pady=4)


        ttk.Label(recip_lf, text="Entity Name:").grid(row=0, column=0, sticky="w")
        self.t8_entity_name = tk.StringVar()
        ttk.Entry(recip_lf, textvariable=self.t8_entity_name, width=30
                  ).grid(row=0, column=1, padx=6, sticky="w")


        ttk.Label(recip_lf, text="Entity Email:").grid(row=0, column=2, padx=(12, 4), sticky="w")
        self.t8_entity_email = tk.StringVar()
        ttk.Entry(recip_lf, textvariable=self.t8_entity_email, width=30
                  ).grid(row=0, column=3, padx=6, sticky="w")


        ttk.Label(recip_lf, text="Subject override (optional):").grid(row=1, column=0,
                                                                        sticky="w", pady=(4, 0))
        self.t8_subject_override = tk.StringVar()
        ttk.Entry(recip_lf, textvariable=self.t8_subject_override, width=60
                  ).grid(row=1, column=1, columnspan=3, padx=6, pady=(4, 0), sticky="w")


        # ── Action buttons ────────────────────────────────────────────
        btn_row = ttk.Frame(tab)
        btn_row.pack(fill="x", padx=8, pady=4)
        ttk.Button(btn_row, text="✉  Generate Letter",
                   command=self._t8_generate).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Clear",
                   command=self._t8_clear).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Clear Log",
                   command=lambda: self.t8_log.delete("1.0", "end")).pack(side="left", padx=4)


        # ── Log ───────────────────────────────────────────────────────
        log_frame = ttk.LabelFrame(tab, text="Log", padding=4)
        log_frame.pack(fill="both", expand=True, padx=8, pady=4)
        self.t8_log = tk.Text(log_frame, wrap="word", font=("Consolas", 9))
        t8_sb = ttk.Scrollbar(log_frame, command=self.t8_log.yview)
        self.t8_log.configure(yscrollcommand=t8_sb.set)
        t8_sb.pack(side="right", fill="y")
        self.t8_log.pack(fill="both", expand=True)


        self._t8_last_letter_text: str = ""
        self._t8_last_pdf_path: str = ""


    def _t8_log(self, msg: str):
        self.t8_log.insert("end", msg + "\n")
        self.t8_log.see("end")
        self.t8_log.update_idletasks()


    def _t8_on_type_change(self):
        ltype = self.t8_letter_type.get()
        self.t8_instructions.delete("1.0", "end")
        if ltype == "fitness":
            self.t8_instructions.insert("1.0",
                "Leave blank to generate a standard Employment Fitness for Duty letter.\n"
                "Add any specific modifications, e.g. 'Patient was found UNFIT due to ...'")
        elif ltype == "absence":
            self.t8_instructions.insert("1.0",
                "Leave blank to generate a standard medical absence excuse letter.\n"
                "Add details if needed, e.g. 'Excuse covers April 14–15, 2026.'")
        else:
            self.t8_instructions.insert("1.0",
                "Describe the letter you need. Include all relevant details:\n"
                "recipient, purpose, key clinical findings, and any specific language required.")


    def _t8_fetch_appts(self):
        self.t8_log.delete("1.0", "end")
        threading.Thread(target=self._t8_fetch_appts_worker, daemon=True).start()


    def _t8_fetch_appts_worker(self):
        log = self._t8_log
        try:
            self._init_google(log)
            cfg    = self.cfg
            cal_id = resolve_calendar_id(cfg)
            tz_str = cfg.get("calendar_timezone", "America/Chicago")
            start  = dt.datetime.fromisoformat(self.t8_fa_start.get()).date()
            end    = dt.datetime.fromisoformat(self.t8_fa_end.get()).date()
            events = fetch_calendar_events(self._calendar, cal_id, start, end, tz_str, log)
            owner  = cfg.get("calendar_owner_email", "")


            appts: List[Dict] = []
            for ev in events:
                email = extract_patient_email_from_event(ev, owner)
                if not email:
                    continue
                name     = _strip_noll_psych_group(infer_patient_name_from_event(ev))
                start_s  = event_start_str(ev)
                label_dt = ""
                try:
                    label_dt = dt.datetime.fromisoformat(
                        start_s.replace("Z", "+00:00")).astimezone().strftime("%m/%d %I:%M %p")
                except Exception:
                    label_dt = start_s[:16]
                appts.append({"name": name, "email": email, "start_str": start_s, "label": label_dt})


            def _populate():
                self.t8_appt_lb.delete(0, "end")
                self.t8_appts_data.clear()
                for a in appts:
                    self.t8_appt_lb.insert("end", f"{a['label']}  —  {a['name']}")
                    self.t8_appts_data.append(a)
                log(f"✅ {len(appts)} appointment(s) fetched.")


            self.after(0, _populate)
        except Exception as e:
            log(f"❌ Fetch error: {e}\n{traceback.format_exc()}")


    def _t8_appt_selected(self, _event=None):
        sel = self.t8_appt_lb.curselection()
        if not sel:
            return
        appt = self.t8_appts_data[sel[0]]
        self.t8_patient.set(appt["name"])
        if not self.t8_patient_email.get().strip():
            self.t8_patient_email.set(appt["email"])


    def _t8_clear(self):
        self.t8_patient.set("")
        self.t8_patient_email.set("")
        self.t8_entity_name.set("")
        self.t8_entity_email.set("")
        self.t8_subject_override.set("")
        self._t8_last_letter_text = ""
        self._t8_last_pdf_path = ""


    # ── LLM prompt builders ───────────────────────────────────────────


    def _t8_build_prompt(self, patient_name: str, patient_email: str,
                          letter_type: str, instructions: str) -> Tuple[str, str]:
        """
        Build the (system_prompt, user_message) pair for the letter LLM call.
        Returns (system, user).
        """
        _d = dt.date.today()
        today = _d.strftime("%B ") + str(_d.day) + _d.strftime(", %Y")
        addr_block = "\n".join(_RE_ADDR_LINES)


        base_system = (
            "You are a clinical assistant for Noll Psych Group, writing a professional "
            "letter on behalf of Nicholas C. Noll, Ph.D., Clinical Psychologist.\n\n"
            "Output ONLY the letter body — no markdown, no headers, no bullet points. "
            "Plain text only.\n\n"
            "The letter already has an NPG letterhead with logo and address printed above "
            "the content. Your output should begin with the date line, then a blank line, "
            "then 'To Whom It May Concern:' (or a specific salutation if instructed), "
            "then a blank line, then the Re: line in bold-equivalent (write it as "
            "'Re: Title Here'), then the letter body paragraphs, then a blank line, "
            "then 'Sincerely,', then two blank lines, then 'Nicholas C. Noll, Ph.D.' "
            "on its own line, then 'Clinical Psychologist' on the next line.\n\n"
            "Do not include the address block — it is already on the letterhead."
        )


        if letter_type == "fitness":
            system = base_system + (
                "\n\nYou are writing an Employment Fitness for Duty letter. "
                "The standard format for this letter:\n"
                "- Re: Fitness for Duty — Confidential\n"
                "- Opening: this letter is provided in response to a request for a "
                "fitness-for-duty determination following a psychological and "
                "neuropsychological evaluation.\n"
                "- Fitness determination paragraph: state the professional opinion that "
                "the individual IS fit (or unfit, if instructed) to continue employment, "
                "from psychological and cognitive standpoints. Note what the evaluation "
                "did NOT reveal (psychosis, bipolar disorder, major neurocognitive disorder). "
                "Include cognitive screening findings, denial of suicidal ideation, "
                "intact judgment, and low workplace risk with appropriate conditions.\n"
                "- Recommendations paragraph: note that ongoing mental health treatment "
                "is recommended.\n"
                "- Confidentiality note: state evaluation details are PHI and not disclosed "
                "beyond what is necessary."
            )
            user = (
                f"Date: {today}\n"
                f"Patient name: {patient_name or '(not specified — omit from letter)'}\n"
                f"Evaluation date: {today} (use today's date unless instructed otherwise)\n\n"
                f"Additional instructions:\n{instructions or 'None — use standard fitness letter format.'}"
            )


        elif letter_type == "absence":
            system = base_system + (
                "\n\nYou are writing a Medical Appointment Absence Excuse letter. "
                "The standard format for this letter:\n"
                "- Re: Medical Appointment Verification — [Patient Full Name]\n"
                "- First paragraph: verify that [Patient Name] was seen as a patient "
                "at this office on [date] for a scheduled medical appointment.\n"
                "- Second paragraph: please excuse his/her/their absence from work on "
                "this date. Direct any questions to this office.\n"
                "The letter must include the patient's full name in the Re: line. "
                "Use 'his' unless instructed otherwise regarding pronoun."
            )
            user = (
                f"Date: {today}\n"
                f"Patient name: {patient_name or '(required — include as instructed)'}\n"
                f"Appointment date: {today} (use today unless instructed otherwise)\n\n"
                f"Additional instructions:\n{instructions or 'None — use standard absence excuse format.'}"
            )


        else:  # other
            system = base_system + (
                "\n\nYou are writing a custom clinical letter as directed by the "
                "instructions provided. Follow the same professional tone and structure "
                "as other NPG letters (date, salutation, Re: line, body paragraphs, "
                "Sincerely, signature block). Adapt content entirely to the instructions."
            )
            user = (
                f"Date: {today}\n"
                f"Patient name: {patient_name or '(not specified)'}\n\n"
                f"Letter instructions:\n{instructions}"
            )


        return system, user


    # ── Generation workflow ───────────────────────────────────────────


    def _t8_generate(self):
        patient_name = self.t8_patient.get().strip()
        if not patient_name:
            messagebox.showerror("Input error", "Enter or select a patient name first.")
            return
        instructions = self.t8_instructions.get("1.0", "end").strip()
        letter_type  = self.t8_letter_type.get()
        if letter_type == "other" and not instructions.strip():
            messagebox.showerror("Input error",
                "For 'Other' letter type, enter instructions describing the letter to write.")
            return
        self.t8_log.delete("1.0", "end")
        threading.Thread(target=self._t8_generate_worker,
                         args=(patient_name, instructions, letter_type), daemon=True).start()


    def _t8_generate_worker(self, patient_name: str, instructions: str, letter_type: str):
        log = self._t8_log
        try:
            patient_email = self.t8_patient_email.get().strip()
            system_prompt, user_msg = self._t8_build_prompt(
                patient_name, patient_email, letter_type, instructions)


            log(f"Generating {letter_type} letter for {patient_name}…")
            hcfg = load_qwen_config(self.rcfg)
            t2_key = self.t2_webui_key.get().strip() if hasattr(self, "t2_webui_key") else ""
            if t2_key:
                hcfg.api_key = t2_key


            url = hcfg.base_url.rstrip("/") + hcfg.api_path
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_msg},
            ]
            log(f"  → calling Qwen ({hcfg.model})…")
            text, finish = _webui_call(url, hcfg.model, 0.25, 120, messages,
                                       max_tokens=1500, api_key=hcfg.api_key)
            letter_text = text.strip()


            # Light continuation if truncated
            for _ in range(3):
                if finish != "length" and not _looks_truncated(letter_text):
                    break
                log("  → letter looks incomplete — continuing…")
                messages.append({"role": "assistant", "content": letter_text})
                messages.append({"role": "user", "content":
                    "Continue the letter exactly where you left off. "
                    "Do not repeat any text. End with the signature block."})
                more, finish = _webui_call(url, hcfg.model, 0.25, 60, messages,
                                           max_tokens=600, api_key=hcfg.api_key)
                if not more:
                    break
                letter_text = (letter_text.rstrip() + "\n\n" + more.lstrip()).strip()


            # Strip any stray markdown
            letter_text = re.sub(r"\*\*([^*]+)\*\*", r"\1", letter_text)
            letter_text = re.sub(r"\*([^*]+)\*",   r"\1", letter_text)
            letter_text = re.sub(r"#{1,6}\s*",     "",     letter_text)


            log(f"✅ Letter generated ({len(letter_text):,} chars)")
            self._t8_last_letter_text = letter_text


            # Show approval dialog on main thread
            self.after(0, lambda lt=letter_text, pn=patient_name: self._t8_show_approval(lt, pn))


        except Exception as e:
            log(f"❌ Generation failed: {e}\n{traceback.format_exc()}")


    def _t8_show_approval(self, letter_text: str, patient_name: str):
        """Modal approval / edit window — identical workflow to Report Editor preview."""
        win = tk.Toplevel(self)
        win.title(f"Letter Review — {patient_name}")
        win.geometry("760x580")
        win.grab_set()


        ttk.Label(win,
                  text="Review and edit the letter below, then approve to save and send.",
                  wraplength=720, justify="left").pack(padx=12, pady=(10, 4), anchor="w")


        editor_frame = ttk.Frame(win)
        editor_frame.pack(fill="both", expand=True, padx=12, pady=4)
        editor = tk.Text(editor_frame, wrap="word", font=("Segoe UI", 10),
                         undo=True, relief="flat", borderwidth=1, padx=6, pady=6)
        vsb = ttk.Scrollbar(editor_frame, command=editor.yview)
        editor.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        editor.pack(side="left", fill="both", expand=True)
        editor.insert("1.0", letter_text)


        status_var = tk.StringVar(value="")
        ttk.Label(win, textvariable=status_var, foreground="gray").pack(
            padx=12, pady=(0, 2), anchor="w")


        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill="x", padx=12, pady=8)


        def _preview_pdf():
            lt = editor.get("1.0", "end").strip()
            self._t8_last_letter_text = lt
            import tempfile
            fd, tmp = tempfile.mkstemp(suffix=".pdf", prefix="npg_letter_preview_")
            os.close(fd)
            try:
                # Extract first line as date for generate_letter_pdf
                lines = lt.splitlines()
                date_line = lines[0].strip() if lines else ""
                body = "\n".join(lines[1:]).strip() if len(lines) > 1 else lt
                generate_letter_pdf(tmp, body, date_line)
                open_file_os(tmp)
                status_var.set("PDF opened for preview.")
            except Exception as ex:
                messagebox.showerror("Preview failed", str(ex), parent=win)


        def _approve():
            lt = editor.get("1.0", "end").strip()
            self._t8_last_letter_text = lt
            patient_name_cur = self.t8_patient.get().strip()
            if not patient_name_cur:
                messagebox.showwarning("No patient", "Enter a patient name before saving.", parent=win)
                return


            # Save PDF to patient folder
            patient_folder = ensure_patient_folder(self.patients_root, patient_name_cur)
            ltype = self.t8_letter_type.get()
            type_slug = {"fitness": "FitnessLetter", "absence": "AbsenceLetter"}.get(ltype, "Letter")
            date_slug  = dt.date.today().strftime("%Y%m%d")
            safe_n     = re.sub(r"[^\w]", "", patient_name_cur.replace(" ", "_"))
            pdf_name   = f"{type_slug}_{safe_n}_{date_slug}.pdf"
            pdf_path   = os.path.join(patient_folder, pdf_name)


            try:
                lines = lt.splitlines()
                date_line = lines[0].strip() if lines else ""
                body = "\n".join(lines[1:]).strip() if len(lines) > 1 else lt
                generate_letter_pdf(pdf_path, body, date_line)
                self._t8_last_pdf_path = pdf_path
                status_var.set(f"Saved → {pdf_path}")
                self._t8_log(f"✅ Letter PDF saved: {pdf_path}")
                messagebox.showinfo("Saved", f"Letter saved:\n{pdf_path}", parent=win)
                win.destroy()
                # Offer to send
                self.after(100, lambda pn=patient_name_cur: self._t8_offer_send(pn))
            except Exception as ex:
                messagebox.showerror("Save failed", str(ex), parent=win)


        def _discard():
            self._t8_log("Letter discarded — no file saved.")
            win.destroy()


        ttk.Button(btn_frame, text="🔍  Preview PDF", command=_preview_pdf).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="✅  Approve & Save", command=_approve).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="✗  Discard", command=_discard).pack(side="left", padx=6)


    def _t8_offer_send(self, patient_name: str):
        """After approval, offer to send the letter via email."""
        patient_email = self.t8_patient_email.get().strip()
        entity_email  = self.t8_entity_email.get().strip()


        recipients = []
        if patient_email and "@" in patient_email:
            recipients.append(("patient", patient_email))
        if entity_email and "@" in entity_email:
            entity_name = self.t8_entity_name.get().strip() or "the entity"
            recipients.append((entity_name, entity_email))


        if not recipients:
            self._t8_log("No email recipients configured — letter saved only.")
            return


        desc = " and ".join(f"{lbl} ({addr})" for lbl, addr in recipients)
        if not messagebox.askyesno("Send Letter?",
                                   f"Send letter to:\n  {desc}\n\nSend now?"):
            return


        threading.Thread(target=self._t8_send_worker,
                         args=(patient_name, recipients), daemon=True).start()


    def _t8_send_worker(self, patient_name: str, recipients: List[Tuple[str, str]]):
        log = self._t8_log
        pdf  = self._t8_last_pdf_path
        if not pdf or not os.path.exists(pdf):
            log("❌ No PDF found to send — generate and approve the letter first.")
            return


        smtp = self.smtp_conf
        if not smtp.get("host") or not smtp.get("username"):
            log("❌ SMTP not configured — cannot send email.")
            self.after(0, lambda: messagebox.showerror(
                "SMTP not configured",
                "SMTP settings are missing in config.json."))
            return


        ltype = self.t8_letter_type.get()
        subj_default = {
            "fitness": f"Fitness for Duty Letter — {patient_name}",
            "absence": f"Medical Excuse Letter — {patient_name}",
        }.get(ltype, f"Clinical Letter — {patient_name}")
        subject = self.t8_subject_override.get().strip() or subj_default
        from_name = smtp.get("from_name", "Noll Psych Group")


        for label, addr in recipients:
            if label == "patient":
                first = patient_name.split()[0] if patient_name else "Patient"
                body = (
                    f"Dear {first},\n\n"
                    "Please find the attached letter from our office.\n\n"
                    "If you have any questions, please do not hesitate to contact us.\n\n"
                    f"Sincerely,\n{from_name}"
                )
            else:
                body = (
                    f"Dear {label},\n\n"
                    "Please find the attached letter regarding your request.\n\n"
                    "If you have any questions, please contact our office directly.\n\n"
                    f"Sincerely,\n{from_name}"
                )
            ok = send_smtp(smtp, [addr], subject=subject, body=body,
                           attachments=[pdf], log=log)
            if ok:
                log(f"✅ Letter sent to {label} ({addr}).")
            else:
                log(f"❌ Failed to send to {label} ({addr}).")


        self.after(0, lambda: messagebox.showinfo("Send Complete",
            "Letter sending complete. See log for details."))






    # ==================================================================
    # ── TAB 9: EMAIL ──────────────────────────────────────────────────
    # ==================================================================
    # Gmail access requires domain-wide delegation on the service account.
    # See init_gmail_service() docstring for one-time setup instructions.
    # ==================================================================


    # ── Gmail helpers ─────────────────────────────────────────────────


    def _t9_imap(self):
        """Return an open IMAP4_SSL connection using the SMTP credentials."""
        import imaplib
        if hasattr(self, "_imap_conn") and self._imap_conn is not None:
            try:
                self._imap_conn.noop()
                return self._imap_conn
            except Exception:
                self._imap_conn = None
        smtp_host = self.smtp_conf.get("host", "smtp.gmail.com")
        imap_host = smtp_host.replace("smtp.", "imap.", 1)
        if imap_host == smtp_host:
            imap_host = "imap.gmail.com"
        user = self.smtp_conf.get("username", "")
        pwd  = self.smtp_conf.get("password", "")
        conn = imaplib.IMAP4_SSL(imap_host, 993)
        conn.login(user, pwd)
        self._imap_conn = conn
        return conn


    def _t9_known_emails(self) -> set:
        """
        Collect all known clinical email addresses:
        • provider_contacts.json emails
        • calendar_owner_email (self) — excluded from results
        • Any patient emails fetched from recent calendar events
        """
        known = set()
        contacts = ProviderContacts(_resolve_contacts_path())
        for c in contacts.data.get("contacts", []):
            for e in c.get("emails", []):
                if e: known.add(normalize_email(e))
            for e in c.get("cc", []):
                if e: known.add(normalize_email(e))
        # Patient emails from the stored billing emails cache
        billing_path = self.cfg.get(
            "billing_emails_path",
            os.path.join(_programdata_dir(), "billing_emails.json"))
        if os.path.exists(billing_path):
            try:
                data = json.loads(Path(billing_path).read_text(encoding="utf-8"))
                for v in data.values():
                    if isinstance(v, str) and "@" in v:
                        known.add(normalize_email(v))
                    elif isinstance(v, dict):
                        e = v.get("email","")
                        if e: known.add(normalize_email(e))
            except Exception:
                pass
        return known


    def _t9_is_clinical(self, sender_email: str, subject: str,
                         body_snippet: str, known: set) -> bool:
        """Heuristic: is this email likely clinical?"""
        se = normalize_email(sender_email)
        if se in known:
            return True
        # Domain match against our own domain — internal emails from staff
        owner = self.cfg.get("calendar_owner_email", "")
        if owner and se.endswith("@" + owner.split("@")[-1]):
            return True
        # Subject keywords
        clinical_kw = re.compile(
            r"\b(eval|evaluation|assessment|report|test|patient|appointment|"
            r"referral|refer|record|records|diagnosis|therapy|session|intake|"
            r"schedule|billing|insurance|claim|authorization|auth|rx|medication|"
            r"prescription|consult|consultation|results|feedback|letter|fax)\b",
            re.I)
        text = f"{subject} {body_snippet}"
        if clinical_kw.search(text):
            return True
        return False


    def _t9_decode_header_value(self, raw: str) -> str:
        """Decode an RFC 2047-encoded email header value."""
        from email.header import decode_header as _dh
        if not raw:
            return ""
        parts = _dh(raw)
        out = []
        for part, charset in parts:
            if isinstance(part, bytes):
                out.append(part.decode(charset or "utf-8", errors="replace"))
            else:
                out.append(str(part))
        return "".join(out)


    def _t9_decode_imap_body(self, msg) -> str:
        """Extract plain-text body from an email.message.Message object."""
        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == "text/plain" and part.get_content_disposition() != "attachment":
                    charset = part.get_content_charset() or "utf-8"
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode(charset, errors="replace")
        else:
            charset = msg.get_content_charset() or "utf-8"
            payload = msg.get_payload(decode=True)
            if payload:
                return payload.decode(charset, errors="replace")
        # fallback: strip HTML
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    charset = part.get_content_charset() or "utf-8"
                    payload = part.get_payload(decode=True)
                    if payload:
                        raw = payload.decode(charset, errors="replace")
                        return re.sub(r"<[^>]+>", " ", raw).strip()
        return ""


    def _t9_fetch_emails_worker(self, log):
        """Fetch INBOX emails via IMAP and filter to clinical ones."""
        import imaplib, email as _email
        imap  = self._t9_imap()
        known = self._t9_known_emails()
        owner = self.smtp_conf.get("username", "").lower()
        log(f"Known clinical addresses: {len(known)}")


        imap.select("INBOX", readonly=True)
        since_date = (dt.date.today() - dt.timedelta(days=30)).strftime("%d-%b-%Y")
        _, data = imap.search(None, f'SINCE {since_date}')
        nums = data[0].split() if data and data[0] else []
        nums = nums[-60:] if len(nums) > 60 else nums
        log(f"Inbox messages to check: {len(nums)}")


        clinical  = []
        responded = []


        for num in reversed(nums):
            try:
                _, raw_data = imap.fetch(num, "(FLAGS RFC822)")
                if not raw_data or not raw_data[0]:
                    continue
                flags_str = (raw_data[0][0].decode()
                             if isinstance(raw_data[0][0], bytes)
                             else str(raw_data[0][0]))
                raw_bytes = raw_data[0][1]
                is_answered = "\\Answered" in flags_str


                msg = _email.message_from_bytes(raw_bytes)
                sender  = self._t9_decode_header_value(msg.get("From", ""))
                subject = self._t9_decode_header_value(msg.get("Subject", "(no subject)"))
                date_s  = msg.get("Date", "")
                msg_id  = msg.get("Message-ID", "")
                num_str = num.decode() if isinstance(num, bytes) else str(num)


                m = re.search(r"<([^>]+)>", sender) or re.match(r"\S+@\S+", sender)
                sender_email = (m.group(1) if m and "<" in sender
                                else (m.group(0) if m else sender))
                sender_email = sender_email.strip().lower()


                if sender_email == owner:
                    continue


                body_txt = self._t9_decode_imap_body(msg)
                snippet  = body_txt[:200]


                if not self._t9_is_clinical(sender_email, subject, snippet, known):
                    continue


                entry = {
                    "id":           num_str,
                    "thread_id":    num_str,
                    "msg_id":       msg_id,
                    "sender":       sender,
                    "sender_email": sender_email,
                    "subject":      subject,
                    "date":         date_s,
                    "snippet":      snippet,
                    "body":         body_txt,
                    "responded":    is_answered,
                    "label_ids":    [],
                }
                if is_answered:
                    responded.append(entry)
                else:
                    clinical.append(entry)
            except Exception as e:
                log(f"  ⚠️  Skipped message {num}: {e}")


        log(f"✅ Clinical emails: {len(clinical)} pending, {len(responded)} responded")
        return clinical, responded


    def _t9_decode_body(self, payload: dict) -> str:
        """Recursively extract plain-text body from a Gmail payload."""
        import base64
        mime = payload.get("mimeType", "")
        if mime == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                try:
                    return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
                except Exception:
                    pass
        for part in payload.get("parts", []):
            result = self._t9_decode_body(part)
            if result:
                return result
        # Fallback: html part
        if mime == "text/html":
            data = payload.get("body", {}).get("data", "")
            if data:
                try:
                    raw = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
                    return re.sub(r"<[^>]+>", " ", raw).strip()
                except Exception:
                    pass
        return ""


    # ── Build UI ──────────────────────────────────────────────────────


    def _build_tab9_email(self):
        tab = ttk.Frame(self.nb)
        self.nb.add(tab, text="  Email  ")
        self._t9_tab = tab
        self._t9_responded_label_id = ""
        self._t9_clinical_emails: list = []
        self._t9_responded_emails: list = []
        self._t9_selected_email: dict  = {}


        # ── Top toolbar ───────────────────────────────────────────────
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill="x", padx=8, pady=6)


        ttk.Button(toolbar, text="🔄  Fetch Clinical Emails",
                   command=self._t9_fetch).pack(side="left", padx=4)
        self.t9_show_responded = tk.BooleanVar(value=False)
        ttk.Checkbutton(toolbar, text="Show Responded",
                        variable=self.t9_show_responded,
                        command=self._t9_refresh_list).pack(side="left", padx=8)
        ttk.Button(toolbar, text="Clear Log",
                   command=lambda: self.t9_log.delete("1.0","end")
                   ).pack(side="right", padx=4)


        # ── Paned: left=list, right=detail ───────────────────────────
        paned = ttk.PanedWindow(tab, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=8, pady=4)


        # Left: email list
        list_frame = ttk.Frame(paned)
        paned.add(list_frame, weight=1)


        self.t9_list_lb = tk.Listbox(
            list_frame, font=("Segoe UI", 9),
            selectmode="browse", activestyle="dotbox",
            bg="#1e1e2e", fg="#cdd6f4",
            selectbackground="#3b82f6", selectforeground="white")
        t9_lsb = ttk.Scrollbar(list_frame, command=self.t9_list_lb.yview)
        self.t9_list_lb.configure(yscrollcommand=t9_lsb.set)
        t9_lsb.pack(side="right", fill="y")
        self.t9_list_lb.pack(fill="both", expand=True)
        self.t9_list_lb.bind("<<ListboxSelect>>", self._t9_on_select)


        # Right: detail + reply
        detail_frame = ttk.Frame(paned)
        paned.add(detail_frame, weight=2)


        # Email header labels
        hdr = ttk.LabelFrame(detail_frame, text="Email", padding=6)
        hdr.pack(fill="x", padx=4, pady=4)


        self.t9_lbl_from    = tk.StringVar()
        self.t9_lbl_subject = tk.StringVar()
        self.t9_lbl_date    = tk.StringVar()
        self.t9_lbl_status  = tk.StringVar()


        for row_i, (lbl, var) in enumerate([
            ("From:",    self.t9_lbl_from),
            ("Subject:", self.t9_lbl_subject),
            ("Date:",    self.t9_lbl_date),
            ("Status:",  self.t9_lbl_status),
        ]):
            ttk.Label(hdr, text=lbl, width=8, anchor="e").grid(
                row=row_i, column=0, sticky="e", padx=4, pady=1)
            ttk.Label(hdr, textvariable=var, anchor="w", wraplength=440,
                      justify="left").grid(
                row=row_i, column=1, sticky="w", padx=4, pady=1)


        # Body view
        body_lf = ttk.LabelFrame(detail_frame, text="Email Body", padding=4)
        body_lf.pack(fill="both", expand=True, padx=4, pady=4)
        self.t9_body = tk.Text(
            body_lf, wrap="word", font=("Segoe UI", 9),
            state="disabled", relief="flat", bg="#f8f8ff", height=8)
        body_sb = ttk.Scrollbar(body_lf, command=self.t9_body.yview)
        self.t9_body.configure(yscrollcommand=body_sb.set)
        body_sb.pack(side="right", fill="y")
        self.t9_body.pack(fill="both", expand=True)


        # Reply area
        reply_lf = ttk.LabelFrame(detail_frame, text="Reply", padding=4)
        reply_lf.pack(fill="both", expand=True, padx=4, pady=4)


        reply_btn_row = ttk.Frame(reply_lf)
        reply_btn_row.pack(fill="x", pady=(0, 4))
        ttk.Button(reply_btn_row, text="✨  Draft with Qwen",
                   command=self._t9_draft_llm).pack(side="left", padx=4)
        ttk.Button(reply_btn_row, text="Send Reply",
                   command=self._t9_send_reply).pack(side="right", padx=4)
        ttk.Button(reply_btn_row, text="Clear",
                   command=lambda: self.t9_reply.delete("1.0","end")
                   ).pack(side="right", padx=4)


        self.t9_reply = tk.Text(
            reply_lf, wrap="word", font=("Segoe UI", 10),
            relief="flat", borderwidth=1, height=8, undo=True)
        reply_sb = ttk.Scrollbar(reply_lf, command=self.t9_reply.yview)
        self.t9_reply.configure(yscrollcommand=reply_sb.set)
        reply_sb.pack(side="right", fill="y")
        self.t9_reply.pack(fill="both", expand=True)


        # Log
        log_lf = ttk.LabelFrame(tab, text="Log", padding=4)
        log_lf.pack(fill="x", padx=8, pady=4)
        self.t9_log = tk.Text(log_lf, wrap="word", font=("Consolas", 8), height=4)
        t9_logsb = ttk.Scrollbar(log_lf, command=self.t9_log.yview)
        self.t9_log.configure(yscrollcommand=t9_logsb.set)
        t9_logsb.pack(side="right", fill="y")
        self.t9_log.pack(fill="both", expand=True)


    # ── List management ───────────────────────────────────────────────


    def _t9_log(self, msg: str):
        self.t9_log.insert("end", msg + "\n")
        self.t9_log.see("end")
        self.t9_log.update_idletasks()


    def _t9_fetch(self):
        self.t9_list_lb.delete(0, "end")
        self.t9_list_lb.insert("end", "Fetching…")
        threading.Thread(target=self._t9_fetch_worker, daemon=True).start()


    def _t9_fetch_worker(self):
        log = self._t9_log
        try:
            self._init_google(log)
            clinical, responded = self._t9_fetch_emails_worker(log)
            self._t9_clinical_emails  = clinical
            self._t9_responded_emails = responded
            self.after(0, self._t9_refresh_list)
        except Exception as e:
            log(f"❌ {e}\n{traceback.format_exc()}")
            self.after(0, lambda: (
                self.t9_list_lb.delete(0, "end"),
                self.t9_list_lb.insert("end", f"Error: {e}")
            ))


    def _t9_refresh_list(self):
        self.t9_list_lb.delete(0, "end")
        show_resp = self.t9_show_responded.get()
        emails = self._t9_clinical_emails[:]
        if show_resp:
            emails += self._t9_responded_emails


        if not emails:
            self.t9_list_lb.insert("end", "(no clinical emails)")
            return


        self._t9_list_index = emails  # keep reference for selection
        for em in emails:
            prefix = "✓ " if em["responded"] else "● "
            sender_short = em["sender_email"].split("@")[0][:18]
            subj  = em["subject"][:38]
            label = f"{prefix}{sender_short:<18}  {subj}"
            self.t9_list_lb.insert("end", label)
            if em["responded"]:
                last = self.t9_list_lb.size() - 1
                self.t9_list_lb.itemconfig(last, fg="#6b7280")


    def _t9_on_select(self, _event=None):
        sel = self.t9_list_lb.curselection()
        if not sel or not hasattr(self, "_t9_list_index"):
            return
        em = self._t9_list_index[sel[0]]
        self._t9_selected_email = em


        self.t9_lbl_from.set(em["sender"])
        self.t9_lbl_subject.set(em["subject"])
        self.t9_lbl_date.set(em["date"])
        self.t9_lbl_status.set("✓ Responded" if em["responded"] else "● Pending reply")


        self.t9_body.configure(state="normal")
        self.t9_body.delete("1.0", "end")
        self.t9_body.insert("1.0", em["body"] or em["snippet"])
        self.t9_body.configure(state="disabled")


        # Pre-fill reply with a simple salutation
        self.t9_reply.delete("1.0", "end")
        first = em["sender"].split("<")[0].strip().split()[0] if em["sender"] else "there"
        smtp_name = self.smtp_conf.get("from_name", "Nicholas C. Noll, Ph.D.")
        self.t9_reply.insert("1.0",
            f"Dear {first},\n\n\n\nSincerely,\n{smtp_name}\nClinical Psychologist\n"
            f"Noll Psych Group\n(816) 835-9882")


    # ── LLM draft ─────────────────────────────────────────────────────


    def _t9_draft_llm(self):
        em = self._t9_selected_email
        if not em:
            messagebox.showwarning("No email selected", "Select an email first.")
            return
        threading.Thread(target=self._t9_draft_llm_worker, daemon=True).start()


    def _t9_draft_llm_worker(self):
        log = self._t9_log
        em  = self._t9_selected_email
        try:
            hcfg  = load_qwen_config(self.rcfg)
            smtp_name = self.smtp_conf.get("from_name", "Nicholas C. Noll, Ph.D.")
            system = (
                "You are a clinical assistant drafting a professional email reply "
                "on behalf of Nicholas C. Noll, Ph.D., Clinical Psychologist at "
                "Noll Psych Group. Keep replies concise, professional, and warm. "
                "Do not disclose protected health information. "
                "Do not use markdown — plain text only. "
                "End every reply with the signature:\n"
                f"Sincerely,\n{smtp_name}\nClinical Psychologist\n"
                "Noll Psych Group\n(816) 835-9882\nFax: (866) 601-2313"
            )
            user = (
                f"Draft a reply to this email.\n\n"
                f"From: {em['sender']}\n"
                f"Subject: {em['subject']}\n\n"
                f"Email body:\n{(em['body'] or em['snippet'])[:2000]}"
            )
            log("Drafting reply with Qwen…")
            url = hcfg.base_url.rstrip("/") + hcfg.api_path
            msgs = [{"role": "system", "content": system},
                    {"role": "user",   "content": user}]
            text, _ = _webui_call(url, hcfg.model, 0.3, 120, msgs,
                                   max_tokens=600, api_key=hcfg.api_key)
            draft = text.strip()
            # Strip any markdown
            draft = re.sub(r"\*\*([^*]+)\*\*", r"\1", draft)
            draft = re.sub(r"#{1,6}\s*", "", draft)
            log(f"✅ Draft ready ({len(draft):,} chars)")


            def _fill():
                self.t9_reply.delete("1.0", "end")
                self.t9_reply.insert("1.0", draft)
            self.after(0, _fill)
        except Exception as e:
            log(f"❌ LLM draft failed: {e}")


    # ── Send reply ────────────────────────────────────────────────────


    def _t9_send_reply(self):
        em = self._t9_selected_email
        if not em:
            messagebox.showwarning("No email selected", "Select an email first.")
            return
        reply_text = self.t9_reply.get("1.0", "end").strip()
        if not reply_text:
            messagebox.showwarning("Empty reply", "Write a reply before sending.")
            return
        if not messagebox.askyesno("Send Reply?",
            f"Send reply to:\n  {em['sender']}\n\nSubject: Re: {em['subject'][:60]}"):
            return
        threading.Thread(target=self._t9_send_worker,
                         args=(em, reply_text), daemon=True).start()


    def _t9_send_worker(self, em: dict, reply_text: str):
        log = self._t9_log
        try:
            # ── Send via existing SMTP (same path as every other tab) ──
            subject = ("Re: " + em["subject"]
                       if not em["subject"].lower().startswith("re:")
                       else em["subject"])
            ok = send_smtp(
                self.smtp_conf,
                [em["sender_email"]],
                subject=subject,
                body=reply_text,
                log=log,
            )
            if not ok:
                raise RuntimeError("send_smtp returned False — check SMTP config.")


            # ── Mark as \Answered via IMAP ──
            try:
                imap = self._t9_imap()
                imap.select("INBOX")
                imap.store(em["id"].encode(), "+FLAGS", "\\Answered")
                log("  Marked as \\Answered in INBOX")
            except Exception as _imap_err:
                log(f"  ⚠️  Could not mark as answered: {_imap_err}")


            log(f"✅ Reply sent to {em['sender_email']}")


            # Update local state
            em["responded"] = True
            self._t9_clinical_emails  = [e for e in self._t9_clinical_emails
                                           if e["id"] != em["id"]]
            self._t9_responded_emails.insert(0, em)
            self.after(0, self._t9_refresh_list)
            self.after(0, lambda: messagebox.showinfo(
                "Sent", f"Reply sent to {em['sender_email']}."))
        except Exception as e:
            log(f"❌ Send failed: {e}\n{traceback.format_exc()}")
            self.after(0, lambda: messagebox.showerror("Send failed", str(e)))




def main():
    _ensure_scaffold()
    app = NPGSuite()
    app.mainloop()




if __name__ == "__main__":
    main()
