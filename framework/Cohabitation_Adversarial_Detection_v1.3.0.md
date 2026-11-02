# Persistent Nonhuman Cohabitation: Adversarial Detection Models, v1.3.0

**Status:** Synthetic and hypothetical mathematical methods paper; no claims of an actual concealed population.  
**Version:** 1.3.0  
**Date:** 2026-11-01  
**Reproducibility:** `python verify_models_v1_3.py --output-dir .` using NumPy and SciPy. All experiment parameters and costs are in the script.  

## Abstract

An original philosophical scenario posits a persistent concealed population sharing the terrestrial environment while avoiding overt involvement in human political life. Such premises supply an adversarial-detection *motivation*, not evidence. Earlier versions formalized report-background ambiguity, concealment costs, controls, between-control heterogeneity, randomized coverage, and observer loss under model misspecification. Version 1.3 extends the toy game so the hypothetical hider can vary operational signal, control reach, and contamination type (mean shifts or balanced dispersion). The observer can choose the number of privately sampled controls and among empirical standard deviation, empirical median absolute deviation (MAD), protected external calibration, or a physics-only noise model. Tests must satisfy an explicit false-alarm admissibility condition before entering the observer's resource game.

The core result is conditional: an unknown long-duration background does **not** automatically make a system untestable, but unrestricted manipulation of every informative measurement can render the alternative unidentifiable. Whether calibration is empirically learned, protected externally, or physically derived is not itself dispositive. Identifiability depends on which restrictions survive strategic contamination.

## 1. What is being tested

The experiment is **not** a test for extraterrestrial life, biological indistinguishability, cryptoterrestrial residence, or historical intervention. It is an abstract ON/OFF measurement model for detecting an adaptive source whose footprint can contaminate controls. No real anomaly reports, clinical records, genomic samples, or nuclear near-miss data are used.

Presence, detectable activity, and inferred motive remain distinct. The conservation-of-evolutionary-option-value conjecture from earlier versions is one possible motivation, not an entailment of the four hypothetical premises.

## 2. Model and information timing

Let there be `m=8` candidate OFF controls. The defender chooses a policy (measurement count `k in {4,6,8}` and estimator/calibration method) and privately selects `k` controls uniformly without replacement *after* the hider chooses which controls to reach. The attacker observes the defender's probability distribution over policies but **not** the realized sample or Gaussian measurement noise. It may reach `r in {0,2,4}` fixed control identities, and chooses signal `s in {0,5,10,20,30}`. When active it can choose:

- **none:** no control contamination, `r=0`;
- **level:** add `s` to each reached control;
- **spread:** add balanced `+delta,-delta` offsets, `delta in {10,20}`;
- **mixed:** add level `s` plus balanced dispersion.

The identity of reached controls is exchangeable in the assumed homogeneous model; the code fixes the first `r`. A heterogeneous or networked model would not permit this reduction.

For each simulated independent campaign, channel mean errors (after averaging 100 nominal Poisson-count blocks at background count `B=1000`) are approximated by independent Gaussians with variance

\[
 v = B/100+\tau^2=10+\tau^2,\qquad \tau\in\{0,3,10\}.
\]

A shared unknown mean cancels from ON-minus-OFF contrasts. `tau` denotes persistent *between-channel* variation in means, not variation independently averaged away with each block. The numerical power calculations are Gaussian approximations, not a reanalysis of the exact Li–Ma Poisson likelihood.

## 3. The two adversarial strategies are genuinely distinct

**Level contamination** attempts to make ON and OFF means agree, while **spread contamination** increases dispersion in the controls without changing their mean when both offset signs are observed. If only one of a balanced pair is sampled, a sample mean shift can occur as well. A hider can also shrink `s`, a strategy missing from v1.2. The resulting detection problem is not characterized by the coverage count `r` alone.

The defender's options:

1. `empirical_std`: ON minus sample mean of OFF controls, divided by the controls' sample SD times `sqrt(1+1/k)`; calibrated with one-sided Student-t critical values under iid Gaussian null.
2. `empirical_mad`: ON minus sample **median** OFF, divided by `1.4826*MAD` times `sqrt(1+1/k)`; one-sided null critical values are determined using 250,000 independent simulated standard-normal reference samples for each `k`. These critical values account for very small `k`, where Gaussian z or t critical values would not be justified for this statistic.
3. `protected_scale`: ON minus OFF mean divided by externally known `sqrt((10+tau²)*(1+1/k))`; uses a standard-normal cutoff. **This is an oracle-like idealization**: clean tau estimation is *assumed* secured outside attack reach and is not established by premise 1.
4. `physics_only`: ON minus OFF mean divided by `sqrt(10*(1+1/k))`, accounting for counting variation but **ignoring between-control heterogeneity**. This can be correctly sized at tau=0 but grossly invalid when tau>0. Physics constrains instrument noise, not necessarily environmental variation.

All methods use one-sided alpha=0.01. For a model to be admissible as a defender policy, its simulated null rejection rate must be within 0.007 of 0.01 in the relevant tau scenario; excluded methods are still reported in the detailed sensitivity CSV. This cutoff is deliberately coarse for a finite Monte Carlo toy, not a recommended pre-registered standard. A real design must assess size across an uncertainty set for tau rather than selecting policies with oracle access to the true tau.

### Breakdown versus efficiency

MAD's 50% asymptotic breakdown point is a robustness property: it does not guarantee optimal detection power at 4 or 8 observations, and exactly half the controls being manipulated is a boundary case. In a Gaussian model MAD is less statistically efficient than SD. Robustness must be evaluated together with estimator location, null calibration, finite-sample coverage, and attacker strategy. No blanket claim that MAD always beats SD is warranted.

## 4. Validation of the spread-injection attack

A separate benchmark reproduces a known t-test vulnerability. It deliberately *fixes the attack to exactly two of the `k` measured controls*, rather than randomizing which candidate controls are observed. Parameters: ON signal 20, baseline variance 10 for every channel mean, balanced `+delta,-delta` OFF offsets, 200,000 independent Gaussian draws, one-sided alpha 0.01.

| k | delta=0 power | delta=10 power | delta=20 power |
|---:|---:|---:|---:|
| 4 | 0.77183 | 0.007015 | 0.000000 |
| 8 | 0.99062 | 0.545785 | 0.001305 |

These Monte Carlo results reproduce the earlier simulation to sampling error. The difference from the main game is the *selection frame*: when the adversary reaches only `r` of `m=8` candidate controls before `k` are randomly selected, a balanced pair is not always fully observed.

## 5. Joint security game and operating utility

The defender chooses a mixture over 12 discrete policies (3 values of k by 4 scale/estimator methods). The follower chooses among 45 discrete attack configurations. The leader observes a fixed synthetic payoff model, not a particular random realization. The follower knows the committed distribution and best responds.

The hider's utility is

\[
U_A(s,r,\delta)=0.6\frac{\log(1+s/5)}{\log(5)}
  -P(\mathrm{detected}\mid s,r,\delta)
  -0.02r-0.04r(\delta/20)^2,
\]

with detection-risk penalty set to zero when `s=0` (no activity to expose). The hider is permitted to cease activity entirely. These are *hypothetical preference parameters*, not experimentally estimated incentives.

The defender loss is

\[
L_D=\frac{s}{20}[1-P(\mathrm{detected})]
  +0.01k+c_{\mathrm{method}}
  +0.1P(\mathrm{false\ alarm}),
\]

where `c_method` is 0 for empirical SD/physics-only, 0.02 for MAD, and 0.06 for protected scale. The probability of detection is a calibrated one-sided contrast rejection probability, not proof of adversarial intent. The defender loss includes missed signal impacts, sampling and calibration costs, and a false-positive term; false-size-invalid policies are excluded rather than being allowed to purchase apparent power at an unacceptable false-alarm rate.

For each possible follower response, a linear program minimizes expected defender loss subject to the response being a follower best reply. Among tied follower best responses the computation uses the **strong Stackelberg** convention (ties resolve in the leader's favor), with numerical tolerances explicitly checked. The optimization is finite-grid and conditional on the specified functional utilities; changing either can alter equilibria substantially.

## 6. v1.3 equilibrium table

| tau | Defender policy | Hider response | Detection power | Null size |
|---:|---|---|---:|---:|
| 0 | k=4, physics-only (100%) | s=10, r=4, level | 0.2113 | 0.0107 |
| 3 | k=4, empirical SD (36.11%) / protected scale (63.89%) | s=10, r=4, level | 0.0778 | 0.0104 |
| 10 | k=4, protected scale (100%) | s=30, r=4, level | 0.1693 | 0.0107 |

Numbers reflect 30,000 common-random-number synthetic realizations per strategy plus independently simulated MAD critical values. The mix in the tau=3 row is an illustrative boundary equilibrium under invented costs, **not a recommendation**. An actor's ability to choose `s` changes the previous deterrence story: at tau=10 the hider accepts greater observable signal because the observation channel is noisy, even with protected-scale calibration. At tau=0 and 3 it operates at reduced signal and reaches all four allowed controls.

An important interpretive caveat: the tau=10 equilibrium presupposes the defender can obtain protected external scale at its assumed price. If such calibration cannot be secured, the game must be resolved with those policies removed, rather than interpreting an oracle-equilibrium as an attainable defense.

## 7. Formal 'no clean baseline' result: what does and does not follow

### Proposition (restricted observational non-identifiability)

Suppose an observation vector has a common unknown mean `B`, and under an alternative an unrestricted adversary can add the same persistent `s` to every measured ON and OFF channel. Let both the null and the alternative permit arbitrary `B` in the same interior range. Then

\[
P(Y\mid H_1,B,s)=P(Y\mid H_0,B+s)
\]

whenever the adversary can also match all relevant noise and joint-dependence properties. The two parameterizations generate overlapping distributions, so `s` is not identifiable from those observations alone, no matter how many repeated samples are collected. A different labeling of the same distribution does not create information. The same ambiguity can occur if an adversary controls the entire history used to calibrate the background.

**Qualification:** the identity above requires *full distribution matching*, not merely raising means. If covariance, correlation, energy balance, physical side effects, or other constraints differ, some measurements can remain discriminating even when every channel's mean is spoofed. A claim that the adversary has controlled historical observations for a long time does not establish unlimited access or perfect distribution matching.

### Why absence of a pre-contact baseline is not decisive

1. **Randomized contrasts can cancel nuisance means.** A Student-t test based on simultaneous exchangeable channels can be correctly sized without knowing the historical mean `B`, provided its sampling/independence assumptions are satisfied.
2. **Current structural restrictions can be identifying.** Conservation laws, independently bounded measurement error, simultaneous multi-modal correlations, and externally constrained intervention reach may yield predictions even without a pre-contact epoch.
3. **Physics-derived noise is not a substitute for a full environmental model.** Known Poisson counting variance does not bound persistent between-control heterogeneity by itself. At tau=10 the physics-only channel uses the wrong null scale.
4. **Protected calibration is conditional.** A clean calibration procedure needs a specified security boundary or a demonstrably attack-resistant mechanism. It cannot simply be asserted to be outside reach.
5. **If an alternative is allowed to rewrite arbitrary evidence**, it is observationally equivalent by stipulation. No passive likelihood ratio can distinguish it without adding restrictions. This is an identifiability limit, not independent evidence for the alternative.

Thus the rigorous conclusion is: *without limits on the adversary's reach or the background family, the hypothesis may be unidentifiable; with independently testable limits, information can reappear even in the absence of a pre-contact record.*

## 8. Priority limitations and v1.4 proposals

- Backgrounds are exchangeable independent Gaussian channel means; introduce correlated backgrounds, drifting common factors, and multiple simultaneous physical modalities.
- The hider fixes controlled identities before the private sample; test delayed reaction, imperfect information, and fixed budgets over repeated periods.
- MAD is only one robust scale estimator; compare Qn, Sn, trimmed scale, and joint robust location/scale with finite-sample honest size calibration.
- Derive security-constrained coverage where the hider can spread effort across *all* controls with partially effective spoofing.
- Replace oracle tau knowledge with uncertainty sets, cross-fitting, and protected calibration protocols with auditable assumptions.
- Compute confidence intervals for Monte Carlo payoffs and response stability, and assess equilibrium sensitivity to small cost changes.
- Replace hypothetical preferences with independently defensible estimates before interpreting any operational predictions.

## Methodological references

- Li, T.-P. & Ma, Y.-Q. (1983), *Analysis methods for results in gamma-ray astronomy*, ApJ 272:317–324, DOI 10.1086/161295. Source: https://articles.adsabs.harvard.edu/pdf/1983ApJ...272..317L . Analogical precedent for ON/OFF analysis, not a model of adversarial manipulation.
- Rousseeuw, P. J. & Croux, C. (1993), *Alternatives to the median absolute deviation*, JASA. Source: https://wis.kuleuven.be/stat/robust/papers/publications-1993/rousseeuwcroux-alternativestomedianad-jasa-1993.pdf . High-breakdown robust scale estimation and efficiency trade-offs.
- Mu, W. & Xiong, S. (2023), *On Huber's contaminated model*, Journal of Complexity 77:101745, DOI 10.1016/j.jco.2023.101745. Source: https://www.sciencedirect.com/science/article/pii/S0885064X23000146 . Identifiability under specified contamination families.

## Reproducibility and interpretation

From the archive root: `python verify_models_v1_3.py --output-dir .`. Inputs, constants, estimator definitions, seeded randomness, and strict assertions are in the script. Outputs are `joint_strategy_results.csv`, `stackelberg_joint_equilibria.csv`, `spread_benchmark.csv`, and `results_v1_3.json`. Check `SHA256SUMS.txt` for packaged checksums. Historical code and notes are retained under `legacy/` without compiled `*.pyc` or `__pycache__` directories. No new source of actual observational evidence is claimed.
