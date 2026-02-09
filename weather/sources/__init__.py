from .open_meteo import fetch as fetch_open_meteo
from .met_no import fetch as fetch_met_no
from .wttr import fetch as fetch_wttr

SOURCES = {
    "open_meteo": {"label": "Open-Meteo", "fetch": fetch_open_meteo},
    "met_no": {"label": "met.no", "fetch": fetch_met_no},
    "wttr": {"label": "wttr.in", "fetch": fetch_wttr},
}
