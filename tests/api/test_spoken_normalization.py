from services.reproducer.scenario_parser import normalize_coupon_code, parse_spoken_scenario

def test_normalize_spoken_coupon_codes():
    assert normalize_coupon_code("expired ten") == "EXPIRED10"
    assert normalize_coupon_code("expired 10") == "EXPIRED10"
    assert normalize_coupon_code("EXPIRED TEN") == "EXPIRED10"
    assert normalize_coupon_code("save twenty") == "SAVE20"
    assert normalize_coupon_code("save 20") == "SAVE20"
    assert normalize_coupon_code("SAVE20") == "SAVE20"

def test_parse_spoken_scenario_extraction():
    parsed = parse_spoken_scenario("@repro reproduce on http://localhost:3001/checkout with coupon code expired ten")
    assert parsed["coupon_code"] == "EXPIRED10"
    assert parsed["target_url"] == "http://localhost:3001/checkout"

    parsed_default = parse_spoken_scenario("please test expired 10 on checkout")
    assert parsed_default["coupon_code"] == "EXPIRED10"
    assert parsed_default["target_url"] == "http://localhost:3001/checkout"
