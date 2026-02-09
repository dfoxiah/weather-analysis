import json

from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render

from .forms import WeatherForm
from .services import SOURCES, analyze, coerce_float
from .sqlalchemy_db import SessionLocal, init_db
from .sqlalchemy_models import WeatherQuery, WeatherResult


def _get_client_id(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _header_context(request):
    header_city = request.GET.get("city") or request.session.get("last_city", "")
    header_sources = [
        {"key": key, "label": item["label"]} for key, item in SOURCES.items()
    ]
    return {"header_city": header_city, "header_sources": header_sources}


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
