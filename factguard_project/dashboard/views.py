from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse


def dashboard_view(request):
    return HttpResponse("<h1>Dashboard FactGuard</h1><p>Application en cours de développement</p>")
    return HttpResponse("Hello, world. You're at the dashboard index.") 