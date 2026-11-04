from urllib.parse import urlparse
import ipaddress

ALLOWED_NETLOCS = {
    "demo-app:3000",
    "localhost:3000",
    "127.0.0.1:3000",
    "localhost:3001",
    "127.0.0.1:3001",
}

BLOCKED_IPS = {
    "169.254.169.254",
    "127.0.0.1",
}

def is_target_url_allowed(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        netloc = parsed.netloc.lower()
        if netloc in ALLOWED_NETLOCS:
            return True
        hostname = parsed.hostname
        if not hostname:
            return False
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
        except ValueError:
            pass
        return False
    except Exception:
        return False
