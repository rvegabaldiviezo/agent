from datetime import datetime, timedelta, timezone
import requests

# Tool para obtener la fecha actual
def get_today_date() -> dict:
    """
    Devuelve la fecha de hoy en formato YYYY-MM-DD (UTC).
    """
    today = datetime.now(timezone.utc).date()  # timezone-aware
    return {
        "status": "success",
        "today": today.isoformat()
    }