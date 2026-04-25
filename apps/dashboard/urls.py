from django.contrib.auth import views as auth_views
from django.urls import path

from apps.dashboard.views import (
    AssignLicenseView,
    DashboardHomeView,
    LicensesListView,
    StoresListView,
)

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="auth/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("stores/", StoresListView.as_view(), name="stores-list"),
    path("licenses/", LicensesListView.as_view(), name="licenses-list"),
    path("assign-license/", AssignLicenseView.as_view(), name="assign-license"),
    path("", DashboardHomeView.as_view(), name="dashboard-home"),
]
