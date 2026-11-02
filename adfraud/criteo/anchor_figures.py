#!/usr/bin/env python3
"""Anchor figures from published full-file Criteo v2.1 aggregates (no raw data needed).

Values: control and treatment conversion rates and exposure among treated users, as
recomputed on the full v2.1 file by the public notebook repository
firefly1248/criteo-uplift-modeling. Cross-checked against Diemert et al. (2021),
Table 1: 0.85 x 0.3089% + 0.15 x 0.1938% = 0.29% overall conversion, and
0.1152 / 0.3089 = 37.3% relative uplift (Table 1 reports 37.2%, which matches when
relative uplift is taken over the treated rate).
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CONTROL, TREATED, FIRST_STAGE = 0.1938, 0.3089, 3.60     # percent
ITT = 0.1152                                              # percentage points, as published (rates above are rounded)
LATE = ITT / (FIRST_STAGE / 100)                          # percentage points
THEMES = {
    "light": dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", grid="#e4e3df", blue="#2a78d6", orange="#eb6834"),
    "dark": dict(surface="#1a1a19", ink="#f0efec", ink2="#c3c2b7", grid="#33332f", blue="#3987e5", orange="#d95926"),
}


def setup(th, title, sub):
    fig, ax = plt.subplots(figsize=(9.6, 5.4), dpi=170)
    fig.patch.set_facecolor(th["surface"]); ax.set_facecolor(th["surface"])
    fig.subplots_adjust(left=0.1, right=0.95, top=0.8, bottom=0.17)
    fig.text(0.1, 0.93, title, fontsize=15, fontweight="bold", color=th["ink"])
    fig.text(0.1, 0.875, sub, fontsize=10.5, color=th["ink2"])
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(th["grid"])
    ax.tick_params(colors=th["ink2"], length=0)
    ax.grid(True, axis="y", color=th["grid"], linewidth=0.8); ax.set_axisbelow(True)
    return fig, ax


def main():
    out = Path(__file__).resolve().parent / "figures"
    out.mkdir(exist_ok=True)
    plt.rcParams["font.family"] = ["Inter", "DejaVu Sans", "sans-serif"]
    for mode, th in THEMES.items():
        fig, ax = setup(th, "Criteo v2.1: the randomized offer raises conversion",
                        "Conversion rate by randomized group, full file (13,979,592 users)")
        bars = ax.bar(["Randomized control (15%)", "Randomized treatment (85%)"], [CONTROL, TREATED],
                      width=0.5, color=[th["blue"], th["orange"]])
        for b, v in zip(bars, (CONTROL, TREATED)):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.006, f"{v:.4f}%", ha="center", color=th["ink"], fontsize=11)
        ax.set_ylabel("Conversion rate (%)", color=th["ink2"])
        ax.set_ylim(0, TREATED * 1.2)
        for lab in ax.get_xticklabels():
            lab.set_color(th["ink"])
        fig.text(0.1, 0.035, "Published full-file aggregates (firefly1248/criteo-uplift-modeling), consistent with Diemert et al. (2021), Table 1.",
                 fontsize=8.5, color=th["ink2"])
        fig.savefig(out / f"criteo_v21_conversion_rates-{mode}.png", facecolor=th["surface"]); plt.close(fig)

        fig, ax = setup(th, "From offer effect to exposure effect",
                        "Only 3.6% of offered users were exposed, so the per-exposure effect is ~28× the offer effect")
        ax.axis("off")
        cells = [("Offer effect (ITT)", f"+{ITT:.4f} pts", th["blue"]),
                 ("÷ Exposure rate among offered", f"{FIRST_STAGE:.2f}%", th["ink2"]),
                 ("= Exposure effect (Wald LATE)", f"≈ +{LATE:.2f} pts", th["orange"])]
        for i, (lab, val, col) in enumerate(cells):
            x = 0.04 + i * 0.33
            ax.text(x, 0.62, val, fontsize=30, fontweight="bold", color=col, transform=ax.transAxes)
            ax.text(x, 0.45, lab, fontsize=11.5, color=th["ink"], transform=ax.transAxes)
        ax.text(0.04, 0.15, "Valid under the usual IV assumptions: random offer, offer acts only through exposure,\n"
                            "and no exposure in control (one-sided non-compliance, true in this design).",
                fontsize=10, color=th["ink2"], transform=ax.transAxes)
        fig.text(0.1, 0.035, "Derived: LATE = ITT ÷ first stage from the published aggregates. Row-level run pending.",
                 fontsize=8.5, color=th["ink2"])
        fig.savefig(out / f"criteo_v21_itt_to_late-{mode}.png", facecolor=th["surface"]); plt.close(fig)
    print(f"ITT {ITT:.4f} pts, LATE {LATE:.2f} pts; wrote anchor figures to {out}")


if __name__ == "__main__":
    main()
