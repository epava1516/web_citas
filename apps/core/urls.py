from django.urls import path

from apps.listings import views as listings
from apps.mediafiles import views as mediafiles

from . import accounts, agencies, legal, mfa, verification

urlpatterns = [
    path("photos/<uuid:photo_id>/reorder/", mediafiles.reorder, name="photo_reorder"),
    path("draft/<uuid:revision_id>/photos/upload/", mediafiles.upload, name="photo_upload"),
    path("photos/<uuid:photo_id>/private/", mediafiles.private_photo, name="private_photo"),
    path("photos/<uuid:photo_id>/remove/", mediafiles.remove, name="photo_remove"),
    path("person/<uuid:person_id>/listing/start/", listings.start, name="listing_start"),
    path("draft/<uuid:revision_id>/<int:step>/", listings.edit, name="draft_edit"),
    path("person/create/", verification.individual, name="individual_create"),
    path("person/<uuid:person_id>/verification/", verification.status, name="person_verification"),
    path("person/<uuid:person_id>/age/", verification.age, name="age_check"),
    path("person/<uuid:person_id>/phone/", verification.phone_start, name="phone_start"),
    path("phone/<uuid:challenge_id>/confirm/", verification.phone_confirm, name="phone_confirm"),
    path(
        "person/<uuid:person_id>/consent/invite/",
        verification.invite_consent,
        name="consent_invite",
    ),
    path("person/<uuid:person_id>/consent/", verification.self_consent, name="self_consent"),
    path(
        "representation/<uuid:invitation_id>/<str:raw>/",
        verification.accept_consent,
        name="consent_accept",
    ),
    path("person/<uuid:person_id>/revoke/", verification.revoke, name="representation_revoke"),
    path(
        "person/<uuid:person_id>/transfer/", verification.transfer, name="representation_transfer"
    ),
    path("account/mfa/enroll/", mfa.enroll, name="mfa_enroll"),
    path("account/mfa/", mfa.challenge, name="mfa_challenge"),
    path("agency/create/", agencies.create, name="agency_create"),
    path("agency/<uuid:agency_id>/", agencies.panel, name="agency_panel"),
    path("agency/<uuid:agency_id>/invite/", agencies.invite, name="agency_invite"),
    path("agency/<uuid:agency_id>/people/add/", agencies.add_person, name="agency_add_person"),
    path(
        "agency/<uuid:agency_id>/people/<uuid:person_id>/assign/",
        agencies.assign,
        name="agency_assign",
    ),
    path(
        "agency/<uuid:agency_id>/members/<int:member_id>/revoke/",
        agencies.revoke_member,
        name="agency_revoke",
    ),
    path(
        "agency/invitation/<uuid:invitation_id>/<str:raw>/",
        agencies.accept_invitation,
        name="agency_accept_invitation",
    ),
    path("account/resend/", accounts.resend, name="resend"),
    path("account/accept/", accounts.accept_current, name="accept_current"),
    path("account/signup/", accounts.signup, name="signup"),
    path("account/login/", accounts.signin, name="login"),
    path("account/logout/", accounts.signout, name="logout"),
    path("account/recover/", accounts.recover, name="recover"),
    path("account/token/<uuid:token_id>/<str:raw>/", accounts.token_view, name="account_token"),
    path("account/", accounts.dashboard, name="dashboard"),
    path("legal/", legal.index, name="legal_index"),
    path("legal/<slug:slug>/", legal.document, name="legal_document"),
]
