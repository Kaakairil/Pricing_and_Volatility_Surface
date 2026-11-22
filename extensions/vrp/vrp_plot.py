"""VRP extension figure: VIX vs next-21d realized vol, 2018-now."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "extensions" / "vrp"


def main() -> None:
    df = pd.read_csv(OUT / "vrp_windows.csv", parse_dates=["date"])
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["date"], df["vix"] / 100.0, label="VIX (window start)", lw=1.2)
    ax.plot(df["date"], df["rv_next"], label="realized vol, next 21d", lw=1.2)
    ax.fill_between(
        df["date"],
        df["vix"] / 100.0,
        df["rv_next"],
        where=df["gap"] > 0,
        alpha=0.25,
        label="premium (VIX > realized)",
    )
    ax.set_xlabel("window start date")
    ax.set_ylabel("annualized volatility (decimal)")
    ax.set_title("Volatility risk premium: VIX vs subsequent SPY realized vol")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "vrp_premium.png", dpi=150)
    print(f"figure -> {OUT / 'vrp_premium.png'}")


if __name__ == "__main__":
    main()
