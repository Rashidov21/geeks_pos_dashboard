from datetime import date
import secrets

from dateutil.relativedelta import relativedelta
from django.db import transaction

from apps.licenses.models import License
from apps.stores.models import Store


def _generate_activation_key() -> str:
    return secrets.token_urlsafe(32)


def _calculate_dates(license_type: str, start: date) -> tuple[date, date | None]:
    if license_type == License.LicenseType.MONTHLY:
        return start, start + relativedelta(months=1)
    if license_type == License.LicenseType.YEARLY:
        return start, start + relativedelta(years=1)
    return start, None


@transaction.atomic
def generate_license(store: Store, license_type: str, start_date: date | None = None) -> License:
    start = start_date or date.today()
    start, end = _calculate_dates(license_type, start)

    License.objects.filter(store=store, is_active=True).update(is_active=False)

    return License.objects.create(
        store=store,
        activation_key=_generate_activation_key(),
        license_type=license_type,
        start_date=start,
        end_date=end,
        is_active=True,
    )
