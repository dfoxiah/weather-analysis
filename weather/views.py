import json

from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from sqlalchemy import func

from .forms import WeatherForm
from .services import SOURCES, analyze, coerce_float
from .sqlalchemy_db import SessionLocal, init_db
from .sqlalchemy_models import WeatherQuery, WeatherResult

ADMIN_SESSION_KEY = "weather_admin"


def _get_client_id(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _header_context(request):
    header_city = request.GET.get("city") or request.session.get("last_city", "")
    header_sources = [
        {"key": key, "label": item["label"]} for key, item in SOURCES.items()
    ]
    return {
        "header_city": header_city,
        "header_sources": header_sources,
        "is_admin": _is_admin(request),
    }


def _is_admin(request):
    return bool(request.session.get(ADMIN_SESSION_KEY))


def _admin_enabled():
    return bool(getattr(settings, "ADMIN_PASSWORD", ""))


def index(request):
    init_db()
    choices = [(key, item["label"]) for key, item in SOURCES.items()]
    initial_city = request.GET.get("city") or request.session.get("last_city", "")
    if request.method == "POST":
        form = WeatherForm(request.POST, sources=choices)
    else:
        form = WeatherForm(None, sources=choices, initial={"city": initial_city})

    if request.method == "POST" and form.is_valid():
        city = form.cleaned_data["city"].strip()
        selected = form.cleaned_data["sources"]

        results = []
        errors = []

        for key in selected:
            fetch = SOURCES[key]["fetch"]
            try:
                data = fetch(city, timeout=settings.WEATHER_TIMEOUT_SECONDS)
                if data.get("error"):
                    errors.append(f"{SOURCES[key]['label']}: {data['error']}")
                    continue
                for key_name in [
                    "temperature_c",
                    "humidity",
                    "wind_kph",
                    "wind_gust_kph",
                    "feels_like_c",
                    "pressure_hpa",
                    "visibility_km",
                    "precip_mm",
                    "cloud_pct",
                ]:
                    data[key_name] = coerce_float(data.get(key_name))
                results.append(data)
            except Exception as exc:
                errors.append(f"{SOURCES[key]['label']}: {exc}")

        if not results:
            messages.error(request, "Не удалось получить данные ни из одного источника.")
            context = {"form": form}
            context.update(_header_context(request))
            return render(request, "weather/index.html", context, using="jinja2")

        summary = analyze(results)
        session_id = _get_client_id(request)

        with SessionLocal() as db:
            query = WeatherQuery(
                city=city,
                sources=",".join(selected),
                session_id=session_id,
                summary_json=json.dumps(summary, ensure_ascii=False),
            )
            db.add(query)
            db.flush()

            for item in results:
                db.add(
                    WeatherResult(
                        query_id=query.id,
                        source=item.get("source"),
                        temperature_c=item.get("temperature_c"),
                        humidity=item.get("humidity"),
                        wind_kph=item.get("wind_kph"),
                        wind_gust_kph=item.get("wind_gust_kph"),
                        feels_like_c=item.get("feels_like_c"),
                        pressure_hpa=item.get("pressure_hpa"),
                        visibility_km=item.get("visibility_km"),
                        precip_mm=item.get("precip_mm"),
                        cloud_pct=item.get("cloud_pct"),
                        condition=item.get("condition"),
                        raw_json=json.dumps(item.get("raw"), ensure_ascii=False),
                    )
                )

            db.commit()
            query_id = query.id

        request.session["last_city"] = city
        for err in errors:
            messages.warning(request, err)
        messages.success(request, "Данные получены.")
        return redirect("weather:result", query_id=query_id)

    if form.errors:
        messages.warning(request, "Проверьте введенные данные.")

    context = {"form": form}
    context.update(_header_context(request))
    return render(request, "weather/index.html", context, using="jinja2")


def result(request, query_id):
    init_db()
    session_id = _get_client_id(request)

    with SessionLocal() as db:
        query = db.query(WeatherQuery).filter_by(id=query_id).first()
        if not query:
            raise Http404("Запись не найдена")
        if query.session_id != session_id:
            messages.warning(request, "Нет доступа к этой записи.")
            return redirect("weather:index")

        summary = json.loads(query.summary_json) if query.summary_json else {}
        result_rows = (
            db.query(WeatherResult).filter_by(query_id=query_id).all()
        )
        results = [
            {
                "label": SOURCES.get(item.source, {}).get("label", item.source),
                "source": item.source,
                "temperature_c": item.temperature_c,
                "humidity": item.humidity,
                "wind_kph": item.wind_kph,
                "wind_gust_kph": item.wind_gust_kph,
                "feels_like_c": item.feels_like_c,
                "pressure_hpa": item.pressure_hpa,
                "visibility_km": item.visibility_km,
                "precip_mm": item.precip_mm,
                "cloud_pct": item.cloud_pct,
                "condition": item.condition,
            }
            for item in result_rows
        ]
        query_data = {
            "city": query.city,
            "created_at": query.created_at,
        }

    context = {"query": query_data, "summary": summary, "results": results}
    context.update(_header_context(request))
    return render(request, "weather/result.html", context, using="jinja2")


def history(request):
    init_db()
    session_id = _get_client_id(request)

    with SessionLocal() as db:
        items = (
            db.query(WeatherQuery)
            .filter_by(session_id=session_id)
            .order_by(WeatherQuery.created_at.desc())
            .limit(20)
            .all()
        )

        history_items = []
        for item in items:
            history_items.append(
                {
                    "id": item.id,
                    "city": item.city,
                    "created_at": item.created_at,
                    "summary": json.loads(item.summary_json) if item.summary_json else {},
                }
            )

    context = {"items": history_items}
    context.update(_header_context(request))
    return render(request, "weather/history.html", context, using="jinja2")


def _parse_limit(value, default=50, min_value=10, max_value=200):
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return default
    limit = max(min_value, min(limit, max_value))
    return limit


def admin_panel(request):
    init_db()
    admin_enabled = _admin_enabled()
    admin_username = getattr(settings, "ADMIN_USERNAME", "admin")
    admin_password = getattr(settings, "ADMIN_PASSWORD", "")
    is_admin = _is_admin(request)

    if request.method == "POST":
        action = request.POST.get("action", "")
        if action == "login":
            if not admin_enabled:
                messages.error(request, "Админка отключена: ADMIN_PASSWORD не задан.")
            else:
                username = request.POST.get("username", "").strip()
                password = request.POST.get("password", "")
                if username == admin_username and password == admin_password:
                    request.session[ADMIN_SESSION_KEY] = True
                    messages.success(request, "Вход выполнен.")
                    return redirect("weather:admin")
                messages.error(request, "Неверный логин или пароль.")
        elif action == "logout":
            request.session.pop(ADMIN_SESSION_KEY, None)
            messages.info(request, "Вы вышли из админки.")
            return redirect("weather:admin")
        elif action == "delete":
            if not is_admin:
                messages.error(request, "Нужна авторизация.")
                return redirect("weather:admin")
            try:
                query_id = int(request.POST.get("query_id", "0"))
            except ValueError:
                query_id = 0
            if query_id:
                with SessionLocal() as db:
                    query = db.query(WeatherQuery).filter_by(id=query_id).first()
                    if not query:
                        messages.warning(request, "Запись не найдена.")
                    else:
                        db.delete(query)
                        db.commit()
                        messages.success(request, f"Запрос #{query_id} удален.")
            else:
                messages.warning(request, "Некорректный идентификатор записи.")
            return redirect("weather:admin")
        elif action == "purge":
            if not is_admin:
                messages.error(request, "Нужна авторизация.")
                return redirect("weather:admin")
            with SessionLocal() as db:
                db.query(WeatherResult).delete()
                db.query(WeatherQuery).delete()
                db.commit()
            messages.success(request, "История очищена.")
            return redirect("weather:admin")

    filters = {
        "city": request.GET.get("city", "").strip(),
        "source": request.GET.get("source", "").strip(),
        "session_id": request.GET.get("session_id", "").strip(),
        "limit": request.GET.get("limit", "").strip(),
    }
    limit = _parse_limit(filters["limit"], default=50)
    filters["limit"] = str(limit)

    items = []
    stats = {
        "total_queries": 0,
        "total_results": 0,
        "unique_cities": 0,
        "latest_at": None,
        "filtered_total": 0,
    }

    if admin_enabled and is_admin:
        with SessionLocal() as db:
            stats["total_queries"] = (
                db.query(func.count(WeatherQuery.id)).scalar() or 0
            )
            stats["total_results"] = (
                db.query(func.count(WeatherResult.id)).scalar() or 0
            )
            stats["unique_cities"] = (
                db.query(func.count(func.distinct(WeatherQuery.city))).scalar()
                or 0
            )
            latest = (
                db.query(WeatherQuery.created_at)
                .order_by(WeatherQuery.created_at.desc())
                .first()
            )
            stats["latest_at"] = latest[0] if latest else None

            base = db.query(WeatherQuery)
            if filters["city"]:
                base = base.filter(WeatherQuery.city.ilike(f"%{filters['city']}%"))
            if filters["source"]:
                base = base.filter(
                    WeatherQuery.sources.like(f"%{filters['source']}%")
                )
            if filters["session_id"]:
                base = base.filter(
                    WeatherQuery.session_id == filters["session_id"]
                )

            stats["filtered_total"] = base.count()

            rows = (
                base.outerjoin(WeatherResult)
                .group_by(WeatherQuery.id)
                .with_entities(
                    WeatherQuery,
                    func.count(WeatherResult.id).label("result_count"),
                )
                .order_by(WeatherQuery.created_at.desc())
                .limit(limit)
                .all()
            )

            for query, result_count in rows:
                summary = json.loads(query.summary_json) if query.summary_json else {}
                source_keys = [
                    key for key in (query.sources or "").split(",") if key
                ]
                source_labels = [
                    SOURCES.get(key, {}).get("label", key) for key in source_keys
                ]
                items.append(
                    {
                        "id": query.id,
                        "city": query.city,
                        "created_at": query.created_at,
                        "session_id": query.session_id,
                        "summary": summary,
                        "result_count": result_count,
                        "sources_labels": source_labels,
                    }
                )

    sources_options = [
        {"key": key, "label": item["label"]} for key, item in SOURCES.items()
    ]
    limit_options = ["20", "50", "100", "200"]

    context = {
        "admin_enabled": admin_enabled,
        "is_admin": is_admin,
        "login_username": admin_username,
        "filters": filters,
        "items": items,
        "stats": stats,
        "sources_options": sources_options,
        "limit_options": limit_options,
    }
    context.update(_header_context(request))
    return render(request, "weather/admin.html", context, using="jinja2")


def admin_detail(request, query_id):
    init_db()
    if not _is_admin(request):
        messages.warning(request, "Нужна авторизация.")
        return redirect("weather:admin")

    with SessionLocal() as db:
        query = db.query(WeatherQuery).filter_by(id=query_id).first()
        if not query:
            raise Http404("Запись не найдена")

        summary = json.loads(query.summary_json) if query.summary_json else {}
        result_rows = db.query(WeatherResult).filter_by(query_id=query_id).all()
        results = [
            {
                "label": SOURCES.get(item.source, {}).get("label", item.source),
                "source": item.source,
                "temperature_c": item.temperature_c,
                "humidity": item.humidity,
                "wind_kph": item.wind_kph,
                "wind_gust_kph": item.wind_gust_kph,
                "feels_like_c": item.feels_like_c,
                "pressure_hpa": item.pressure_hpa,
                "visibility_km": item.visibility_km,
                "precip_mm": item.precip_mm,
                "cloud_pct": item.cloud_pct,
                "condition": item.condition,
            }
            for item in result_rows
        ]
        source_keys = [key for key in (query.sources or "").split(",") if key]
        source_labels = [
            SOURCES.get(key, {}).get("label", key) for key in source_keys
        ]
        query_data = {
            "id": query.id,
            "city": query.city,
            "created_at": query.created_at,
            "session_id": query.session_id,
            "sources_labels": source_labels,
        }

    context = {
        "query": query_data,
        "summary": summary,
        "results": results,
        "admin_view": True,
    }
    context.update(_header_context(request))
    return render(request, "weather/result.html", context, using="jinja2")
