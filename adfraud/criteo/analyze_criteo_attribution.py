#!/usr/bin/env python3
"""Criteo attribution-vs-incrementality transfer test.

Original design and pipeline by ChatGPT; revised by Claude to add Poisson-bootstrap
uncertainty, a weak-first-stage guard, geometry on continuous features only, a
first-stage confound check, and themed figures. All revisions are listed in README.md.

Estimands (Z = randomized offer `treatment`, A = actual `exposure`, Y = `conversion`
or `visit`, X = 12 anonymized pre-treatment features f0..f11):

    ITT  = E[Y|Z=1] - E[Y|Z=0]                       protected randomized anchor
    FS   = E[A|Z=1] - E[A|Z=0]                       first stage (E[A|Z=0] = 0 here)
    LATE = ITT / FS                                  Wald, under the usual IV assumptions
    OBS  = E[Y|A=1,Z=1] - E[Y|A=0,Z=1]               naive exposed-vs-unexposed attribution
    BIAS = OBS - LATE

Within exposure-propensity bins b (bins are defined on pre-treatment X only, so the
randomization holds inside each bin):

    d_b  = mean(Xg|A=1,Z=1,b) - mean(Xg|A=0,Z=1,b)   Xg = standardized geometry features
    C_b  = 1 / sqrt(u_b' R^-1 u_b),  u_b = d_b/|d_b| directional concealment capacity
    M_b  = sqrt(d_b' R^-1 d_b)                        Mahalanobis selection magnitude

R is the correlation matrix of the geometry features in the randomized control group.
By default the geometry uses only the 4 continuous features (f0, f2, f7, f10): the other
8 are hashed categorical codes (Diemert et al. 2021, Table 2), for which a covariance
matrix has no geometric meaning.

Uncertainty: every row gets B independent Poisson(1) weights (a streaming bootstrap),
so standard errors and confidence intervals cover per-bin estimates and the
geometry-vs-bias correlations without holding the data in memory. The propensity model
and bin edges are held fixed across replicates.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

FEATURES = [f"f{i}" for i in range(12)]
CONTINUOUS = ["f0", "f2", "f7", "f10"]
USECOLS = FEATURES + ["treatment", "conversion", "visit", "exposure"]
COUNTS = ["n_z0", "n_z1", "n_e1", "n_e0",
          "c_z0", "c_z1", "c_e1", "c_e0",
          "v_z0", "v_z1", "v_e1", "v_e0"]


def read_chunks(path, chunksize, max_rows=None):
    seen = 0
    for chunk in pd.read_csv(path, compression="gzip", usecols=USECOLS, chunksize=chunksize):
        if max_rows is not None and seen + len(chunk) > max_rows:
            chunk = chunk.iloc[: max_rows - seen]
        if len(chunk) == 0:
            break
        seen += len(chunk)
        yield chunk
        if max_rows is not None and seen >= max_rows:
            break


# --------------------------------------------------------------------------- #
# Pass 1: control-group moments and a treated-user sample for the propensity model
# --------------------------------------------------------------------------- #
def first_pass(path, chunksize, sample_n, seed, max_rows=None):
    rng = np.random.default_rng(seed)
    k = len(FEATURES)
    n0, sx, sxx = 0, np.zeros(k), np.zeros((k, k))
    samples, kept = [], 0
    target = min(1.0, 1.25 * sample_n / max(1, (max_rows or 13_979_592) * 0.85))
    for ch in read_chunks(path, chunksize, max_rows):
        x = ch[FEATURES].to_numpy(float)
        z = ch["treatment"].to_numpy(np.int8)
        xc = x[z == 0]
        n0 += len(xc)
        sx += xc.sum(axis=0)
        sxx += xc.T @ xc
        idx = np.flatnonzero(z == 1)
        if kept < 2 * sample_n and len(idx):
            take = idx[rng.random(len(idx)) < target]
            if len(take):
                samples.append(ch.iloc[take][FEATURES + ["exposure"]])
                kept += len(take)
    mu = sx / n0
    cov = (sxx - n0 * np.outer(mu, mu)) / (n0 - 1)
    sd = np.sqrt(np.clip(np.diag(cov), 0, None))
    sd[sd == 0] = 1.0
    corr = cov / np.outer(sd, sd)
    corr = (corr + corr.T) / 2
    samp = pd.concat(samples, ignore_index=True)
    if len(samp) > sample_n:
        samp = samp.sample(sample_n, random_state=seed)
    return mu, sd, corr, n0, samp


def fit_propensity(samp, mu, sd, bins, kind, seed):
    X = (samp[FEATURES].to_numpy(float) - mu) / sd
    A = samp["exposure"].to_numpy(np.int8)
    if kind == "logistic":
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(max_iter=500)
    else:
        from sklearn.ensemble import HistGradientBoostingClassifier
        model = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, random_state=seed)
    model.fit(X, A)
    p = model.predict_proba(X)[:, 1]
    edges = np.quantile(p, np.linspace(0, 1, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    for i in range(1, len(edges) - 1):
        if edges[i] <= edges[i - 1]:
            edges[i] = np.nextafter(edges[i - 1], np.inf)
    return model, edges


# --------------------------------------------------------------------------- #
# Pass 2: per-bin sums, point estimate (weight 1) plus B Poisson-bootstrap replicates
# --------------------------------------------------------------------------- #
def second_pass(path, chunksize, max_rows, mu, sd, geo_idx, model, edges, B, seed):
    nb, kg, R = len(edges) - 1, len(geo_idx), B + 1      # replicate 0 = point estimate
    acc = {c: np.zeros((nb, R)) for c in COUNTS}
    acc["x_e1"] = np.zeros((nb, R, kg))
    acc["x_e0"] = np.zeros((nb, R, kg))
    rng = np.random.default_rng(seed + 1)
    for ch in read_chunks(path, chunksize, max_rows):
        Xs = (ch[FEATURES].to_numpy(float) - mu) / sd
        Xg = Xs[:, geo_idx]
        z = ch["treatment"].to_numpy(np.int8)
        a = ch["exposure"].to_numpy(np.int8)
        yc = ch["conversion"].to_numpy(np.int8)
        yv = ch["visit"].to_numpy(np.int8)
        b = np.clip(np.digitize(model.predict_proba(Xs)[:, 1], edges[1:-1]), 0, nb - 1)
        W = np.empty((len(z), R))
        W[:, 0] = 1.0
        W[:, 1:] = rng.poisson(1.0, size=(len(z), B))
        masks = {"z0": z == 0, "z1": z == 1, "e1": (z == 1) & (a == 1), "e0": (z == 1) & (a == 0)}
        for g, m in masks.items():
            for bb in range(nb):
                mm = m & (b == bb)
                if not mm.any():
                    continue
                w = W[mm]
                acc[f"n_{g}"][bb] += w.sum(axis=0)
                acc[f"c_{g}"][bb] += yc[mm] @ w
                acc[f"v_{g}"][bb] += yv[mm] @ w
                if g in ("e1", "e0"):
                    acc[f"x_{g}"][bb] += w.T @ Xg[mm]
    return acc


def estimates(acc, Rinv):
    """Per-bin and global estimates for every replicate: arrays shaped (bins+1, R)."""
    tot = {k: np.concatenate([v, v.sum(axis=0, keepdims=True)], axis=0) for k, v in acc.items()}
    with np.errstate(divide="ignore", invalid="ignore"):
        out = {"first_stage": tot["n_e1"] / tot["n_z1"]}
        for y, nm in (("c", "conv"), ("v", "visit")):
            r0, r1 = tot[f"{y}_z0"] / tot["n_z0"], tot[f"{y}_z1"] / tot["n_z1"]
            re1, re0 = tot[f"{y}_e1"] / tot["n_e1"], tot[f"{y}_e0"] / tot["n_e0"]
            itt = r1 - r0
            late = itt / out["first_stage"]
            obs = re1 - re0
            out.update({f"{nm}_rate_control": r0, f"{nm}_rate_treated": r1, f"{nm}_itt": itt,
                        f"{nm}_late_wald": late, f"{nm}_obs": obs, f"{nm}_bias": obs - late})
        d = tot["x_e1"] / tot["n_e1"][..., None] - tot["x_e0"] / tot["n_e0"][..., None]
        md2 = np.einsum("brk,kl,brl->br", d, Rinv, d)
        eu = np.linalg.norm(d, axis=-1)
        out["selection_euclidean"] = eu
        out["selection_mahalanobis"] = np.sqrt(np.clip(md2, 0, None))
        out["concealment_capacity"] = eu / np.sqrt(np.clip(md2, 1e-300, None))
    for k in ("n_z0", "n_z1", "n_e1"):
        out[k] = tot[k]
    return out


def corr_stats(x, y):
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 4:
        return np.nan, np.nan
    return stats.pearsonr(x[ok], y[ok]).statistic, stats.spearmanr(x[ok], y[ok]).statistic


# --------------------------------------------------------------------------- #
# Figures (light + dark, matching the rest of adfraud/)
# --------------------------------------------------------------------------- #
THEMES = {
    "light": dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", grid="#e4e3df",
                  blue="#2a78d6", orange="#eb6834", aqua="#1baf7a"),
    "dark": dict(surface="#1a1a19", ink="#f0efec", ink2="#c3c2b7", grid="#33332f",
                 blue="#3987e5", orange="#d95926", aqua="#199e70"),
}


def make_plots(df, glob, outdir, min_fs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["Inter", "DejaVu Sans", "sans-serif"]
    outdir.mkdir(parents=True, exist_ok=True)
    x = df["bin"].to_numpy() + 1
    strong = df["first_stage"].to_numpy() >= min_fs

    def setup(th, title, sub):
        fig, ax = plt.subplots(figsize=(9.6, 5.4), dpi=170)
        fig.patch.set_facecolor(th["surface"]); ax.set_facecolor(th["surface"])
        fig.subplots_adjust(left=0.1, right=0.95, top=0.8, bottom=0.15)
        fig.text(0.1, 0.93, title, fontsize=15, fontweight="bold", color=th["ink"])
        fig.text(0.1, 0.875, sub, fontsize=10.5, color=th["ink2"])
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(th["grid"])
        ax.tick_params(colors=th["ink2"], length=0)
        ax.grid(True, color=th["grid"], linewidth=0.8); ax.set_axisbelow(True)
        return fig, ax

    for mode, th in THEMES.items():
        fig, ax = setup(th, "Criteo: what exposure attribution claims vs what randomization shows",
                        "Conversion effect of exposure by propensity bin, with 95% bootstrap intervals")
        ax.errorbar(x, 100 * df["conv_obs"], yerr=196 * df["conv_obs_se"], color=th["orange"],
                    marker="o", capsize=3, linewidth=2, label="Naive exposed − unexposed (treated only)")
        ax.errorbar(x[strong], 100 * df["conv_late_wald"][strong], yerr=196 * df["conv_late_wald_se"][strong],
                    color=th["blue"], marker="o", capsize=3, linewidth=2, label="Wald LATE from randomized offer")
        ax.axhline(100 * glob["conv_late_wald"], color=th["ink2"], linestyle=(0, (4, 3)), linewidth=1,
                   label="Global Wald LATE")
        ax.set_xlabel("Exposure-propensity bin (low → high)", color=th["ink2"])
        ax.set_ylabel("Conversion effect (percentage points)", color=th["ink2"])
        ax.legend(frameon=False, labelcolor=th["ink"], fontsize=9.5)
        fig.text(0.1, 0.03, f"LATE hidden in bins with first stage below {min_fs:.0%} (too noisy).",
                 fontsize=8.5, color=th["ink2"])
        fig.savefig(outdir / f"criteo_attribution_vs_late-{mode}.png", facecolor=th["surface"]); plt.close(fig)

        fig, ax = setup(th, "Does covariance geometry predict where attribution bias lives?",
                        "Per-bin |naive − LATE| vs directional concealment capacity (strong-first-stage bins)")
        cap, bias, se = (df[c].to_numpy() for c in ("concealment_capacity", "conv_bias", "conv_bias_se"))
        ax.errorbar(cap[strong], 100 * np.abs(bias[strong]), yerr=196 * se[strong], fmt="o", color=th["blue"],
                    capsize=3, markersize=7)
        for xi, yi, bi in zip(cap[strong], np.abs(bias[strong]), x[strong]):
            ax.annotate(str(bi), (xi, 100 * yi), xytext=(4, 4), textcoords="offset points", fontsize=8,
                        color=th["ink2"])
        ax.set_xlabel("Directional concealment capacity 1/√(uᵀR⁻¹u)", color=th["ink2"])
        ax.set_ylabel("|naive − LATE| (percentage points)", color=th["ink2"])
        fig.savefig(outdir / f"criteo_geometry_vs_bias-{mode}.png", facecolor=th["surface"]); plt.close(fig)

        fig, ax = setup(th, "Criteo: actual exposure is highly selective within randomized treatment",
                        "Share of randomized-treatment users actually exposed, by propensity bin")
        ax.plot(x, 100 * df["first_stage"], color=th["blue"], marker="o", linewidth=2)
        ax.axhline(100 * min_fs, color=th["ink2"], linestyle=(0, (4, 3)), linewidth=1)
        ax.text(x[0], 100 * min_fs, " weak-first-stage threshold", va="bottom", color=th["ink2"], fontsize=9)
        ax.set_xlabel("Exposure-propensity bin (low → high)", color=th["ink2"])
        ax.set_ylabel("Exposure among randomized treatment (%)", color=th["ink2"])
        fig.savefig(outdir / f"criteo_first_stage_by_propensity-{mode}.png", facecolor=th["surface"]); plt.close(fig)


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data", help="criteo-research-uplift-v2.1.csv.gz")
    ap.add_argument("--outdir", default="adfraud/criteo/figures")
    ap.add_argument("--results", default="adfraud/criteo/results/criteo_attribution_results.csv")
    ap.add_argument("--summary", default="adfraud/criteo/results/criteo_attribution_summary.json")
    ap.add_argument("--chunksize", type=int, default=300_000)
    ap.add_argument("--model-sample", type=int, default=800_000)
    ap.add_argument("--bins", type=int, default=20)
    ap.add_argument("--bootstrap", type=int, default=50, help="Poisson-bootstrap replicates")
    ap.add_argument("--propensity", choices=["hgb", "logistic"], default="hgb")
    ap.add_argument("--geometry-features", choices=["continuous", "all"], default="continuous")
    ap.add_argument("--min-first-stage", type=float, default=0.01,
                    help="Bins below this exposure rate are excluded from the geometry test")
    ap.add_argument("--seed", type=int, default=20261102)
    ap.add_argument("--max-rows", type=int, default=None, help="Optional smoke-test row limit")
    ap.add_argument("--no-figures", action="store_true")
    a = ap.parse_args()

    path = Path(a.data)
    mu, sd, corr, n_control, samp = first_pass(path, a.chunksize, a.model_sample, a.seed, a.max_rows)
    geo = CONTINUOUS if a.geometry_features == "continuous" else FEATURES
    geo_idx = [FEATURES.index(f) for f in geo]
    Rg = corr[np.ix_(geo_idx, geo_idx)]
    ridge = max(1e-10, 1e-8 * np.trace(Rg) / len(geo_idx))
    Rinv = np.linalg.inv(Rg + ridge * np.eye(len(geo_idx)))
    model, edges = fit_propensity(samp, mu, sd, a.bins, a.propensity, a.seed)
    acc = second_pass(path, a.chunksize, a.max_rows, mu, sd, geo_idx, model, edges, a.bootstrap, a.seed)
    est = estimates(acc, Rinv)

    nb = a.bins
    point = {k: v[:, 0] for k, v in est.items()}
    se = {k: np.nanstd(v[:, 1:], axis=1, ddof=1) for k, v in est.items()}
    df = pd.DataFrame({"bin": np.arange(nb)})
    for k in ("n_z0", "n_z1", "n_e1"):
        df[k] = point[k][:nb].astype(int)
    for k in ("first_stage", "conv_rate_control", "conv_rate_treated", "conv_itt", "conv_late_wald",
              "conv_obs", "conv_bias", "visit_itt", "visit_late_wald", "visit_obs", "visit_bias",
              "selection_euclidean", "selection_mahalanobis", "concealment_capacity"):
        df[k] = point[k][:nb]
        df[f"{k}_se"] = se[k][:nb]
    glob = {k: float(point[k][nb]) for k in point}
    glob_se = {k: float(se[k][nb]) for k in se}

    strong = df["first_stage"].to_numpy() >= a.min_first_stage
    def corr_block(xkey):
        xs, ys, fs = est[xkey][:nb][strong], np.abs(est["conv_bias"][:nb][strong]), est["first_stage"][:nb][strong]
        pr, sr = corr_stats(xs[:, 0], ys[:, 0])
        boot = np.array([corr_stats(xs[:, r], ys[:, r]) for r in range(1, xs.shape[1])])
        conf_p, conf_s = corr_stats(xs[:, 0], fs[:, 0])
        ci = lambda col: [float(np.nanpercentile(boot[:, col], 2.5)), float(np.nanpercentile(boot[:, col], 97.5))]
        return {"pearson": pr, "pearson_ci95": ci(0), "spearman": sr, "spearman_ci95": ci(1),
                "confound_check_spearman_with_first_stage": conf_s}

    summary = {
        "rows_analyzed": int(point["n_z0"][nb] + point["n_z1"][nb]),
        "bins": nb, "strong_bins": int(strong.sum()), "min_first_stage": a.min_first_stage,
        "bootstrap_replicates": a.bootstrap, "propensity_model": a.propensity,
        "geometry_features": geo, "geometry_ridge": ridge,
        "global": {k: glob[k] for k in ("first_stage", "conv_rate_control", "conv_rate_treated", "conv_itt",
                                         "conv_late_wald", "conv_obs", "conv_bias", "visit_itt",
                                         "visit_late_wald", "visit_obs", "visit_bias")},
        "global_se": {k: glob_se[k] for k in ("first_stage", "conv_itt", "conv_late_wald", "conv_obs", "conv_bias")},
        "geometry_vs_abs_conversion_bias": {
            "concealment_capacity": corr_block("concealment_capacity"),
            "selection_mahalanobis": corr_block("selection_mahalanobis"),
        },
        "notes": [
            "Treatment is the randomized offer; exposure is endogenous. Wald LATE assumes independence, "
            "exclusion, relevance and monotonicity (one-sided non-compliance makes monotonicity structural).",
            "Correlations use only bins whose first stage is at least min_first_stage; weak bins make LATE "
            "and |bias| dominated by noise. Bootstrap intervals hold the propensity model and bin edges fixed.",
            "If capacity correlates with first stage, any capacity-bias association may be a noise artifact.",
            "Geometry-vs-bias association is a transfer hypothesis, not implied by the synthetic framework.",
        ],
    }
    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, (float, np.floating)):
            return float(o) if math.isfinite(o) else None
        if isinstance(o, np.integer):
            return int(o)
        return o
    for p in (Path(a.results), Path(a.summary)):
        p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.results, index=False)
    Path(a.summary).write_text(json.dumps(clean(summary), indent=2) + "\n")
    if not a.no_figures:
        make_plots(df, glob, Path(a.outdir), a.min_first_stage)
    print(json.dumps(clean(summary), indent=2))
    print(f"Wrote {a.results} and {a.summary}")


if __name__ == "__main__":
    main()
