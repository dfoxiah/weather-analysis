from django.conf import settings
from django.urls import path

from . import views

app_name = "weather"

ADMIN_PATH = getattr(settings, "ADMIN_PATH", "control").strip("/") or "control"

urlpatterns = [
    path("", views.index, name="index"),
    path("result/<int:query_id>/", views.result, name="result"),
    path("history/", views.history, name="history"),
    path(f"{ADMIN_PATH}/", views.admin_panel, name="admin"),
    path(
        f"{ADMIN_PATH}/query/<int:query_id>/",
        views.admin_detail,
        name="admin_detail",
    ),
]
