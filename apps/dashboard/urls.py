from django.contrib.auth import views as auth_views
from django.urls import path

from apps.dashboard.views import DashboardHomeView

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", DashboardHomeView.as_view(), name="dashboard-home"),
]
