from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth import login
from .forms import SignUpForm

def home_view(request):
    return render(request, "home/home.html")  # corrige le chemin si besoin

class SignUpView(CreateView):
    template_name = "registration/signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("dashboard:analyzer")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return redirect(self.get_success_url())
