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

def get_weather_and_time(city="Buenos Aires", country="Argentina"):
    location = f"{city},{country}"

    # Clima desde wttr.in (no requiere API key)
    weather_url = f"https://wttr.in/{location}?format=j1"
    try:
        w_resp = requests.get(weather_url, timeout=5).json()
        current = w_resp['current_condition'][0]
        temp = current['temp_C']
        desc = current['weatherDesc'][0]['value']
    except Exception:
        return f"❌ No se pudo obtener el clima para {location}"

    # Hora local desde worldtimeapi.org
    try:
        tz_url = f"http://worldtimeapi.org/api/timezone/America/Argentina/Buenos_Aires"
        t_resp = requests.get(tz_url, timeout=5).json()
        local_time = t_resp['datetime']
    except Exception:
        local_time = "Hora no disponible"

    result = f"🌤 Clima actual en {location}: {temp}°C, {desc}\n🕒 Hora local: {local_time}"
    return result
