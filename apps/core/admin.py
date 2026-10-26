"""Keep Group administration native, with current authority after target waits."""

from django.contrib import admin
from django.contrib.admin.actions import delete_selected as native_delete_selected
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import router, transaction

from .models import User


def current_group_actor(request, permission, database):
    original = request.user
    fresh = User._base_manager.using(database).filter(pk=original.pk).first()
    if (
        not fresh
        or not fresh.is_active
        or not fresh.is_staff
        or fresh.account_erased_at is not None
        or fresh.email_verified_at is None
        or not fresh.mfa_enabled
        or fresh.session_version != original.session_version
        or fresh.mfa_version != original.mfa_version
        or request.session.get("account_version") != original.session_version
        or request.session.get("mfa_version") != original.mfa_version
        or not fresh.has_perm("auth." + permission)
    ):
        raise PermissionDenied


class CurrentGroupAdmin(GroupAdmin):
    actions = ("delete_selected",)

    def _lock_group(self, obj, database):
        current = (
            self.model._base_manager.using(database)
            .select_for_update(of=("self",))
            .filter(pk=obj.pk)
            .first()
        )
        if current is None:
            raise PermissionDenied

    def save_model(self, request, obj, form, change):
        database = router.db_for_write(self.model)
        with transaction.atomic(using=database):
            if change:
                self._lock_group(obj, database)
            current_group_actor(request, "change_group" if change else "add_group", database)
            super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        database = router.db_for_write(self.model)
        with transaction.atomic(using=database):
            current_group_actor(request, "change_group" if change else "add_group", database)
            super().save_related(request, form, formsets, change)

    def delete_model(self, request, obj):
        database = router.db_for_write(self.model)
        with transaction.atomic(using=database):
            self._lock_group(obj, database)
            current_group_actor(request, "delete_group", database)
            super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        database = router.db_for_write(self.model)
        with transaction.atomic(using=database):
            list(
                queryset.using(database)
                .order_by("pk")
                .select_for_update(of=("self",))
            )
            current_group_actor(request, "delete_group", database)
            super().delete_queryset(request, queryset)

    @admin.action(
        permissions=("delete",), description=native_delete_selected.short_description
    )
    def delete_selected(self, request, queryset):
        database = router.db_for_write(self.model)
        with transaction.atomic(using=database):
            current_group_actor(request, "delete_group", database)
            return native_delete_selected(self, request, queryset)


admin.site.unregister(Group)
admin.site.register(Group, CurrentGroupAdmin)
