# WeatherLab (курсовая)

Сервис анализа погоды из нескольких источников на **Django**, с хранением данных в SQLite через **SQLAlchemy** и сессиями в БД (Django sessions). Шаблоны — **Jinja2**, flash‑сообщения — Django Messages.

## Что реализовано
- SQLite3 + SQLAlchemy для таблиц `weather_queries`, `weather_results`.
- Сессии в БД (Django `django.contrib.sessions`).
- Jinja2-шаблоны.
- Формы через Django Forms.
- Маршрутизация через Django `urls.py` (аналог BluePrint в Django).
- Flash-сообщения через Django Messages.
- Поиск города в шапке и переход на главную по клику на название.
- Несколько источников погоды: Open‑Meteo, wttr.in, met.no.
- Расширенные параметры: ощущается как, давление, видимость, осадки, порывы, облачность.

## Быстрый старт (локально)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python manage.py migrate
python manage.py init_sqlalchemy
python manage.py runserver
```
Откройте `http://127.0.0.1:8000`.

## Переменные окружения
- `SECRET_KEY` — секрет для сессий.
- `DEBUG` — `1` или `0`.
- `ALLOWED_HOSTS` — список доменов через запятую.
- `WEATHER_TIMEOUT_SECONDS` — таймаут запросов к API (в секундах).

> Примечание: для Python 3.13 требуется SQLAlchemy `>= 2.0.36`.

## Deploy на PythonAnywhere (бесплатно)
1. Зарегистрируйтесь на pythonanywhere.com.
2. Загрузите проект или сделайте `git clone`.
3. Создайте virtualenv и установите зависимости:
```bash
mkvirtualenv weatherlab
pip install -r requirements.txt
```
4. Выполните миграции:
```bash
python manage.py migrate
python manage.py init_sqlalchemy
```
5. В разделе Web App выберите `Manual configuration` → `Python 3.x`.
6. В WSGI-файле укажите:
```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "weatherlab.settings")
application = get_wsgi_application()
```
7. Добавьте статические файлы:
- URL: `/static/`
- Path: `/home/youruser/yourproject/weather/static/`
8. Перезагрузите приложение (`Reload`).
