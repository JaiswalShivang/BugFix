import re
from typing import Dict, Any

COUPON_NORMALIZATION_MAP = {
    "expired ten": "EXPIRED10",
    "expired 10": "EXPIRED10",
    "expired10": "EXPIRED10",
    "save twenty": "SAVE20",
    "save 20": "SAVE20",
    "save20": "SAVE20",
    "welcome ten": "WELCOME10",
    "welcome 10": "WELCOME10",
    "welcome10": "WELCOME10",
}

def normalize_coupon_code(raw: str) -> str:
    cleaned = raw.strip().lower()
    for phrase, replacement in COUPON_NORMALIZATION_MAP.items():
        if phrase in cleaned:
            return replacement
    token_match = re.search(r"\b[A-Za-z0-9_-]{3,15}\b", raw)
    if token_match:
        return token_match.group(0).upper()
    return raw.strip().upper()

def parse_spoken_scenario(text: str, default_target: str = "http://localhost:3001/checkout") -> Dict[str, Any]:
    target_match = re.search(r"https?://[^\s]+", text)
    target_url = target_match.group(0) if target_match else default_target

    coupon = "EXPIRED10"
    for phrase, mapped in COUPON_NORMALIZATION_MAP.items():
        if phrase in text.lower():
            coupon = mapped
            break

    return {
        "target_url": target_url,
        "coupon_code": coupon,
        "raw_text": text,
        "summary": f"Target: {target_url} · Coupon: {coupon}",
    }

