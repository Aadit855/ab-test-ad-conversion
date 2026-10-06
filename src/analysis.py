"""Two-proportion test, confidence interval, sample-ratio check, and power for the ad-vs-PSA test."""
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from build import build  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
FIG = ROOT / "figures"

Z_95 = 1.959964  # two-sided 95%
Z_80_POWER = 0.841621


def normal_sf(z: float) -> float:
    """Upper-tail probability of the standard normal."""
    return 0.5 * math.erfc(z / math.sqrt(2))


def two_proportion(x_t: int, n_t: int, x_c: int, n_c: int) -> dict:
    p_t, p_c = x_t / n_t, x_c / n_c
    diff = p_t - p_c
    pooled = (x_t + x_c) / (n_t + n_c)
    se_pooled = math.sqrt(pooled * (1 - pooled) * (1 / n_t + 1 / n_c))
    z = diff / se_pooled
    se_unpooled = math.sqrt(p_t * (1 - p_t) / n_t + p_c * (1 - p_c) / n_c)
    return {
        "treatment_rate": p_t,
        "control_rate": p_c,
        "absolute_lift": diff,
        "relative_lift": diff / p_c,
        "ci95_absolute": [diff - Z_95 * se_unpooled, diff + Z_95 * se_unpooled],
        "z": z,
        "p_value_two_sided": 2 * normal_sf(abs(z)),
    }


def srm_chi_square(n_t: int, n_c: int, expected_share_t: float = 0.5) -> dict:
    """Chi-square goodness-of-fit against the expected split. The planned split is not in the source."""
    total = n_t + n_c
    exp_t, exp_c = total * expected_share_t, total * (1 - expected_share_t)
    chi2 = (n_t - exp_t) ** 2 / exp_t + (n_c - exp_c) ** 2 / exp_c
    return {
        "expected_share_treatment": expected_share_t,
        "observed_share_treatment": round(n_t / total, 4),
        "chi_square": round(chi2, 1),
        # With 1 degree of freedom, p < 0.001 when chi2 > 10.83.
        "mismatch_at_p_0_001": chi2 > 10.83,
    }


def sample_size_per_arm(p_control: float, abs_mde: float) -> int:
    """Users per arm for 80% power, two-sided alpha 0.05, 1:1 split."""
    p_treat = p_control + abs_mde
    p_bar = (p_control + p_treat) / 2
    num = (
        Z_95 * math.sqrt(2 * p_bar * (1 - p_bar))
        + Z_80_POWER * math.sqrt(p_control * (1 - p_control) + p_treat * (1 - p_treat))
    ) ** 2
    return math.ceil(num / abs_mde**2)


def compute(con) -> dict:
    rows = {r[0]: r for r in con.execute(
        "SELECT variant, users, conversions FROM mart_variant_summary"
    ).fetchall()}
    _, n_t, x_t = rows["ad"]
    _, n_c, x_c = rows["psa"]

    result = two_proportion(x_t, n_t, x_c, n_c)
    incremental = result["absolute_lift"] * n_t

    return {
        "users": {"ad": n_t, "psa": n_c},
        "conversions": {"ad": x_t, "psa": x_c},
        "test": {k: (round(v, 6) if isinstance(v, float) else v) for k, v in result.items()
                 if k != "ci95_absolute"}
        | {"ci95_absolute": [round(v, 6) for v in result["ci95_absolute"]]},
        "incremental_conversions_estimate": round(incremental),
        "sample_ratio_check": srm_chi_square(n_t, n_c),
        "power": {
            "users_per_arm_for_0_25pp_mde_at_psa_baseline": sample_size_per_arm(x_c / n_c, 0.0025),
            "users_per_arm_for_0_5pp_mde_at_psa_baseline": sample_size_per_arm(x_c / n_c, 0.005),
        },
    }


def chart(metrics: dict) -> None:
    FIG.mkdir(exist_ok=True)
    test = metrics["test"]
    fig, ax = plt.subplots(figsize=(6.5, 3.5))
    labels = ["PSA (control)", "Ad (treatment)"]
    rates = [test["control_rate"] * 100, test["treatment_rate"] * 100]
    ax.bar(labels, rates, color=["#9aa5b1", "#2a6f97"])
    ax.set_ylabel("Conversion rate (%)")
    ax.set_title("Ad exposure lifts conversion from 1.79% to 2.55%")
    for i, v in enumerate(rates):
        ax.text(i, v + 0.05, f"{v:.2f}%", ha="center")
    ax.set_ylim(0, max(rates) * 1.25)
    fig.tight_layout()
    fig.savefig(FIG / "conversion_by_variant.png", dpi=150)
    plt.close(fig)


def main() -> None:
    con = build()
    metrics = compute(con)
    OUT.mkdir(exist_ok=True)
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2))
    chart(metrics)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
