"""Actual urgent restriction hides romantic sponsored profiles before worker refresh."""
import pytest
from django.test import Client
from test_promotion_exposure import purchased
from test_report_decisions import action
from test_report_inspection import case, reviewer
from test_reports import directory, photo_environment  # noqa: F401
from test_sitemaps import NS, urls

from apps.core.models import Person, User
from apps.listings import tasks
from apps.listings.models import Favorite, Listing, PublicationState, Revision
from apps.listings.publication_state import refresh_all
from apps.safety.models import ReportAction, Restriction, UrgentReportAlert

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('language', ['es', 'en'])
def test_urgent_restriction_hides_every_surface_and_preserves_peer_and_audit(
    request, settings, monkeypatch, record_property, language
):
    _, listing, entitlement = purchased(request, settings)
    public = Client()
    photo = listing.approved_revision.photos.get(removed_at__isnull=True)
    peer = Person.objects.get(subject__username='fixture-v1-model-a').listing
    peer_before = (Listing.objects.filter(pk=peer.pk).values().get(),
                   Revision.objects.filter(pk=peer.approved_revision_id).values().get())
    visitor = User.objects.get(username='fixture-v1-visitor')
    private = Client()
    private.force_login(visitor)
    detail = f'/{language}/listing/{listing.pk}/'
    image = detail + f'photo/{photo.pk}/'
    assert public.get(detail).status_code == 200
    response = public.get(image)
    assert response.status_code == 200
    response.close()
    assert private.post(detail + 'favorite/').status_code == 302
    report = case(public, listing.person)
    assert report.priority == 0
    _, staff = reviewer()
    urgent = f'/{language}/moderation/reports/urgent-alerts/'
    assert staff.post(urgent, {'report_id': report.pk}).status_code == 302
    acknowledged = UrgentReportAlert.objects.get(report=report)
    def decision(operation):
        path, values = action(staff, report, operation)
        return path.replace('/en/', f'/{language}/', 1), values
    path, values = decision('claim')
    assert staff.post(path, values).status_code == 302
    assert staff.post(f'/{language}/moderation/reports/{report.pk}/',
                      {'purpose': 'Inspect synthetic urgent evidence before restriction'}).status_code == 200
    monkeypatch.setattr(tasks.refresh_publication_state, 'delay', lambda *a, **k: None)
    refresh_all()
    assert PublicationState.objects.get(listing=listing).eligible
    path, values = decision('restrict')
    assert staff.post(path, values).status_code == 302
    assert PublicationState.objects.get(listing=listing).eligible  # Deliberately stale projection.
    assert Restriction.objects.get(report=report).active
    for refreshed in (False, True):
        if refreshed:
            refresh_all()
        for promotional in (False, True):
            settings.PROMOTION_TEST_MODE = promotional
            result = public.get(f'/{language}/')
            ids = [item.pk for item in result.context['page'].object_list]
            assert listing.pk not in ids and peer.pk in ids
            assert public.get(detail).status_code == public.get(image).status_code == 404
            favorites = private.get(f'/{language}/favorites/')
            assert favorites.status_code == 200 and favorites['Cache-Control'] == 'private, no-store'
            assert all(not entry['visible'] for entry in favorites.context['entries'])
            assert str(listing.pk).encode() not in favorites.content
            assert private.post(detail + 'favorite/').status_code == 404
            locations = [node.find('s:loc', NS).text for node in urls(public)]
            assert all(str(listing.pk) not in value for value in locations)
            assert any(str(peer.pk) in value for value in locations)
    assert staff.post(path, values).status_code == 302
    assert ReportAction.objects.filter(report=report, operation='restrict').count() == 1
    alert = UrgentReportAlert.objects.get(report=report)
    assert (alert.acknowledged_by_id, alert.acknowledged_at) == (
        acknowledged.acknowledged_by_id, acknowledged.acknowledged_at)
    entitlement.refresh_from_db()
    assert entitlement.order.status == 'paid'
    assert Favorite.objects.filter(user=visitor, listing=listing).count() == 1
    assert (Listing.objects.filter(pk=peer.pk).values().get(),
            Revision.objects.filter(pk=peer.approved_revision_id).values().get()) == peer_before
    record_property('urgent_restriction_before_worker', True)
    record_property('all_public_surfaces_guarded', True)
    record_property('peer_preserved', True)
