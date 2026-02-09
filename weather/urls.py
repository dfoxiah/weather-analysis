from django.urls import path

from . import views

app_name = "weather"

urlpatterns = [
    path("", views.index, name="index"),
    path("result/<int:query_id>/", views.result, name="result"),
    path("history/", views.history, name="history"),
]
