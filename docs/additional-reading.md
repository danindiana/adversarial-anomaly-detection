# Additional reading

An annotated bibliography that places this project at the intersection of adversarial machine learning, robust statistics, multivariate detection, information hiding, distributed sensing and imperfect detection. Thirty papers in three groups: directly related, mathematically adjacent, and orthogonal but unusually useful.

The same structure keeps reappearing across fields:

```
latent state → imperfect observation → observer policy → adaptive response → changed observation distribution
```

Ecologists meet it as imperfect detection, security researchers as evasion, econometricians as policy response, reliability engineers as common-mode failure, and statisticians as contamination or dependence.

**Eight anchors** that tell most of the story, in order: Huber (1964) → Cachin (1998) → Rousseeuw & Van Driessen (1999) → Axelsson (2000) → MacKenzie et al. (2002) → Dalvi et al. (2004) → Kloft & Laskov (2010, 2012) → Li & Yu (2021). That is: robust contamination → statistical concealment → robust covariance → base rates → imperfect detection → strategic adversary → adversarial anomaly detection → modern robust detection.

Tags: `adaptive-adversary` `poisoning` `evasion` `robust-statistics` `covariance` `steganography` `multichannel-detection` `sensor-fusion` `imperfect-detection` `multiple-testing` `policy-response`

---

## Directly related

These establish that the central premise, that **the detector changes the behavior of what it is trying to detect**, is an established research problem rather than something peculiar to the motivating thought experiment.

**1. Kloft, M., & Laskov, P. (2010). Online anomaly detection under adversarial impact.** *AISTATS*, PMLR 9. [Link](https://proceedings.mlr.press/v9/kloft10a.html)
`adaptive-adversary` `poisoning`
One of the closest antecedents to this setup: an attacker strategically manipulates the data an anomaly detector learns from, and the paper derives the optimal attack and its constraints.

**2. Kloft, M., & Laskov, P. (2012). Security analysis of online centroid anomaly detection.** *Journal of Machine Learning Research* 13. [Link](https://jmlr.org/beta/papers/v13/kloft12b.html)
`poisoning` `adaptive-adversary`
Extends the 2010 analysis to poisoning bounds, limited attacker reach and false-positive constraints, showing how external constraints can sharply bound what an attacker gains. The analogue of our reach-limited contamination.

**3. Rubinstein, B. I. P., et al. (2009). ANTIDOTE: Understanding and defending against poisoning of anomaly detectors.** *ACM Internet Measurement Conference*. [Link](https://ptolemy.berkeley.edu/projects/truststc/pubs/725.html)
`poisoning` `covariance` `robust-statistics`
Network anomaly detectors whose learned "normal" background is itself poisoned, defended with robust PCA. Very close to the planned poisoned-calibration stage.

**4. Cretu, G. F., Stavrou, A., Locasto, M. E., Stolfo, S. J., & Keromytis, A. D. (2008). Casting out demons: Sanitizing training data for anomaly sensors.** *IEEE Symposium on Security and Privacy*. [PDF](https://www.cs.columbia.edu/~angelos/Papers/2008/stand-sp.pdf)
`poisoning` `robust-statistics`
Shows how an anomaly sensor goes blind when its baseline is polluted, and how to sanitize training data with micro-models. The practical form of the "no clean baseline" problem.

**5. Li, M., & Yu, Y. (2021). Adversarially robust change point detection.** *NeurIPS*. [Link](https://papers.neurips.cc/paper_files/paper/2021/hash/c1e39d912d21c91dce811d6da9929ae8-Abstract.html)
`robust-statistics` `adaptive-adversary`
Formalizes adversarial contamination with Huber's ε-contamination model and derives detection and localization limits. Relevant to the finite-T and adaptive-observation extensions.

**6. Altamirano, M., Briol, F.-X., & Knoblauch, J. (2023). Robust and scalable Bayesian online changepoint detection.** *ICML*, PMLR 202. [Link](https://proceedings.mlr.press/v202/altamirano23a.html)
`robust-statistics`
A robust Bayesian treatment of contaminated time series, useful for a sequential version of the problem.

**7. Fogla, P., & Lee, W. (2006). Evading network anomaly detection systems: Formal reasoning and practical techniques.** *ACM CCS*. [DOI](https://doi.org/10.1145/1180405.1180414)
`evasion` `adaptive-adversary`
An adversary deliberately shapes its traffic to fall inside the detector's normal region; a concrete case of footprint shaping.

**8. Wagner, D., & Soto, P. (2002). Mimicry attacks on host-based intrusion detection systems.** *ACM CCS*. [DOI](https://doi.org/10.1145/586110.586145)
`evasion` `multichannel-detection`
Attacks that reproduce the joint pattern of normal behavior rather than just keeping a raw signal small. The security version of matching the background's covariance structure.

**9. Nelson, B., et al. (2008). Exploiting machine learning to subvert your spam filter.** *USENIX LEET*. [Link](https://www.usenix.org/conference/leet-08/exploiting-machine-learning-subvert-your-spam-filter)
`poisoning`
A clean empirical demonstration that controlling a small fraction of training data can radically change a learned detector.

**10. Barreno, M., Nelson, B., Joseph, A. D., & Tygar, J. D. (2010). The security of machine learning.** *Machine Learning* 81. [DOI](https://doi.org/10.1007/s10994-010-5188-5)
`adaptive-adversary` `poisoning` `evasion`
The attack taxonomy (causative vs. exploratory, attacker costs, formal adversarial interaction) that gives the contamination game its historical context.

## Mathematically adjacent

Where to point a technical audience that asks where the equations come from.

**11. Huber, P. J. (1964). Robust estimation of a location parameter.** *Annals of Mathematical Statistics* 35(1). [DOI](https://doi.org/10.1214/aoms/1177703732)
`robust-statistics`
The origin of the ε-contamination model and the efficiency-versus-robustness tradeoff that recurs here in SD vs. MAD, directional vs. omnibus tests, and estimator choice.

**12. Rousseeuw, P. J., & Van Driessen, K. (1999). A fast algorithm for the minimum covariance determinant estimator.** *Technometrics* 41(3). [DOI](https://doi.org/10.1080/00401706.1999.10485670)
`covariance` `robust-statistics`
The standard robust multivariate covariance estimator; an obvious observer action for the poisoned-Σ̂ stage.

**13. Ledoit, O., & Wolf, M. (2004). A well-conditioned estimator for large-dimensional covariance matrices.** *Journal of Multivariate Analysis* 88(2). [DOI](https://doi.org/10.1016/S0047-259X(03)00096-4)
`covariance`
Shrinkage estimation for when finite T makes the sample covariance unstable to invert; likely to become another observer action.

**14. Pacreau, G., & Lounici, K. (2023). Robust covariance estimation with missing values and cell-wise contamination.** *NeurIPS*. [Link](https://proceedings.neurips.cc/paper_files/paper/2023/hash/e444859b2a22df6b56af9381ad1e9480-Abstract-Conference.html) · [arXiv](https://arxiv.org/abs/2306.00752)
`covariance` `robust-statistics` `poisoning`
Robustness when contamination hits individual components rather than whole observations, which is how reach-limited multichannel poisoning works.

**15. Cachin, C. (1998). An information-theoretic model for steganography.** *Information Hiding*, LNCS 1525. [DOI](https://doi.org/10.1007/3-540-49380-8_21)
`steganography`
Concealment as hypothesis testing, with security measured by the relative entropy between cover and stego distributions: the intellectual ancestor of this project's KL formulation.

**16. Ker, A. D. (2010). The square root law does not require a linear key.** *ACM Multimedia and Security Workshop*. [DOI](https://doi.org/10.1145/1854229.1854267)
`steganography`
Both substance and warning: square-root concealment laws are conditional results, not universal laws, a point this project had to correct in its own reasoning.

**17. Bash, B. A., Goeckel, D., & Towsley, D. (2013). Limits of reliable communication with low probability of detection on AWGN channels.** *IEEE Journal on Selected Areas in Communications* 31(9). [DOI](https://doi.org/10.1109/JSAC.2013.130923) · [arXiv](https://arxiv.org/abs/1202.6423)
`steganography` `adaptive-adversary`
A square-root law for covert communication under an explicit warden-and-noise model; a useful comparison with this project's concealment-capacity results.

**18. Reed, I. S., & Yu, X. (1990). Adaptive multiple-band CFAR detection of an optical pattern with unknown spectral distribution.** *IEEE Transactions on Acoustics, Speech, and Signal Processing* 38(10). [DOI](https://doi.org/10.1109/29.60107)
`multichannel-detection` `covariance`
The classic covariance-whitened multichannel detector (the RX detector), directly related to the Mahalanobis omnibus test used here.

**19. Neyman, J., & Pearson, E. S. (1933). On the problem of the most efficient tests of statistical hypotheses.** *Philosophical Transactions of the Royal Society A* 231. [DOI](https://doi.org/10.1098/rsta.1933.0009)
`multichannel-detection`
The foundation under all the size-and-power language: choose rejection regions subject to a false-alarm constraint.

**20. Dalvi, N., Domingos, P., Mausam, Sanghai, S., & Verma, D. (2004). Adversarial classification.** *ACM KDD*. [PDF](https://homes.cs.washington.edu/~pedrod/papers/kdd04.pdf)
`adaptive-adversary`
Classification as a game in which the adversary alters observations in response to the classifier; an early formal antecedent of the Stackelberg structure here.

## Orthogonal but unusually useful

**21. Stevens, M., & Merilaita, S. (2009). Animal camouflage: current issues and new perspectives.** *Philosophical Transactions of the Royal Society B* 364. [PubMed](https://pubmed.ncbi.nlm.nih.gov/18990674/)
`imperfect-detection` `evasion`
Defines camouflage functionally, as reduced detection relative to a particular observer's sensory system, which maps closely onto the `uᵀΣ⁻¹u` view of concealment.

**22. MacKenzie, D. I., et al. (2002). Estimating site occupancy rates when detection probabilities are less than one.** *Ecology* 83(8). [Link](https://www.usgs.gov/publications/estimating-site-occupancy-rates-when-detection-probabilities-are-less-one)
`imperfect-detection`
Ecology's version of the existence/detection distinction: non-detection is not absence when detection probability is below one.

**23. Link, W. A. (2003). Nonidentifiability of population size from capture–recapture data with heterogeneous detection probabilities.** *Biometrics* 59(4). [DOI](https://doi.org/10.1111/j.0006-341X.2003.00129.x)
`imperfect-detection`
Strikingly close to the original population question: different population sizes with heterogeneous detectability can produce essentially indistinguishable data, however much of it you collect.

**24. Axelsson, S. (2000). The base-rate fallacy and the difficulty of intrusion detection.** *ACM Transactions on Information and System Security* 3(3). [DOI](https://doi.org/10.1145/357830.357849)
`multiple-testing` `imperfect-detection`
Why rare-event detection programs drown in false positives unless the false-alarm rate is extraordinarily small; the reason raw anomaly catalogs are weak evidence, and the reason individual-level scoring fails.

**25. Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate.** *Journal of the Royal Statistical Society B* 57(1). [DOI](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x)
`multiple-testing`
Scanning thousands of places, channels and time windows makes multiple testing unavoidable: a 1% detector run a million times is a different evidential problem.

**26. Tsitsiklis, J. N. (1993). Decentralized detection.** In *Advances in Statistical Signal Processing*, vol. 2. [PDF](https://www.mit.edu/~jnt/Papers/B-93-detection.pdf)
`sensor-fusion`
How to compress and fuse information from multiple sensors under constrained architectures; a counterpoint to assuming more sensors automatically means more evidence.

**27. Viswanathan, R., & Varshney, P. K. (1997). Distributed detection with multiple sensors, Part I: Fundamentals.** *Proceedings of the IEEE* 85(1). [DOI](https://doi.org/10.1109/5.554208)
`sensor-fusion` `multichannel-detection`
A survey of optimal multi-sensor decision rules under Bayesian and Neyman–Pearson formulations, useful once the multichannel model becomes a real sensor network.

**28. Mosleh, A. (1991). Common cause failures: an analysis methodology and examples.** *Reliability Engineering & System Safety* 34(3). [DOI](https://doi.org/10.1016/0951-8320(91)90104-F)
`covariance` `sensor-fusion`
The engineering analogue of this project's covariance warning: redundant channels do not multiply confidence when one shared cause can fail them all at once.

**29. Lucas, R. E. (1976). Econometric policy evaluation: A critique.** *Carnegie-Rochester Conference Series on Public Policy* 1. [DOI](https://doi.org/10.1016/S0167-2231(76)80003-6)
`policy-response` `adaptive-adversary`
Behavior estimated under one policy need not hold when the policy changes: "the hider responds to the detector" in econometric form.

**30. Campbell, D. T. (1979). Assessing the impact of planned social change.** *Evaluation and Program Planning* 2(1). [DOI](https://doi.org/10.1016/0149-7189(79)90048-X)
`policy-response`
Indicators degrade when the people being measured have incentives to respond to them; a conceptual companion to the randomized-observation and adaptation results.

---

*Selection and first-draft annotations by ChatGPT; links checked and cleaned, and annotations edited, by Claude.*
