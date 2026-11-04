import pytest
from services.api.db import Database
from packages.contracts.models import InvestigationStatus
import tempfile
import os

def test_database_transitions():
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tf:
        temp_db = tf.name
    try:
        db = Database(db_path=temp_db)
        inv = db.create_investigation("TEST-01", "http://localhost:3001/checkout", "Apply EXPIRED10")
        assert inv["status"] == InvestigationStatus.CREATED.value

        db.update_status("TEST-01", InvestigationStatus.REPRODUCING, "system", {})
        assert db.get_investigation("TEST-01")["status"] == InvestigationStatus.REPRODUCING.value

        db.update_status("TEST-01", InvestigationStatus.REPRODUCED, "@bug-reproducer", {"failures_observed": 3})
        assert db.get_investigation("TEST-01")["status"] == InvestigationStatus.REPRODUCED.value
    finally:
        if os.path.exists(temp_db):
            os.remove(temp_db)

