from django.db import migrations


class Migration(migrations.Migration):
    """Formerly added the partial text-proof indexes of the retired projected read path.

    Emptied by MOD-05 so the retired module is not needed to load migrations; databases
    that applied the original operations drop the indexes in 0016.
    """

    dependencies = [
        ("catalog", "0005_promotionentitlement_last_checked_at"),
        ("core", "0015_user_account_erased_at"),
        ("listings", "0013_stored_search_document"),
    ]

    operations = []
