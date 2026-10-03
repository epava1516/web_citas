from django.urls import path

from apps.listings import (
    appeals,
    favorites,
    match_views,
    moderation_views,
    photo_appeals,
    photo_restrictions,
)
from apps.listings import views as listings
from apps.mediafiles import views as mediafiles

from . import (
    accounts,
    agencies,
    agency_appeals,
    legal,
    manager_appeals,
    manager_review,
    mfa,
    organization_review,
    verification,
)

urlpatterns = [
    path("favorites/", favorites.index, name="favorites"),
    path("listing/<uuid:listing_id>/favorite/", favorites.add, name="favorite_add"),
    path("favorites/<int:favorite_id>/remove/", favorites.remove, name="favorite_remove"),
    path("moderation/photo-appeals/", photo_appeals.queue, name="photo_appeal_queue"),
    path(
        "moderation/photo-appeals/<int:appeal_id>/",
        photo_appeals.review,
        name="photo_appeal_review",
    ),
    path(
        "person/photo-restrictions/<int:restriction_id>/",
        photo_restrictions.detail,
        name="photo_restriction",
    ),
    path(
        "agency/decisions/<int:decision_id>/appeal/",
        agency_appeals.submit,
        name="agency_appeal_submit",
    ),
    path("moderation/agency-appeals/", agency_appeals.queue, name="agency_appeal_queue"),
    path(
        "moderation/agency-appeals/<int:appeal_id>/",
        agency_appeals.review,
        name="agency_appeal_review",
    ),
    path(
        "person/manager-decisions/<int:decision_id>/appeal/",
        manager_appeals.submit,
        name="manager_appeal_submit",
    ),
    path("moderation/manager-appeals/", manager_appeals.queue, name="manager_appeal_queue"),
    path(
        "moderation/manager-appeals/<int:appeal_id>/",
        manager_appeals.review,
        name="manager_appeal_review",
    ),
    path("draft/decisions/<int:decision_id>/appeal/", appeals.submit, name="appeal_submit"),
    path("moderation/appeals/", appeals.queue, name="appeal_queue"),
    path("moderation/appeals/<int:appeal_id>/", appeals.review, name="appeal_review"),
    path("moderation/managers/", manager_review.queue, name="manager_queue"),
    path("moderation/managers/<uuid:person_id>/", manager_review.review, name="manager_review"),
    path("moderation/matches/", match_views.queue, name="match_queue"),
    path("moderation/matches/<int:match_id>/", match_views.review, name="match_review"),
    path(
        "moderation/matches/<int:match_id>/<str:side>/image/", match_views.image, name="match_image"
    ),
    path("moderation/listings/", moderation_views.queue, name="moderation_queue"),
    path(
        "moderation/listings/<uuid:revision_id>/", moderation_views.review, name="moderation_review"
    ),
    path(
        "moderation/photos/<uuid:photo_id>/", moderation_views.review_photo, name="moderation_photo"
    ),
    path("listing/<uuid:listing_id>/", moderation_views.public_detail, name="listing_detail"),
    path(
        "listing/<uuid:listing_id>/photo/<uuid:photo_id>/",
        moderation_views.public_photo,
        name="public_photo",
    ),
    path("moderation/organizations/", organization_review.queue, name="organization_queue"),
    path(
        "moderation/organizations/<uuid:agency_id>/",
        organization_review.review,
        name="organization_review",
    ),
    path("draft/<uuid:revision_id>/submit/", listings.send_for_review, name="submit_revision"),
    path("draft/<uuid:revision_id>/status/", listings.revision_status, name="revision_status"),
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
