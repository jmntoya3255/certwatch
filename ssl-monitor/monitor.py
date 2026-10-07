#!/usr/bin/env python3
"""
Ejecuta el chequeo de todos los sitios activos y envia el reporte por correo.

Uso:
    python3 monitor.py               # revisa y envia siempre (modo diario)
    python3 monitor.py --only-alerts # solo envia correo si hay rojo/amarillo/naranja/error
"""
import argparse
import sys

import database
import email_sender
from ssl_checker import get_cert_expiry


def run(only_alerts=False):
    database.init_db()
    sites = database.list_sites(only_active=True)

    if not sites:
        print("No hay sitios configurados. Agrega alguno desde el panel web.")
        return

    results = []
    for site in sites:
        r = get_cert_expiry(site["hostname"], site["port"])
        database.save_check_result(site["id"], r)
        merged = {**site, **r}
        results.append(merged)
        print(f"[{merged['status']}] {site['label']} ({site['hostname']}:{site['port']}) "
              f"-> {r.get('days_remaining')} dias restantes" if r.get("ok")
              else f"[error] {site['label']} -> {r.get('error')}")

    if only_alerts:
        alert_states = {"rojo", "amarillo", "naranja", "error"}
        if not any((s.get("status") in alert_states) for s in results):
            print("Todo en verde, no se envia correo (--only-alerts).")
            return

    prefix = "Alerta" if only_alerts else "Reporte diario"
    email_sender.send_report(results, force_subject_prefix=prefix)
    print("Correo enviado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--only-alerts", action="store_true",
                         help="Envia el correo solo si algun sitio esta en rojo/amarillo/naranja/error")
    args = parser.parse_args()
    try:
        run(only_alerts=args.only_alerts)
    except Exception as e:
        print(f"Error ejecutando el monitor: {e}", file=sys.stderr)
        sys.exit(1)
