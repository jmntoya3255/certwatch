from flask import Flask, render_template, request, redirect, url_for, flash

import config
import database
import email_sender
from ssl_checker import get_cert_expiry, normalize_hostname

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


@app.route("/")
def index():
    database.init_db()
    sites = database.get_last_result_per_site()
    return render_template("index.html", sites=sites)


@app.route("/add", methods=["POST"])
def add():
    label = request.form.get("label", "").strip()
    raw_host = request.form.get("hostname", "").strip()
    if not label or not raw_host:
        flash("Debes indicar un nombre y una URL/host.", "error")
        return redirect(url_for("index"))
    try:
        host, port = normalize_hostname(raw_host)
        database.add_site(label, host, port)
        flash(f"Sitio '{label}' agregado.", "ok")
    except Exception as e:
        flash(f"No se pudo agregar: {e}", "error")
    return redirect(url_for("index"))


@app.route("/delete/<int:site_id>", methods=["POST"])
def delete(site_id):
    database.delete_site(site_id)
    flash("Sitio eliminado.", "ok")
    return redirect(url_for("index"))


@app.route("/toggle/<int:site_id>/<int:active>", methods=["POST"])
def toggle(site_id, active):
    database.toggle_site(site_id, bool(active))
    return redirect(url_for("index"))


@app.route("/check-now", methods=["POST"])
def check_now():
    sites = database.list_sites(only_active=True)
    if not sites:
        flash("No hay sitios activos para revisar.", "error")
        return redirect(url_for("index"))

    results = []
    for site in sites:
        r = get_cert_expiry(site["hostname"], site["port"])
        database.save_check_result(site["id"], r)
        results.append({**site, **r})

    try:
        email_sender.send_report(results, force_subject_prefix="Reporte manual")
        flash("Chequeo ejecutado y correo enviado.", "ok")
    except Exception as e:
        flash(f"Chequeo ejecutado pero el correo falló: {e}", "error")

    return redirect(url_for("index"))


if __name__ == "__main__":
    database.init_db()
    app.run(host=config.WEB_HOST, port=config.WEB_PORT, debug=False)
