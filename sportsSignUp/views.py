from django.shortcuts import render
from django.http import HttpResponse
from .models import Sport, Team, Player, Division, League


def index(request):
    return render(request, "index.html")