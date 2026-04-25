from django.urls import path

from apps.api.views import ActivateView, AdminLicenseListView, CheckStatusView, SyncReportView

urlpatterns = [
    path("activate/", ActivateView.as_view(), name="activate"),
    path("check-status/", CheckStatusView.as_view(), name="check-status"),
    path("sync-report/", SyncReportView.as_view(), name="sync-report"),
    path("admin/licenses/", AdminLicenseListView.as_view(), name="admin-licenses"),
]
