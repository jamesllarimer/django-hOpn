from django.urls import path

from . import views
app_name = "sportsSignUp"
urlpatterns = [
    path("", views.index, name="index"),
    path('active-leagues/', views.active_leagues, name='active_leagues'),
]