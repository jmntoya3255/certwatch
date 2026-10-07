# Monitor de Certificados SSL

Bot para Linux que monitorea la vigencia de certificados SSL de tu
infraestructura, con panel web para administrar el inventario de sitios y
envío de correos con semáforo de colores (🔴 rojo / 🟡 amarillo / 🟠 naranja / 🟢 verde).

## Semáforo de estados

| Estado   | Condición                              |
|----------|-----------------------------------------|
| 🔴 Rojo   | Menos de `RED_DAYS` días para vencer (por defecto 15)   |
| 🟡 Amarillo | Menos de `YELLOW_DAYS` días (por defecto 30)          |
| 🟠 Naranja | Entre `YELLOW_DAYS` y `GREEN_DAYS` días (zona de atención, 30–44 por defecto) |
| 🟢 Verde  | `GREEN_DAYS` días o más (por defecto 45)               |

> Nota: pediste explícitamente "<15 rojo", "<30 amarillo" y ">45 verde", lo
> que deja sin definir el tramo 30–45. Para no dejar sitios sin clasificar
> agregué la categoría "naranja" para ese rango. Todos los umbrales son
> ajustables en `.env`.

## 1. Instalación

```bash
# Copia la carpeta a tu servidor, por ejemplo en /opt/ssl-monitor
sudo mkdir -p /opt/ssl-monitor
sudo cp -r ssl-monitor/* /opt/ssl-monitor/
cd /opt/ssl-monitor

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
nano .env   # completa SMTP, destinatarios y umbrales
```

### Gmail
Si usas Gmail como SMTP, debes generar una "Contraseña de aplicación" en tu
cuenta de Google (no funciona con tu contraseña normal si tienes 2FA activo).

## 2. Panel web (para administrar el inventario de sitios)

Ejecutar manualmente para probar:
```bash
source venv/bin/activate
python3 app.py
```
Abre `http://IP_DEL_SERVIDOR:5000` en tu navegador. Desde ahí puedes:
- Agregar sitios (nombre + URL u host:puerto).
- Activar/desactivar sitios sin borrarlos.
- Eliminar sitios.
- Botón "Revisar ahora y enviar correo" para forzar un chequeo manual.

### Dejarlo corriendo permanentemente (systemd)
```bash
sudo cp ssl-monitor-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ssl-monitor-web
sudo systemctl status ssl-monitor-web
```
Recomendado: pon Nginx/Apache como proxy inverso delante del puerto 5000 con
autenticación básica o VPN, ya que este panel no trae login propio.

## 3. Chequeo diario automático (cron)

El script `monitor.py` revisa todos los sitios activos y envía el correo.

```bash
crontab -e
```
Agrega, por ejemplo, para correr todos los días a las 7:00 am:
```
0 7 * * * /opt/ssl-monitor/venv/bin/python3 /opt/ssl-monitor/monitor.py >> /opt/ssl-monitor/monitor.log 2>&1
```

### Variantes
- Enviar correo siempre (reporte diario completo), aunque todo esté verde:
  ```
  0 7 * * * /opt/ssl-monitor/venv/bin/python3 /opt/ssl-monitor/monitor.py
  ```
- Enviar correo SOLO cuando haya algo en rojo/amarillo/naranja/error (útil si
  además quieres una revisión más frecuente, ej. cada 6 horas, sin recibir
  spam cuando todo está bien):
  ```
  0 */6 * * * /opt/ssl-monitor/venv/bin/python3 /opt/ssl-monitor/monitor.py --only-alerts
  ```
- Puedes combinar ambas líneas: un reporte diario completo a las 7am y
  revisiones de alerta más frecuentes durante el día.

"Cuando yo defina" = tú controlas la periodicidad totalmente editando el
crontab (puedes poner la hora y frecuencia que quieras), y además siempre
puedes forzar un chequeo inmediato desde el botón del panel web.

## 4. Estructura del proyecto

```
ssl-monitor/
├── app.py                 # Panel web (Flask) - administrar inventario
├── monitor.py             # Script para cron - chequea y envía correo
├── ssl_checker.py         # Lógica de verificación TLS
├── email_sender.py        # Generación y envío del correo HTML
├── database.py            # Persistencia en SQLite (sites.db)
├── config.py              # Carga de configuración desde .env
├── templates/             # Vistas HTML del panel
├── static/style.css       # Estilos del panel
├── requirements.txt
├── .env.example
└── ssl-monitor-web.service
```

## 5. Notas de seguridad

- El panel web no tiene autenticación propia: expórtalo solo en tu red
  interna/VPN, o ponle un proxy inverso con usuario/contraseña o SSO delante.
- Las credenciales SMTP se guardan en `.env` (fuera de control de versiones).
- El chequeo TLS no valida la cadena de confianza (no es necesario para
  saber cuándo vence), solo lee la fecha de expiración del certificado que
  realmente sirve cada sitio.
