"""
Migration 0006 – Unique magic_number

Step 1 (data): Assign a distinct random magic number (100000–999999) to every
               session that shares the old hardcoded default (234567 or 123456)
               or collides with another row.
Step 2 (schema): Add the unique constraint to the column.
"""
import random
from django.db import migrations, models


def _rand_magic():
    """Inline default callable for the migration (matches model's _generate_magic_number)."""
    return random.randint(100_000, 999_999)


def _assign_unique_magic_numbers(apps, schema_editor):
    """
    Walk all sessions ordered by id and give each one a magic number that is
    not already taken by a previously-processed row.
    """
    LiveTradingSession = apps.get_model('trading_sessions_api', 'LiveTradingSession')

    used = set()
    # First pass: collect magic numbers that are already unique so we don't
    # accidentally replace them.
    seen_magic = {}
    for session in LiveTradingSession.objects.order_by('id'):
        m = session.magic_number
        if m not in seen_magic:
            seen_magic[m] = session.id  # first owner keeps it
        # Mark all as seen for conflict detection below

    # Second pass: assign new unique values to every session that either
    # (a) collides with another session, or (b) uses a legacy default.
    LEGACY_DEFAULTS = {234567, 123456}

    for session in LiveTradingSession.objects.order_by('id'):
        m = session.magic_number
        first_owner = seen_magic.get(m)

        needs_new = (
            m in LEGACY_DEFAULTS          # old hardcoded default
            or first_owner != session.id  # duplicate – not the first owner
        )

        if needs_new:
            while True:
                candidate = random.randint(100_000, 999_999)
                if candidate not in used and candidate not in LEGACY_DEFAULTS:
                    session.magic_number = candidate
                    session.save(update_fields=['magic_number'])
                    used.add(candidate)
                    break
        else:
            used.add(m)


class Migration(migrations.Migration):

    dependencies = [
        ('trading_sessions_api', '0005_livetradingsession_exit_mode_and_risk_default'),
    ]

    operations = [
        # Step 1: fix the data before the unique constraint is applied
        migrations.RunPython(
            _assign_unique_magic_numbers,
            reverse_code=migrations.RunPython.noop,
        ),

        # Step 2: enforce uniqueness at the DB level
        migrations.AlterField(
            model_name='livetradingsession',
            name='magic_number',
            field=models.IntegerField(
                unique=True,
                default=_rand_magic,
                help_text=(
                    'Unique MT5 magic number identifying this session. '
                    'Auto-generated if not supplied.'
                ),
            ),
        ),
    ]
