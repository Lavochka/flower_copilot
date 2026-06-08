# Инструкция по деплою GulCard на VPS (Ubuntu)

## 1. Подготовка системы
Обновите пакеты и установите необходимые зависимости:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx certbot python3-certbot-nginx -y
```

## 2. Настройка проекта
Перейдите в папку проекта, создайте виртуальное окружение и установите библиотеки:
```bash
cd ~/gulcard_project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Отредактируйте файл `.env`, вставив туда свой токен бота и домен:
```env
BOT_TOKEN=ваш_токен_от_BotFather
BASE_URL=https://gulcard.uz
DATABASE_URL=sqlite:////home/ubuntu/gulcard_project/gulcard.db
SHOP_NAME="Имя Вашего Магазина"
SHOP_LOGO_PATH="./static/logo.png"
```

## 3. Настройка Nginx и SSL
Создайте конфиг для сайта:
`sudo nano /etc/nginx/sites-available/gulcard`

Вставьте (замените `gulcard.uz` на ваш домен):
```nginx
server {
    server_name gulcard.uz;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /home/ubuntu/gulcard_project/static;
    }
}
```
Активируйте конфиг и получите SSL:
```bash
sudo ln -s /etc/nginx/sites-available/gulcard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo certbot --nginx -d gulcard.uz
```

## 4. Автозапуск (Systemd)
Чтобы бот и сайт работали всегда, создадим службы.

**Для веб-сайта:**
`sudo nano /etc/systemd/system/gulcard_web.service`
```ini
[Unit]
Description=GulCard Web App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/gulcard_project
Environment="PATH=/home/ubuntu/gulcard_project/venv/bin"
ExecStart=/home/ubuntu/gulcard_project/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 web.app:app

[Install]
WantedBy=multi-user.target
```

**Для бота:**
`sudo nano /etc/systemd/system/gulcard_bot.service`
```ini
[Unit]
Description=GulCard Telegram Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/gulcard_project
Environment="PATH=/home/ubuntu/gulcard_project/venv/bin"
ExecStart=/home/ubuntu/gulcard_project/venv/bin/python3 bot/main.py

[Install]
WantedBy=multi-user.target
```

Запустите их:
```bash
sudo systemctl enable gulcard_web gulcard_bot
sudo systemctl start gulcard_web gulcard_bot
```

## 5. Авто-очистка (Cron)
Чтобы файлы удалялись через 7 дней, добавьте задачу в планировщик:
`crontab -e`
Добавьте в конец строки:
`0 3 * * * /home/ubuntu/gulcard_project/venv/bin/python3 /home/ubuntu/gulcard_project/utils/cleaner.py`
(Это будет запускать очистку в 3 часа ночи каждый день).
