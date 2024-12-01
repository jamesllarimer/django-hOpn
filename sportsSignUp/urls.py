from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
app_name = "sportsSignUp"
urlpatterns = [
    path("", views.index, name="index"),
    path('active-leagues/', views.active_leagues, name='active_leagues'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
]