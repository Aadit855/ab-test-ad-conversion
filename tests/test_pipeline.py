"""Checks for the A/B pipeline. Run from the project root: python -m pytest -q"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from analysis import compute, normal_sf, srm_chi_square, two_proportion  # noqa: E402
from build import build  # noqa: E402


@pytest.fixture(scope="module")
def metrics(tmp_path_factory):
    db = tmp_path_factory.mktemp("wh") / "test.duckdb"
    return compute(build(db))


def test_every_user_is_counted_once(metrics):
    assert metrics["users"] == {"ad": 564577, "psa": 23524}


def test_conversion_rates_match_source(metrics):
    assert metrics["conversions"] == {"ad": 14423, "psa": 420}
    assert metrics["test"]["treatment_rate"] == pytest.approx(0.025547, abs=1e-6)


def test_ad_lift_is_significant_and_positive(metrics):
    assert metrics["test"]["p_value_two_sided"] < 0.001
    low, high = metrics["test"]["ci95_absolute"]
    assert 0 < low < high


def test_sample_split_is_flagged_not_assumed_50_50(metrics):
    assert metrics["sample_ratio_check"]["mismatch_at_p_0_001"] is True


def test_two_proportion_matches_hand_calculation():
    # 50/1000 vs 40/1000: pooled p = 0.045, z = 0.01 / sqrt(0.045*0.955*0.002) ~ 1.0786
    result = two_proportion(50, 1000, 40, 1000)
    assert result["z"] == pytest.approx(1.0786, abs=1e-3)


def test_normal_tail_known_value():
    assert normal_sf(1.96) == pytest.approx(0.025, abs=1e-4)


def test_srm_no_flag_for_balanced_split():
    assert srm_chi_square(5000, 5000)["mismatch_at_p_0_001"] is False
