from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("register", views.register, name="register"),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("multiple-datasources", views.data_sources, name="data_sources"),
    path("time-based", views.time_based, name="time_based"),
    path("daily-based", views.daily_based, name="daily_based"),
    path("box-plot", views.box_plot, name="box_plot"),
    path("season-wise", views.season_wise, name="season_wise"),
    path("yearly-average", views.yearly_average, name="yearly_average"),
]