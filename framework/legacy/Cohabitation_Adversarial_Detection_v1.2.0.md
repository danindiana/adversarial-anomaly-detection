# Persistent Nonhuman Cohabitation: Adversarial Detection and Coverage

**Version:** 1.2.0  
**Date:** 2026-11-01  
**Status:** Formal synthetic-methods note; no empirical evidence for concealed nonhuman residents is offered or implied.  
**Code:** `verify_models_v1_2.py`; previous frozen notes and verification scripts are retained in `legacy/`.

## Abstract

The motivating counterfactual is a concealed terrestrial population of nonhuman origin that monitors ordinary activity and might intervene at planetary-risk thresholds. The statistical question extracted from that speculation is substantially more general: **what can an observer detect when a strategic actor can alter some—but not all—observation channels, and when normal channels differ for ordinary reasons?** Version 1.2 replaces the one-control, matching-pennies game with a multiple-control **coverage game**. It explicitly models background heterogeneity, distinguishes a robust omnibus test from a misspecified directional test, and optimizes randomized observation budgets against a resource-limited adversary. All numbers below follow from declared toy-model parameters and are not estimates about extraterrestrial activity.

## 1. Scope and the v1.1 correction

The earlier toy had a defender select exactly one of two OFF controls. A hider attacked the more likely choice, giving a closed-form matching-pennies equilibrium with equal selection probabilities. With clean information `I` and attack cost `c`, the hider attacks if `c < I/2` when the defender randomizes equally; the defender's expected retained information was `I/2` under attack and `I` otherwise. A 1,001-point strategy grid was unnecessary.

**That result is not a general argument for randomization over controls.** If the defender can measure both controls, unequal contaminated and uncontaminated channels remain distinguishable under a calibrated common-background null. With background `B=1000`, signal `s=20`, and 100 independent blocks, the exact *profile Poisson KL to the common-mean null* is:

| Simultaneously measured channels | Profile KL, nats |
|---|---:|
| ON plus one clean OFF | 9.90099 |
| ON plus both clean OFFs | 13.216083 |
| ON plus two OFFs, exactly one spoofed by +20 | 13.187036 |
| ON plus two OFFs, both spoofed by +20 | 0 |

The statistic distinguishes **equality versus inequality of channels**, not necessarily a hider versus a natural heterogeneous mechanism. KL against a common-rate null must never be read as posterior odds of extraterrestrial presence.

## 2. Coverage model and information order

There are `m` exchangeable potential OFF controls. The defender publicly commits to a distribution over the number `k` of controls to measure but privately and uniformly samples their identities. Before the draw, the adversary commits to a set of `r` controls that it can raise by the full signal `s`; it cannot change the ON signal, learn the random sample in advance, or alter controls outside that set. Set `0<=r<=R<=m` for a hard reach budget `R`.

The number `A` of selected controls reached by the adversary follows the hypergeometric distribution:

\[
P(A=a\mid m,k,r)=\frac{\binom{r}{a}\binom{m-r}{k-a}}{\binom{m}{k}}.
\]

The exact full-coverage probability is

\[
P(A=k\mid m,k,r)=\frac{\binom{r}{k}}{\binom{m}{k}}\quad (r\ge k),
\]

and zero when `k>r`. This probability is a **combinatorial bound on full coverage**, not itself a detection probability. For `m=8`, `k=4`, `r=4`, full coverage occurs with probability `1/70 = 1.428571%`.

The order of events is: (1) defender announces a mixed distribution on `k` and its conditional uniform random sampling policy; (2) adversary chooses `r` and which `r` control identities to cover; (3) private `k` and identities are sampled; (4) measurements arrive; (5) observer applies its specified statistical test. Uniform exchangeability makes the covered identities strategically interchangeable. A hider who sees individual realized assignments requires a different game.

## 3. Background heterogeneity and the omnibus test

Each channel contributes a mean count over `T=100` blocks, with nominal baseline `B=1000` per block. The ON channel adds signal `s=20`; the hider adds `s` to each covered OFF channel. In addition to Poisson measurement noise, channel `i` has a persistent random baseline offset `u_i ~ N(0,tau²)`. The background offsets are independent across channels and centered at zero; the model **assumes tau is externally calibrated and known to the test**. For sufficiently high baseline counts, channel means are approximately Gaussian with variance:

\[
v=\frac BT+\tau^2.
\]

Let `n=k+1`, `P=I-11ᵀ/n`, and `delta=s(1,1,...,1,0,...,0)` with `1+a` elevated components. Profiling out the common background gives:

\[
D_{\rm profile}\approx\frac{\|P\delta\|^2}{2v}
=\frac{s^2}{2v}\frac{(a+1)(k-a)}{k+1}.
\]

Under a correctly specified equal-mean Gaussian null, the omnibus statistic `Q=||Px||²/v` has a chi-squared distribution with `k` degrees of freedom. Under the specified alternative, it has a noncentral chi-squared distribution with noncentrality `2D_profile`. We set `alpha=.01` and compute exact noncentral-chi-squared tail probabilities within this **Gaussian approximation**. The test is two-sided: it detects deviations from common means, not a positive ON-only excess, much less a particular agent's motive.

For *k=2* (ON plus both controls), the approximate information and omnibus power are:

| Between-control SD `tau` | Clean controls, KL | One spoofed, KL | Power with one spoofed |
|---|---:|---:|---:|
| 0 | 13.3333 | 13.3333 | 98.7946% |
| 3 | 7.0175 | 7.0175 | 80.561% |
| 10 | 1.2121 | 1.2121 | 10.679% |

The clean versus one-spoofed equality here is exact *within the equal-variance Gaussian approximation*, while the exact Poisson profile KL differs slightly (13.2161 versus 13.1870). If both controls are spoofed, all channels have the same mean and the test has only its nominal 1% false-alarm rate.

**A badly estimated tau can be more damaging than adversarial spoofing.** For `k=2`, if true `tau=10` but the observer designs its 1%-size test as though `tau=0`, the *actual* false alarm rate is **65.7933%**. This is obtained by rescaling the chi-squared critical value by `v_assumed/v_true = 10/110`. The result is conditional on the stated Gaussian random-effects model; realistic heterogeneity may be correlated, non-Gaussian or nonstationary.

## 4. Expected power versus full coverage

Take `m=8`, hard reach `r=4`, no heterogeneity (`tau=0`), and the 1%-size omnibus test:

| Number observed `k` | Full coverage | Expected omnibus power |
|---:|---:|---:|
| 1 | 50.00% | 49.05% |
| 2 | 21.43% | 77.84% |
| 3 | 7.14% | 92.42% |
| 4 | 1.43% | 98.34% |
| 5 | 0% | 99.92% |
| 8 | 0% | nearly 100% |

Expected power averages over the hypergeometric distribution of the actually reached controls. Increasing `k` raises measurement cost, so maximizing power alone is not an optimal resource policy.

## 5. The loss from confident false reassurance

The omnibus test above is *not* the same decision rule as a directional observer who incorrectly assumes controls are always clean. To illustrate the cost of model misspecification, compare two sharp Gaussian contrast models, `H0` (no ON excess) and `H1_clean` (ON excess `s`, no spoofed controls), with known variance `v`. Ignoring contamination, the clean-only log likelihood ratio under a true configuration with `a` spoofed controls has:

\[
\mathbb E[\log LR_{\rm clean,0}]=I_{\rm clean}(1-2a/k),\quad
\mathrm{Var}(\log LR_{\rm clean,0})=2I_{\rm clean},\quad
I_{\rm clean}=\frac{s^2 k}{2v(k+1)}.
\]

Define **confident false reassurance** as `log LR_clean,0 < -log(10)` under an actual ON-signal condition. With `k=2`, `tau=0` and `a=1`, its probability is approximately **32.78%**; with `a=2`, **98.37%**. Meanwhile, the heterogeneity-aware omnibus detector has about **98.79% power** for `a=1`. Thus the same observations can contain strong evidence *against the equal-channel null* while a falsely specified ON-only alternative yields misleading reassurance.

This is an error **relative to the artificially restricted H1_clean**. A fully specified adversarial alternative including contamination would not treat the equal-channel observation as decisive evidence against all hidden-actor models. Conversely, an omnibus rejection does not identify malicious contamination.

## 6. Coverage Stackelberg game with explicit losses

The follower is now limited to reaching `R=4` of `m=8` controls. The defender chooses a **mixed distribution over the measurement count `k=1..8`** and uniformly samples identities after the hider commits. Both sides know the model and costs. The defender wants to minimize:

\[
L_D=E[\text{omnibus miss probability}]+c_D E[k],
\]

whereas the hider wants to maximize:

\[
U_A=E[\text{omnibus miss probability}]-c_A r.
\]

This is a non-zero-sum resource game. Per-control costs are in units of decision loss, not money. The hider selects `r` in `{0,1,2,3,4}`. The defender's optimal commitment is found by **enumerating follower responses and solving a linear program for each best-response region**; no 1,001-point allocation grid is required. We demand a small `0.002` follower-incentive margin so numerical equilibria are not supported solely by exact indifference.

Three examples, all conditional on the arbitrary decision costs:

| tau | cD | cA | Defender's distribution over k | Hider r | Omnibus miss |
|---:|---:|---:|---|---:|---:|
| 0 | .01 | .01 | 52.3% k=3, 47.7% k=4 | 0 | 0.96% |
| 3 | .03 | .02 | 43.7% k=2, 56.3% k=3 | 0 | 19.13% |
| 10 | .01 | .01 | 59.1% k=1, 40.9% k=2 | 0 | 89.14% |

The hider abstains in these particular equilibria because the *committed* design makes reaching controls insufficiently attractive relative to the stipulated cost. These are deterrence equilibria **inside a hard-capability model**, not evidence of deterrence in reality. In particular, if the hider can afford `r=m`, full spoofing can make the tested contrasts observationally identical to the null. Costs, hard budgets, and randomization secrecy are indispensable premises.

## 7. Conclusions and open constraints

1. **Two simultaneous controls can defeat a single perfect spoof** in an equal-background model, because the hider cannot make every channel match.
2. **Independent calibration is not optional.** Between-control heterogeneity can masquerade as the same inequality the observer seeks; an underestimated `tau` can destroy nominal error control.
3. **Full coverage and statistical nondetection are distinct.** Their relationship depends on signal-to-noise, calibration, the chosen test, and the actor's ability to match entire channel distributions rather than just means.
4. **Expected information is not decision quality.** A misspecified sharp alternative can induce high-confidence support for the null when the alternative was simply too narrow.
5. **Randomization can create value only when access is constrained** by cost, a hard reach budget, or the hider's inability to see realized assignments. If every observed channel can be perfectly matched to the null, passive contrast tests cannot distinguish the hypotheses using those channels alone.

The framework does **not** assert that any nonhuman or clandestine population exists. It defines statistical and game-theoretic conditions under which some kinds of concealed action would be detectable, undetectable, or confounded with an ordinary heterogeneous background. Next-generation work should include joint estimation of `tau`, spatial/temporal correlation, partially spoofed controls, imperfect attacker knowledge, and out-of-sample calibration. No model here estimates a probability of extraterrestrial residence.

## Selected methodological sources

- Li, T.-P., and Ma, Y.-Q. (1983). *Analysis methods for results in gamma-ray astronomy*. *Astrophysical Journal* 272:317–324. DOI: 10.1086/161295. Established ON/OFF significance methodology, **not** a solution to adversarial controls.
- Tsai, J. et al. (2010). *Urban Security: Game-Theoretic Resource Allocation in Networked Domains*. AAAI 24:881–886. DOI: 10.1609/aaai.v24i1.7612. Motivates Stackelberg resource allocation and randomized commitments.
- Xu, H. et al. (2015). *Exploring Information Asymmetry in Two-Stage Security Games*. AAAI 29. DOI: 10.1609/aaai.v29i1.9290. Information timing and disclosure matter in attacker/defender strategy.

**Reproducibility:** `python verify_models_v1_2.py --output-dir .` generates `results_v1_2.json`, `coverage_results.csv`, `heterogeneity_results.csv`, and `coverage_game_equilibria.csv`. Values may vary at the last few decimal places across SciPy implementations. Synthetic assumptions are explicit in code. Earlier v1.0/v1.1 code is retained without modification for comparison.
