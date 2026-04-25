# VPS Deploy (SQLite + Nginx + Gunicorn + systemd)

## 1) Server tayyorlash
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip nginx
```

## 2) Loyihani joylash
```bash
sudo mkdir -p /var/www/geeks_pos_dashboard
sudo chown -R $USER:$USER /var/www/geeks_pos_dashboard
git clone <your-repo-url> /var/www/geeks_pos_dashboard
cd /var/www/geeks_pos_dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt gunicorn
```

## 3) Environment
```bash
cp .env.example .env
```

`.env` ichida kamida:
- `DEBUG=False`
- `ALLOWED_HOSTS=your-domain.com,www.your-domain.com`
- `SECRET_KEY=<strong-random-secret>`
- `CLIENT_API_KEY=<long-random-api-key>`

## 4) Django migrate/static
```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## 5) SQLite uchun ruxsatlar
```bash
sudo chown -R www-data:www-data /var/www/geeks_pos_dashboard
sudo chmod 750 /var/www/geeks_pos_dashboard
sudo chmod 664 /var/www/geeks_pos_dashboard/db.sqlite3
```

## 6) Gunicorn service
```bash
sudo cp deploy/gunicorn.service /etc/systemd/system/geeks_pos_dashboard.service
sudo systemctl daemon-reload
sudo systemctl enable geeks_pos_dashboard
sudo systemctl start geeks_pos_dashboard
sudo systemctl status geeks_pos_dashboard
```

## 7) Nginx config
```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/geeks_pos_dashboard
sudo ln -s /etc/nginx/sites-available/geeks_pos_dashboard /etc/nginx/sites-enabled/geeks_pos_dashboard
sudo nginx -t
sudo systemctl reload nginx
```

## 8) HTTPS (Let’s Encrypt tavsiya)
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## 9) Operatsion buyruqlar
```bash
sudo systemctl restart geeks_pos_dashboard
sudo journalctl -u geeks_pos_dashboard -f
sudo systemctl reload nginx
```

## 10) SQLite bilan ishonchli ishlash bo‘yicha tavsiyalar
- Backup: `db.sqlite3` ni har kuni cron bilan nusxalash.
- Og‘ir parallel yozuv bo‘lsa kelajakda PostgreSQL’ga o‘tish.
- `sync-report` endpointda bulk payloadni kichik batchlarda yuborish.
