from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Exists, OuterRef, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.licenses.models import License
from apps.licenses.services import generate_license
from apps.stores.models import Store


class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self) -> bool:
        return bool(self.request.user.is_superuser)


def _license_valid_qs(today):
    return License.objects.filter(
        store=OuterRef("pk"),
        is_active=True,
    ).filter(Q(end_date__isnull=True) | Q(end_date__gte=today))


def _license_expired_qs(today):
    return License.objects.filter(
        store=OuterRef("pk"),
        is_active=True,
        end_date__isnull=False,
        end_date__lt=today,
    )


def _has_any_active_license_row():
    return License.objects.filter(store=OuterRef("pk"), is_active=True)


class DashboardHomeView(SuperuserRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        expiring_threshold = today + timedelta(days=3)

        stores = Store.objects.all().prefetch_related(
            Prefetch(
                "licenses",
                queryset=License.objects.filter(is_active=True).order_by("-created_at"),
            )
        )
        licenses = License.objects.select_related("store").all()

        q = self.request.GET.get("q", "").strip()
        status_filter = self.request.GET.get("status", "")
        license_status = self.request.GET.get("license_status", "").strip()

        if q:
            stores = stores.filter(
                Q(name__icontains=q) | Q(owner_name__icontains=q) | Q(phone__icontains=q)
            )
        if status_filter in {"active", "inactive"}:
            stores = stores.filter(is_active=status_filter == "active")

        if license_status == "valid":
            stores = stores.filter(Exists(_license_valid_qs(today)))
        elif license_status == "expired":
            stores = stores.filter(Exists(_license_expired_qs(today)))
        elif license_status == "none":
            stores = stores.filter(~Exists(_has_any_active_license_row()))

        valid_license_q = Q(is_active=True) & (Q(end_date__isnull=True) | Q(end_date__gte=today))

        ctx["stores"] = stores[:50]
        ctx["recent_licenses"] = licenses.order_by("-created_at")[:40]
        ctx["stats"] = {
            "total_stores": Store.objects.count(),
            "active_licenses": License.objects.filter(valid_license_q).count(),
            "expiring_soon": License.objects.filter(
                is_active=True,
                end_date__isnull=False,
                end_date__gte=today,
                end_date__lte=expiring_threshold,
            ).count(),
        }
        ctx["notifications"] = License.objects.filter(
            is_active=True,
            end_date__isnull=False,
            end_date__gte=today,
            end_date__lte=expiring_threshold,
        ).select_related("store")[:10]
        ctx["license_status"] = license_status
        return ctx


class StoresListView(SuperuserRequiredMixin, TemplateView):
    template_name = "stores/list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        stores = (
            Store.objects.all()
            .prefetch_related(
                Prefetch(
                    "licenses",
                    queryset=License.objects.filter(is_active=True).order_by("-created_at"),
                )
            )
            .order_by("-created_at")
        )
        q = self.request.GET.get("q", "").strip()
        if q:
            stores = stores.filter(
                Q(name__icontains=q) | Q(owner_name__icontains=q) | Q(phone__icontains=q)
            )
        ctx["stores"] = stores[:200]
        ctx["today"] = today
        return ctx


class LicensesListView(SuperuserRequiredMixin, TemplateView):
    template_name = "licenses/list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["licenses"] = License.objects.select_related("store").order_by("-created_at")[:200]
        return ctx


class AssignLicenseView(SuperuserRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        store_id = request.POST.get("store_id")
        license_type = request.POST.get("license_type", "").strip()
        valid_types = {
            License.LicenseType.MONTHLY,
            License.LicenseType.YEARLY,
            License.LicenseType.LIFETIME,
        }
        if not store_id or license_type not in valid_types:
            messages.error(request, "Invalid store or license type.")
            return redirect(_safe_next(request.POST.get("next")))

        store = get_object_or_404(Store, pk=store_id)
        new_license = generate_license(store=store, license_type=license_type, start_date=timezone.localdate())
        messages.success(
            request,
            f"Litsenziya yaratildi. Kalit (bir marta nusxalang): {new_license.activation_key}",
        )
        return redirect(_safe_next(request.POST.get("next")))


def _safe_next(next_url: str | None) -> str:
    if not next_url or not next_url.startswith("/") or next_url.startswith("//"):
        return reverse("dashboard-home")
    return next_url
