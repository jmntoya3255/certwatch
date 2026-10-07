import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse

from cryptography import x509
from cryptography.x509.oid import NameOID

import config


def normalize_hostname(raw):
    """Acepta 'example.com', 'https://example.com/path', 'example.com:8443', etc."""
    raw = raw.strip()
    if "://" in raw:
        parsed = urlparse(raw)
        host = parsed.hostname
        port = parsed.port or 443
    elif ":" in raw and not raw.count(":") > 1:
        host, port_s = raw.split(":", 1)
        port = int(port_s)
    else:
        host = raw
        port = 443
    return host, port


def classify(days_remaining):
    if days_remaining is None:
        return "desconocido"
    if days_remaining < config.RED_DAYS:
        return "rojo"
    if days_remaining < config.YELLOW_DAYS:
        return "amarillo"
    if days_remaining < config.GREEN_DAYS:
        return "naranja"  # zona de atencion entre amarillo y verde
    return "verde"


def get_cert_expiry(hostname, port=443, timeout=None):
    """Se conecta al host:puerto, obtiene el certificado servido y calcula
    los dias restantes hasta su vencimiento. No valida la cadena de
    confianza (solo nos interesa la fecha de expiracion real servida)."""
    timeout = timeout or config.CHECK_TIMEOUT
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                der_cert = ssock.getpeercert(binary_form=True)
                if not der_cert:
                    raise ValueError("El servidor no devolvio informacion del certificado")

                cert = x509.load_der_x509_certificate(der_cert)

                # Compatibilidad con distintas versiones de la libreria cryptography
                if hasattr(cert, "not_valid_after_utc"):
                    expiry_dt = cert.not_valid_after_utc
                else:
                    expiry_dt = cert.not_valid_after.replace(tzinfo=timezone.utc)

                issuer = ""
                try:
                    issuer_attrs = cert.issuer.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)
                    if not issuer_attrs:
                        issuer_attrs = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
                    if issuer_attrs:
                        issuer = issuer_attrs[0].value
                except Exception:
                    issuer = ""

                days_remaining = (expiry_dt - datetime.now(timezone.utc)).days
                return {
                    "ok": True,
                    "expiry_date": expiry_dt.strftime("%Y-%m-%d"),
                    "days_remaining": days_remaining,
                    "issuer": issuer,
                    "status": classify(days_remaining),
                    "error": None,
                }
    except Exception as e:
        return {
            "ok": False,
            "expiry_date": None,
            "days_remaining": None,
            "issuer": None,
            "status": "error",
            "error": str(e),
        }
