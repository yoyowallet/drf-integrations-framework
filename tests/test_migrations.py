import pytest
from django.core.management import call_command
from django.test import override_settings
from io import StringIO


@pytest.mark.django_db
@override_settings(MIGRATION_MODULES={})
def test_no_missing_migrations():
    """
    Calls the makemigrations command in dry run mode and check the output to see if
    there were any changes.
    """
    stdout = StringIO()
    call_command("makemigrations", dry_run=True, stdout=stdout, verbosity=3)

    migrations_missing = "No changes detected" not in stdout.getvalue()

    if migrations_missing:
        pytest.fail("There are missing migrations:\n{}".format(stdout.getvalue()))
