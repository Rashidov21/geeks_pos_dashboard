from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import TemplateView

from apps.licenses.models import License
from apps.stores.models import Store


class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class DashboardHomeView(SuperuserRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        expiring_threshold = today + timedelta(days=3)

        stores = Store.objects.all()
        licenses = License.objects.select_related("store").all()

        q = self.request.GET.get("q", "").strip()
        status_filter = self.request.GET.get("status", "")
        if q:
            stores = stores.filter(Q(name__icontains=q) | Q(owner_name__icontains=q) | Q(phone__icontains=q))
        if status_filter in {"active", "inactive"}:
            stores = stores.filter(is_active=status_filter == "active")

        ctx["stores"] = stores[:50]
        ctx["stats"] = {
            "total_stores": Store.objects.count(),
            "active_licenses": licenses.filter(is_active=True).count(),
            "expiring_soon": licenses.filter(
                is_active=True, end_date__isnull=False, end_date__gte=today, end_date__lte=expiring_threshold
            ).count(),
        }
        ctx["notifications"] = licenses.filter(
            is_active=True, end_date__isnull=False, end_date__gte=today, end_date__lte=expiring_threshold
        )[:10]
        return ctx
