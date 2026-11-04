import pytest
from services.reproducer.url_validator import is_target_url_allowed

def test_allowed_urls():
    assert is_target_url_allowed("http://demo-app:3000/checkout")
    assert is_target_url_allowed("http://localhost:3001/checkout")
    assert is_target_url_allowed("http://127.0.0.1:3001")

def test_blocked_urls():
    assert not is_target_url_allowed("http://169.254.169.254/latest/meta-data/")
    assert not is_target_url_allowed("http://evil-attacker.com/payload")
    assert not is_target_url_allowed("ftp://demo-app:3000/checkout")
    assert not is_target_url_allowed("http://10.0.0.1/admin")

