import os
import requests
from dotenv import load_dotenv
from typing import Dict, Optional

load_dotenv()

# ─── DEFAULTS ────────────────────────────────────────────────────────────────
DEFAULT_BASE_URL      = os.getenv("GRAFANA_URL", "http://localhost:3000")
DEFAULT_DASHBOARD_UID = "cehe9q80jzjeoc"
DEFAULT_DASHBOARD_SLUG= "test"
DEFAULT_PANEL_ID      = 3
DEFAULT_TIME_FROM     = "2021-07-05T00:00:00.000Z"
DEFAULT_TIME_TO       = "2025-04-23T00:00:00.000Z"
DEFAULT_WIDTH         = 1200
DEFAULT_HEIGHT        = 600
DEFAULT_ORG_ID        = 1
DEFAULT_TIMEZONE      = "browser"
DEFAULT_TEMPLATE_VARS = {
    "var-Portfolio":  "my-portfolio3",
    "var-pair":       "$__all",
    "var-indicators": "$__all",
}

API_KEY = os.getenv("GRAFANA_API_KEY")
if not API_KEY:
    raise RuntimeError("Please set GRAFANA_API_KEY in your environment")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


def get_panel_png(
    base_url: str = DEFAULT_BASE_URL,
    dashboard_uid: str = DEFAULT_DASHBOARD_UID,
    dashboard_slug: str = DEFAULT_DASHBOARD_SLUG,
    panel_id: int = DEFAULT_PANEL_ID,
    time_from: str = DEFAULT_TIME_FROM,
    time_to: str = DEFAULT_TIME_TO,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    org_id: int = DEFAULT_ORG_ID,
    timezone: str = DEFAULT_TIMEZONE,
    template_vars: Optional[Dict[str, str]] = None,
) -> bytes:
    """
    Fetch a PNG image of a Grafana panel.
    Raises RuntimeError on any error.
    """
    # --- validate inputs ---
    if not base_url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid base_url: {base_url!r}")
    if panel_id <= 0:
        raise ValueError(f"panel_id must be > 0, got {panel_id}")
    params = {
        "orgId":    org_id,
        "panelId":  panel_id,
        "from":     time_from,
        "to":       time_to,
        "timezone": timezone,
        "width":    width,
        "height":   height,
    }
    # merge template vars
    vars_to_use = template_vars or DEFAULT_TEMPLATE_VARS
    for k in vars_to_use:
        if not k.startswith("var-"):
            raise ValueError(f"Template variable key must start with 'var-', got {k!r}")
    params.update(vars_to_use)

    url = f"{base_url.rstrip('/')}/render/d-solo/{dashboard_uid}/{dashboard_slug}"
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=30)
    except requests.RequestException as e:
        raise RuntimeError(f"Error connecting to Grafana at {url}: {e}") from e

    if resp.status_code != 200:
        # include body snippet for debugging
        snippet = resp.text[:200].replace("\n", " ")
        raise RuntimeError(
            f"Grafana returned status {resp.status_code}: {snippet}"
        )

    ctype = resp.headers.get("Content-Type", "")
    if not ctype.startswith("image/png"):
        snippet = resp.text[:200].replace("\n", " ")
        raise RuntimeError(
            f"Expected image/png, got {ctype!r}: {snippet}"
        )

    return resp.content


def save_panel_png(
    filepath: str,
    base_url: str                = DEFAULT_BASE_URL,
    dashboard_uid: str           = DEFAULT_DASHBOARD_UID,
    dashboard_slug: str          = DEFAULT_DASHBOARD_SLUG,
    panel_id: int                = DEFAULT_PANEL_ID,
    time_from: str               = DEFAULT_TIME_FROM,
    time_to: str                 = DEFAULT_TIME_TO,
    width: int                   = DEFAULT_WIDTH,
    height: int                  = DEFAULT_HEIGHT,
    org_id: int                  = DEFAULT_ORG_ID,
    timezone: str                = DEFAULT_TIMEZONE,
    template_vars: Optional[Dict[str, str]] = None,
) -> None:
    """
    Download and save a Grafana panel as a PNG file.
    Raises RuntimeError on failure.
    """
    try:
        png = get_panel_png(
            base_url=base_url,
            dashboard_uid=dashboard_uid,
            dashboard_slug=dashboard_slug,
            panel_id=panel_id,
            time_from=time_from,
            time_to=time_to,
            width=width,
            height=height,
            org_id=org_id,
            timezone=timezone,
            template_vars=template_vars,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to download panel PNG: {e}") from e

    try:
        with open(filepath, "wb") as f:
            f.write(png)
    except OSError as e:
        raise RuntimeError(f"Failed to write file {filepath}: {e}") from e
