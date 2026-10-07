import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sites.db")

# --- SMTP ---
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)
# Varios destinatarios separados por coma: correo1@x.com,correo2@x.com
EMAIL_TO = [e.strip() for e in os.getenv("EMAIL_TO", "").split(",") if e.strip()]

# --- Umbrales de días para el semáforo (configurables) ---
RED_DAYS = int(os.getenv("RED_DAYS", "15"))       # < 15 dias => ROJO
YELLOW_DAYS = int(os.getenv("YELLOW_DAYS", "30"))  # < 30 dias => AMARILLO
GREEN_DAYS = int(os.getenv("GREEN_DAYS", "45"))    # >= 45 dias => VERDE
# Entre YELLOW_DAYS y GREEN_DAYS => NARANJA (zona de atención, no definida
# explícitamente por el usuario, se agrega para no dejar huecos)

# --- Web app ---
SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esta-clave-en-produccion")
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", "5000"))

# Timeout de conexion TLS al validar cada sitio (segundos)
CHECK_TIMEOUT = int(os.getenv("CHECK_TIMEOUT", "8"))
