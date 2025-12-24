import math

from utils.parse_numeric_with_metadata import parse_numeric_with_metadata


def test_parse_indian_number_lakh_crore():
    meta = parse_numeric_with_metadata("65,00,000")
    assert meta["value"] == 6500000.0

    meta = parse_numeric_with_metadata("2.8 Cr")
    assert meta["value"] == 2.8 * 10_000_000

    meta = parse_numeric_with_metadata("1.25 Cr")
    assert meta["value"] == 1.25 * 10_000_000

    meta = parse_numeric_with_metadata("7.5 Lakh")
    assert meta["value"] == 7.5 * 100_000


def test_parse_lpa_salary():
    meta = parse_numeric_with_metadata("6.5 LPA")
    assert meta["is_lpa"] is True
    assert meta["value"] == 6.5
    assert meta["inr"] == 6.5 * 100_000


def test_parse_area_sqft_to_sqm():
    meta = parse_numeric_with_metadata("185,000 sq.ft")
    assert meta["unit"] == "sqft"
    assert meta["value"] == 185000.0
    sqm = meta["sqm"]
    assert sqm is not None
    # 185000 / 10.7639 ≈ 17178
    assert math.isclose(sqm, 185000.0 / 10.7639, rel_tol=1e-4)



