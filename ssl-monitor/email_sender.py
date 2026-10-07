import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import config

COLOR_HEX = {
    "rojo": "#e53935",
    "amarillo": "#fbc02d",
    "naranja": "#fb8c00",
    "verde": "#43a047",
    "error": "#757575",
    "desconocido": "#9e9e9e",
}

LABELS = {
    "rojo": "CRÍTICO",
    "amarillo": "ADVERTENCIA",
    "naranja": "ATENCIÓN",
    "verde": "OK",
    "error": "ERROR DE CONEXIÓN",
    "desconocido": "SIN DATOS",
}


def _row(site):
    status = site.get("status") or "desconocido"
    color = COLOR_HEX.get(status, "#9e9e9e")
    label = LABELS.get(status, status.upper())
    days = site.get("days_remaining")
    days_txt = f"{days} días" if days is not None else "-"
    expiry = site.get("expiry_date") or "-"
    error = site.get("error") or ""
    return f"""
    <tr>
      <td style="padding:8px;border:1px solid #ddd;">{site['label']}</td>
      <td style="padding:8px;border:1px solid #ddd;">{site['hostname']}:{site['port']}</td>
      <td style="padding:8px;border:1px solid #ddd;">{expiry}</td>
      <td style="padding:8px;border:1px solid #ddd;">{days_txt}</td>
      <td style="padding:8px;border:1px solid #ddd;background:{color};color:#fff;text-align:center;font-weight:bold;">{label}</td>
      <td style="padding:8px;border:1px solid #ddd;font-size:12px;color:#900;">{error}</td>
    </tr>"""


def build_html_report(sites):
    rows = "\n".join(_row(s) for s in sites)
    return f"""
    <html><body style="font-family:Arial,sans-serif;">
      <h2>Reporte de vigencia de certificados SSL</h2>
      <p>Umbrales: rojo &lt; {config.RED_DAYS} días · amarillo &lt; {config.YELLOW_DAYS} días ·
         naranja &lt; {config.GREEN_DAYS} días · verde &ge; {config.GREEN_DAYS} días</p>
      <table style="border-collapse:collapse;width:100%;">
        <thead>
          <tr style="background:#333;color:#fff;">
            <th style="padding:8px;">Sitio</th>
            <th style="padding:8px;">Host:Puerto</th>
            <th style="padding:8px;">Vencimiento</th>
            <th style="padding:8px;">Días restantes</th>
            <th style="padding:8px;">Estado</th>
            <th style="padding:8px;">Detalle error</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>
    </body></html>
    """


def worst_status(sites):
    order = ["rojo", "error", "amarillo", "naranja", "desconocido", "verde"]
    statuses = {s.get("status") or "desconocido" for s in sites}
    for st in order:
        if st in statuses:
            return st
    return "verde"


def send_email(subject, html_body, to_addrs=None):
    to_addrs = to_addrs or config.EMAIL_TO
    if not to_addrs:
        raise ValueError("No hay destinatarios configurados (EMAIL_TO en .env)")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = ", ".join(to_addrs)
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        if config.SMTP_USE_TLS:
            server.starttls()
        if config.SMTP_USER:
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.sendmail(config.EMAIL_FROM, to_addrs, msg.as_string())


def send_report(sites, force_subject_prefix=None):
    worst = worst_status(sites)
    icons = {"rojo": "🔴", "amarillo": "🟡", "naranja": "🟠", "verde": "🟢", "error": "⚠️"}
    icon = icons.get(worst, "ℹ️")
    prefix = force_subject_prefix or "Reporte diario"
    subject = f"{icon} {prefix} de certificados SSL - estado general: {LABELS.get(worst, worst).upper()}"
    html = build_html_report(sites)
    send_email(subject, html)
