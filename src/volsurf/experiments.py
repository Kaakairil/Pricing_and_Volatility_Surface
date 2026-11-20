"""Early-exercise premium experiment (Task 10, PRD §9.2 / RQ2).

Paired American and European CRR binomial prices over a moneyness/maturity
grid at documented SPY parameters; the premium (american - european) is the
value of early exercise. Same step count for both legs so tree
discretization bias cancels in the difference.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from volsurf.binomial import binomial_price

PREMIUM_COLUMNS = [
    "moneyness",
    "T",
    "option",
    "american",
    "european",
    "premium",
    "premium_pct",
]

# Documented fallback ATM sigma when no snapshot IV table is available
# (results/iv_table.csv near-term ATM median on 2026-11-16 was 0.195).
DEFAULT_ATM_SIGMA = 0.20


def _one(
    S: float, K: float, T: float, sigma: float, r: float, q: float, option: str, steps: int
) -> tuple[float, float]:
    """Paired (american, european) binomial prices at identical parameters."""
    am = binomial_price(S, K, T, sigma, r, q, option, steps=steps, american=True)
    eu = binomial_price(S, K, T, sigma, r, q, option, steps=steps, american=False)
    return am, eu


def _validate(S: float, steps: int) -> None:
    if not (isinstance(S, (int, float)) and S > 0):
        raise ValueError(f"spot must be a finite positive number, got {S!r}")
    if not isinstance(steps, int) or steps < 1:
        raise ValueError(f"steps must be a positive int, got {steps!r}")


def early_exercise_premium(
    S: float,
    moneyness: list[float],
    T_grid: list[float],
    sigma: float,
    r: float,
    q: float,
    steps: int = 1000,
) -> pd.DataFrame:
    """American - European binomial premium over the (moneyness, T) grid.

    Columns: moneyness, T, option, american, european, premium, premium_pct.
    premium is never negative (American >= European by construction, up to
    floating-point rounding).
    """
    _validate(S, steps)
    rows = []
    for m in moneyness:
        K = S * float(m)
        for T in T_grid:
            T = float(T)
            for option in ("call", "put"):
                am, eu = _one(S, K, T, sigma, r, q, option, steps)
                rows.append(
                    {
                        "moneyness": float(m),
                        "T": T,
                        "option": option,
                        "american": am,
                        "european": eu,
                        "premium": am - eu,
                        "premium_pct": (am - eu) / eu if eu > 0 else 0.0,
                    }
                )
    return pd.DataFrame(rows, columns=PREMIUM_COLUMNS)


def rate_sensitivity(
    S: float,
    moneyness: float,
    T: float,
    sigma: float,
    r_grid: list[float],
    q: float,
    steps: int = 1000,
) -> pd.DataFrame:
    """Premium vs rate over r_grid at fixed moneyness and maturity.

    Checks the PRD §9.2 pattern: put premium rises with rate, call premium
    (q > 0) falls.
    """
    _validate(S, steps)
    K = S * float(moneyness)
    rows = []
    for r in r_grid:
        for option in ("call", "put"):
            am, eu = _one(S, K, float(T), sigma, float(r), q, option, steps)
            rows.append(
                {
                    "r": float(r),
                    "moneyness": float(moneyness),
                    "T": float(T),
                    "option": option,
                    "american": am,
                    "european": eu,
                    "premium": am - eu,
                    "premium_pct": (am - eu) / eu if eu > 0 else 0.0,
                }
            )
    return pd.DataFrame(rows)


def write_experiment_outputs(df: pd.DataFrame, out_dir: Path | str, name: str) -> Path:
    """Write one experiment DataFrame to ``out_dir/name`` (creates the dir)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / name
    df.to_csv(path, index=False)
    return path


def plot_early_exercise_premium(df: pd.DataFrame, out_dir: Path | str) -> Path:
    """Premium by moneyness, one line per (option, T) — PRD §10 figure."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    for option, marker in (("call", "o"), ("put", "s")):
        sub = df[df.option == option]
        for T, grp in sub.groupby("T"):
            grp = grp.sort_values("moneyness")
            ax.plot(grp.moneyness, grp.premium, marker=marker, ms=4, label=f"{option} T={T:.3f}")
    ax.set_xlabel("moneyness K/S")
    ax.set_ylabel("early-exercise premium (american - european)")
    ax.set_title("Early-exercise premium by moneyness and maturity")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path = out / "early_exercise_premium.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
