# IDEA_QUEUE.md — ranked attack queue

Pull the next idea from the top. Re-rank after every verdict.
Ranking criterion: **information per unit cost** first, then genuine non-genericity,
then probability of an asymptotic win, then cheapness.

Tags: `[E]` established · `[H]` heuristic · `[S]` speculation.
Source: `seed` = written at session start; `gen:<surface>` = from the multi-agent idea
sweep (47 ideas across 8 surfaces, `ecdlp/data/wf_ideas_raw.json`).

---

## The accounting that drives the ranking

Index calculus with factor base `F`, `|F| = m`, `k`-term decompositions:

- `Pr[random R decomposes] ≈ (2m)^k / (k!·n)`  `[E]`
- relation generation by guess-and-check costs `Θ(n)` **in total, for every `m` and `k`** —
  each probe succeeds with probability `m/p` and we need `m` successes. So a win
  requires a genuine **decomposition oracle**.
- with an oracle of cost `T`: `total = m·T + m²`, and decompositions must exist
  (`m ≳ n^{1/k}`), so beating `n^{1/2}` needs `T < n^{1/2}/m`.
- writing `T = m^θ`: **a win needs `θ ≤ k−3`. Brute force is `θ = k−1`.**
  So any winning oracle must beat brute force by **two full exponent units in `m`**,
  at every `k`.

Two oracle families are known, and both are now measured:

| family | best known `θ` | resulting exponent | measured? |
|---|---|---|---|
| combinatorial (birthday / meet-in-the-middle with a `j`-sum table) | `j`, giving `n^{j/(2j−1)}` | → `1/2` **from above**, never below | **yes — IC1** |
| Wagner k-tree (needs a filtration) | would give `n^{2/(l+1)}`, i.e. `n^{2/5}` at `l=4` | **would beat rho** | **yes — K1: no filtration exists** |
| algebraic (eliminant / resultant) | `k−1` (the eliminant is dense) | `Θ(n)` | **yes — IC2** |

---

## CLOSED — verdicts recorded in ATTACK_LOG.md

| id | idea | verdict | what killed it |
|---|---|---|---|
| `F0` | rho baseline | n/a | measured `n^0.5072`, `r²=0.998`, matches `√(πn/12)` |
| `NULL-BATTERY` (N1-A) | any leak from `k` into `x(kP)` | **DEAD** | 2028 χ² tests, 0 pass Bonferroni; the calibrated control passes 1 |
| `MULT-SUBGROUP-BIAS` (N1-B) | `μ_m` as a better-than-random factor base | **DEAD** | deviation `∝ m^{−0.589}`; sampling noise is `−0.5`; shrinks with `m` |
| `RHO-LSH` (N1-C) | coordinate-metric nearest neighbours beat birthday | **DEAD** | no translation distortion under any metric; permutation null |
| `KTREE-FILTRATION` (K1) | Wagner k-tree via coordinate predicates | **DEAD** | `ρ = 1.00` for every predicate; `Z_n` control returns `ρ = 2050` vs theory 2048; the sumset of a structured set is indistinguishable from uniform |
| `SMOOTH-POINTS` (N2) | integer smoothness of `x` as a group-compatible notion | **DEAD** | 540669 pairs, `ρ = 1.028`; the control deviates more |
| `SNFS-ANALOGUE` / `XEDNI-CM` (L1) | lifting to characteristic 0 | **DEAD** | `E(Q) = {O}` for `y²=x³+7` (four independent verifications); 0 dependencies in 1080 xedni lifts |
| `HOM-SEARCH` (T1) | transfer via `log_g x(P)` in `F_p^*` | **DEAD** | quasi-homomorphism defect uniform; 12-map machine search finds only estimator bias; the apparent 5σ result was a sampling artifact reproduced by a random bijection |
| `IC-ELIMINANT` (IC2) | algebraic decomposition oracle | **DEAD** | eliminant density `1.000`, `nnz ∝ m^1.956`, `μ_m` identical to random |
| `IC-BUILD` (IC1) | index calculus, actually built | **DEAD** | `k=2: n^0.977` · `k=3: n^0.605→2/3` · `k=6: n^0.465→3/5`; 256-bit projections `2^257 / 2^174 / 2^157` vs rho `2^127.8` |
| `SAT-SCALING` (SAT1) | bit-level solver on the ECDLP | **DEAD** | slope 2.21 bits⁻¹ vs 1.0 brute force, 0.5 rho; `2^551` s at 256 bits |
| `MU6-GRADED-SEMAEV` (G1) | does the `j=0` symmetry lower algebraic complexity | **DEAD** (exponent-level) | `S_3`, `S_4` are `μ_3`-graded, but fixing `x_R` breaks the grading: eliminant splits into exactly equal thirds. Orbit reduction is a constant factor 6 |
| `SEMAEV-COPPERSMITH` (C1) | lattice attack on box factor bases | **DEAD** | derived `e* = 2(s+1)^k/(k(d+s)(d+s+1)^k)`; measured `e* ≈ 0.12–0.14` stable across 32/40/48 bits and saturating in shift order, vs `1/k = 0.5` needed at k=2 and a 47.6× shortfall at k=4 |
| `LATTES-DYNAMICS` | functional-graph anomalies of the Lattès walk | **DEAD** (indirect) | rho's measured constant matches random-map theory to a few % at every size — the walk *is* random-like |
| `COVER-GENUS` | higher-genus covers | **DEAD** (analytic) | a degree-`d` cover has `#Jac ≈ p^g`; index calculus there costs `Õ(p^{2−2/g}) > p^{1/2}` for every `g ≥ 2`. Descent needs a *smaller field*; `F_p` has none |
| `ANOMALOUS-ESCAPE` | p-adic elliptic log when `#E ≠ p` | **DEAD** (analytic) | `v = k·u + n·w` with `u,v,w ∈ pZ_p`; dividing by `p` leaves `n·(w/p)` unknown mod `p` unless `p | n`. Information is recoverable mod `p`, the scalar lives mod `n`; they coincide only for anomalous curves |

---

## LIVE QUEUE

_Merged with the multi-agent sweep's ranking (34 ranked, 25 discarded; `ecdlp/data/wf_ranking.json`). Its rank-1 item is now CLOSED as C1. Items already settled by this session's measurements are struck out with the entry that killed them._

### 1. ~~`coppersmith-crossing-exponent`~~ — **CLOSED as C1.** Measured `e* ≈ 0.13`, saturating in shift order, against `1/k` needed. Shortfall 5.6× at k=2, 47.6× at k=4.

### 2. ~~`collinear-3sum-isd`~~ — Relation search as a low-weight-codeword problem: Riemann-Roch evaluation vectors, Plucker collisions, and ISD
**Cost:** half day · **Non-generic:** Explicit F_p coordinates: v(P)=(1,x,y,x^2,xy,...) makes the parity-check matrix computable without knowing any discrete log (verified 11987/11987 agreement between singularity of the m x m e

**Experiment:** C or Python+gmpy2 on y^2=x^3+7 over p = 1 mod 3 with prime order, 20-40 bits. (a) For m in {3,4,5} and N spanning 2^4..2^12, enumerate (m-1)-subsets of the factor base, hash-lookup the negated sum, count actual relations, report total work per relation. (b) Implement Prange and Stern over F_p on the explicit m x N evaluation mat

**Kill:** DEAD if (a) reproduces total work ~p in every cell and (b) gives Prange success = m!/N^{m-1}. ALIVE only if some (N,m) cell shows total work materially below p — that would falsify the framing all downstream ideas rest on.

**Auditor's fatal flaw:** The Plucker meet-in-the-middle costs N^m, a factor N worse than the N^{m-1} textbook baseline; and at weight = redundancy = m with rate -> 1, ISD is provably worse than brute force.

> **Status: largely settled by IC1: relation generation by guess-and-check measured at Θ(n) for every m and k, and the full attack measured at n^0.977 / n^0.605 / n^0.465 → asymptotes 1, 2/3, 3/5. What remains is their (N,m) grid as a second, independent confirmation.**

### 3. `weak-family-positive-controls` — Positive-control calibration: do coordinate-level distinguishers have ANY power, measured against planted bias
**Cost:** 1 day · **Non-generic:** The test arm feeds real F_p coordinate features (cubic character, limb boxes, Hamming weight) and secp256k1's own structure (j=0 CM, free lambda, pseudo-Mersenne limbs) into detectors that a

**Experiment:** Replace the proposed broken-curve positive controls with PLANTED bias: on Z/n under an AES bijection, reveal a chosen linear functional of k in a chosen coordinate bit with probability eps; sweep eps down and bit size 20->26 up; report per-detector ROC and the smallest eps detected at 5% FPR. Separately pre-register the known j=

**Kill:** DEAD-FOR-THE-PROGRAM if every detector's MDE tracks 1/sqrt(n) — detection power then buys nothing a birthday bound does not, and all bias-hunting nulls are confirmed uninformative-but-unnecessary. DEAD-FOR-SECP256K1 if, after quot

**Auditor's fatal flaw:** The originally proposed positive controls (anomalous, small-k) are known-ATTACKABLE, not known-BIASED — their attacks are an exact p-adic isomorphism and an exact pairing, neither of which predicts any statistical anomaly, so the 

### 4. ~~`cm-height-oracle-probe`~~ — Hunting a computable proxy for the Z[omega]-norm: a 4-query reduction from ECDLP to any height oracle
**Cost:** hours · **Non-generic:** The F_p coordinate encoding (integer size, rational reconstruction, characters) against the canonical short Z[omega] representative; the CM lattice makes a height exist, and the question is 

**Experiment:** Synthesize s = N(alpha) + noise with tunable Pearson eps; run the least-squares monic-quadratic fit; plot minimum eps for EXACT recovery of 2a-b at 20/28/36/44 bits; test the prediction 1-eps_crit ~ n^{-1/2}. Alongside, log the Voronoi piece-length scaling (median second-difference run length / sqrt n; measured 0.42 at n=2^20) t

**Kill:** DEAD if 1-eps_crit ~ n^{-1/2} holds across four sizes (implying eps within 2^-128 of 1 at 256 bits) and the Voronoi run-length ratio is constant. Also DEAD if end-to-end exact recovery from any real statistic fails at 20 bits — it

**Auditor's fatal flaw:** The proposed oracle is DLP-complete: h(Q)-h(Q-G)+1 = 2a-b recovers the full logarithm in O(1) group operations, so N(alpha) is a bijective repackaging of the discrete log, not an independent height.

> **Status: pre-killed by N1-A (no coordinate statistic depends on the scalar) — but their reframing as an oracle-QUALITY THRESHOLD (how exact must a height oracle be?) is genuinely new and still open.**

### 5. `special-p-carryfree-descent` — Descent along p = t^8 - t - 977 (t = 2^32): carry-free Weil restriction to Z
**Cost:** 30 minutes · **Non-generic:** The SNFS representation p = f(2^32) with f sparse and tiny-height, so mod-p reduction is a shift-and-add; the factor base is defined by the base-t digit expansion of x.

**Experiment:** A (30 s, no curve, no prime): for X in {64,256,1024,4096} loop over integer pairs |x1|,|x2| <= X, solve S_3(x1,x2,X3) as a quadratic in X3, count exact integer roots with |x3| <= X. Measured: N(X) = 3 at X=64,256,1024, all degenerate. B (1 min): for representations p = t^k - t - c with k = 2,4,8 at matched p, measure the carry-f

**Kill:** DEAD if N(X) does not grow like X^2 (the heuristic count a useful factor base needs) — it is constant at 3. DEAD if B confirms the k-independence law, since the SNFS shape then contributes literally nothing over a trivial height b

**Auditor's fatal flaw:** Carry-freeness is logically equivalent to S_m = 0 over Z, i.e. an exact global relation among bounded-height lifts — Siegel/Mordell finiteness, which is the xedni failure mode in different clothing.

### 6. ~~`dl-free-homomorphy-defect`~~ — Homomorphy-defect maximization over coordinate circuits, with exact spectra and a 2-torsion positive control
**Cost:** 30-60 minutes · **Non-generic:** Multiplicative/additive characters of low-degree polynomials in (x, y, beta*x) and limb slices of the canonical representative — objects defined by the field representation, with the additio

**Experiment:** Walk k -> kG for k = 0..N-1 in C, store f(kG) as one byte, take one real FFT of length N. Report max_{c!=0}|ghat(c)| / sqrt(N) for f in {chi(x), chi(g(x)) for random deg<=4 g, chi_3(x), LSB(x), MSB(x), limb slices}, at N = 2143, 8293, 32497, 130579, 524269, against a matched random +-1 control (measured 0.459) and a matched AES-

**Kill:** DEAD if alpha for every family equals the random control's alpha within noise across five sizes (measured so far: chi(x) 0.497, chi(deg-4) 0.464, LSB 0.440, MSB 0.466, best-of-200 0.476 vs random 0.459). ALIVE only if the ratio to

**Auditor's fatal flaw:** eps as literally defined is maximized to 1/2 by degenerate f (g = a perfect square gives f == +1), and unbalanced f fake a signal entirely through the mean; Deligne pins the honest statistic at alpha = 1/2 for the whole algebraic 

> **Status: pre-killed by T1 (quasi-homomorphism defect uniform; 12-map machine search found only estimator bias).**

### 7. `bilinear-sumset-oracle` — S_4 as a rank-4 bilinear form: relation search is orthogonality search, and the sum-membership oracle
**Cost:** 2 hours · **Non-generic:** The exact identity S_4 = (<u,v>^2 - D(u)D(v))/4 (verified symbolically) plus the rationality of sqrt(disc) forced by x(P1+P2), x(P1-P2) both lying in F_p — a coordinate-level fact with no ge

**Experiment:** On 24/28/32/36-bit curves, implement m=3 relation gathering honestly: precompute the sorted table of x(P2 +- P3) over B x B, then for each random R sort x(R +- P1) against it. Count group operations, not wall clock. Plot log(ops)/log(p) against the rho baseline sqrt(pi*n/4) on the same curves.

**Kill:** DEAD if the exponent sits at 2/3 across all four sizes. Skip the proposed degree-<=6 vanishing-ideal fit (it returns the known ideal of the 2-dimensional image surface) and the sort-vs-pairs timing (that IS the birthday bound, not

**Auditor's fatal flaw:** The stated success condition is arithmetically empty: (2+delta)/3 < 1/2 needs delta < -1/2, so even a free perfect sum-membership oracle gives p^{2/3} = 2^170; and the rank-4 identity is specific to Res of two binary quadratics an

### 8. ~~`detectable-difference-set`~~ — Beating birthday needs a hash that detects a whole difference set, not just equality
**Cost:** hours · **Non-generic:** The hash reads the coordinate representation (top bits, x mod small primes, character vectors, canonical-lift digits, Lattes-orbit minima); in the generic model conditional and unconditional

**Experiment:** On y^2=x^3+7 with prime order at ~2^19, 2^22.7, 2^25.3 (and up to 2^26), enumerate the entire orbit x(jP0) and compute exact A(k) = #{j : h(x_j)=h(x_{j+k})} for all k <= 256 in one pass, against a shuffled control. Hash families: top-b bits, x mod small primes, character vectors, and — the two families NOT covered by Kohel-Shpar

**Kill:** DEAD if r-1 decays like n^{-1/2} across five sizes (measured 0.0315 -> 0.0099 -> 0.0031) and the real curve's worst-z over 256 shifts is indistinguishable from the shuffled control's. Log max observed r as a permanent upper bound 

**Auditor's fatal flaw:** At the strength the cost formula needs (r ~ |T| with range B = O(|T|)), the hypothesis is equivalent to predicting the top log2(n/|T|) bits of the discrete log with constant advantage — the premise is the conclusion.

> **Status: pre-killed by N1-C and K1 (no translation distortion; no compatible predicate). Their exact-autocorrelation version is a stronger instrument than my permutation test.**

### 9. ~~`mw-lift-height-vs-reduction`~~ — Quantifying the height gap: exponentially many small lifts for F_p^* vs polynomially many for E
**Cost:** hours · **Non-generic:** Reduction E(K) -> E(F_p) at a degree-1 prime, Neron-Tate canonical heights, Mordell-Weil lattice geometry — relations would be found by lattice enumeration under a height quadratic form, inv

**Experiment:** Extend scratchpad/lat5.gp: sweep r = 3, 5, 8, 12 using small-generator curves from rank tables (and, for r >= 8, the multiquadratic-twist construction the idea itself proposes), p from 10 to 26 bits with #E(F_p) prime, ~200 primes per cell. Per cell record the full distribution of lambda_1/GH and the LLL-reduced Gram diagonal pr

**Kill:** DEAD if the KS p-value exceeds 0.01 in every cell. Do NOT use the originally stated Poisson null — the relation set is a sublattice by construction, so a Poisson test is guaranteed to 'reject' and would read as a spurious positive

**Auditor's fatal flaw:** To write down the relation lattice at all you must already know r discrete logs; without them the only membership test is one group operation per candidate, so the lattice is a costume over a generic search.

> **Status: settled by L1: E(Q) = {O} for y²=x³+7, and rational points of height ≤ H grow as (log H)^{r/2} vs π(H) ~ H/log H.**

### 10. ~~`sat-scaling-exponent-ablation`~~ — Measured hardness exponent of bit-level ECDLP encodings, with p-shape / lambda / ladder ablations
**Cost:** hours · **Non-generic:** The CNF sees the F_p multiplier and the pseudo-Mersenne reduction circuit (2^256 = 2^32 + 977 mod p), structure no generic algorithm can query.

**Experiment:** Build the CNF once per curve with a sound complete encoding — first fix the two bugs: use projective/Jacobian coordinates or an explicit exceptional-case disjunction so s*(x2-x1)=y2-y1 never silently forces UNSAT (measured degeneracy 9.1% at b=8, 2.9% at b=10), and hand-circuit pseudo-Mersenne reduction as shift+add+conditional-

**Kill:** DEAD if refutation requires L = b (only a fully specified scalar is refutable), which forces c = 1 exactly and proves CDCL cannot beat enumerating its own backdoor. ALIVE only if refuting-L < b, and only then is the expensive expo

**Auditor's fatal flaw:** The pilot's measured c >= 1.1 is WORSE than scalar-bit enumeration (the b scalar bits are a strong backdoor, so complete CDCL is at worst 2^b poly) — reporting 1.1 as 'the exponent' would be a solver-heuristic pathology, not a pro

> **Status: base arm measured in SAT1 (slope 2.21 bits⁻¹). The ABLATION arms — special-prime shape, λ constraint, ladder encoding — are the open part, and a slope shift would be a real non-generic effect.**

### 11. ~~`interval-factor-base-decomposition-exponent`~~ — Machine-searched structured factor bases over F_p, judged against a counting bound and a measured solve cost
**Cost:** hours (plus msolve build) · **Non-generic:** Semaev polynomials (coordinate ring of E^m), the integer ordering of F_p, and the mu_3-stable choice of S available only for j=0.

**Experiment:** Install msolve (open-source, F4, builds from source). On a 20-bit curve with S_4 cached, form the ideal (S_4(x1,x2,x3,x_R), prod_{s in S}(x_i - s) for i=1..3) and sweep |S| over 20,40,60,80,100,120 for S = interval, S = mu_d coset, S = random control. Record msolve's maximum Macaulay degree and matrix dimension.

**Kill:** DEAD if d_reg/|S| converges to a positive constant (prediction: d_reg = Theta(|S|) with slope ~m, columns ~|S|^m, identically for all three families) — that confirms the minimal-vanishing-polynomial dichotomy and closes the algebr

**Auditor's fatal flaw:** For any S the unique minimal polynomial vanishing on it has degree exactly |S|, so either the solver pays degree |S| (worse than the N^{m-1} brute force) or S is not Zariski-closed and Groebner has zero purchase; the stated kill c

> **Status: the eliminant half is settled by IC2 (density 1.000). Their version needs msolve for the degree of regularity, which this environment lacks — the top remaining tooling gap.**

### 12. `scalar-class-solver-exponent-grid` — Sub-birthday-on-a-class: a class x solver grid measured against the universal sqrt(n/delta) line
**Cost:** 1-2 days · **Non-generic:** The classes themselves are generic-subset DL (Shoup extends verbatim to a restricted exponent set); the non-genericity lives only in the solver column — F4 on summation systems, LLL small-ro

**Experiment:** C harness on y^2=x^3+7 over prime-order p = 1 mod 3 at 24/28/32/36/40 bits measuring group-operation COUNTS (not wall clock) for (a) kangaroo on an interval of width W, (b) Gaudry-Schost on the Eisenstein ball {a+b*lambda : |a|,|b| < R}, (c) splitting-system search on low-weight k, each swept over 4-5 class sizes AT FIXED n so l

**Kill:** The harness is CORRECT only if all three give e = 0.500 +- 0.02 and the density-corrected total lands on sqrt(n/delta). Treat any measured e < 0.48 as an instrumentation bug (censored timeouts, miscounted |C| from collisions, toy-

**Auditor's fatal flaw:** The k = a*b cell has density 0.64 at 256 bits, so |C| ~ n and the cell IS the target problem restated; and Cheon 2006 is a generic algorithm with a matching generic lower bound, so it is not a precedent for exponent structure defe

### 13. `eisenstein-residue-coordinates` — Eisenstein residue coordinates: Coppersmith-Odlyzko-Schroeppel smoothness transplanted, with beta as an exact 
**Cost:** 1 day · **Non-generic:** The ring isomorphism F_p = Z[omega]/(pi) acting on the COORDINATE field rather than the group, so that beta and the unit omega are the same object: nu(beta*x)=nu(x) exactly (0 failures in 30

**Experiment:** Generalize scratchpad/count2.py: (i) count decompositions of a random target, S_4(x1,x2,x3,x(R))=0, not S_3=0 among factor-base points; (ii) build the relation matrix over F_n and report rho_rank, not rho_count; (iii) sweep p from 2^20 to 2^32 with B = p^{1/3} and fit the exponent of log(rho_rank)/log(p).

**Kill:** DEAD if rho_rank -> 1 with no trend in p (nontrivial ratios already measured at 1.25, 1.28, 1.44, 1.25 vs interval 1.06, 1.16, 1.17, 0.80 — a constant, consistent with factor-3 orbit folding). A constant, however large, is dead; o

**Auditor's fatal flaw:** A box condition is archimedean so it cannot enter the ideal at all — the Groebner system for an Eisenstein box is bit-identical to the interval case; and a linear volume-preserving change of variables leaves the Coppersmith reach 

### 14. ~~`torus-dickson-factor-base`~~ — Dickson/torus factor base: the one intermediate-size ALGEBRAIC subset of F_p that secp256k1 admits
**Cost:** 2 hours · **Non-generic:** Field structure of F_p and F_{p^2} (norm-1 torus, Dickson/Lucas recurrences), the arithmetic of p+1 for this specific prime, and Semaev polynomials on top; 'x in S_d' is a genuine degree-d c

**Experiment:** (1) Reproduce and log the eliminant density using the 2-sparse binomial x^d - 1 (strictly sparser than Dickson, so a failure kills Dickson a fortiori), d = 3..40, recording degree and nonzero-term count per remaining variable. (2) Time the full constrained solve for m=3,4 on real S_4/S_5 over a 24-32 bit prime, five values of d 

**Kill:** DEAD the moment step (1) shows density (it does). Predicted alpha = m-1 exactly, forced by output-size counting rather than heuristics, giving total cost d*(p/d) = p ~ 2^256.

**Auditor's fatal flaw:** The subfield condition x^q - x that makes Weil descent work is ADDITIVE and linearizes at zero degree cost; the Dickson condition is multiplicative and its degree d propagates into every eliminant. Also: the best divisor of p+1 is

> **Status: the μ_m case is settled by IC2 (eliminant dense, μ_m indistinguishable from random). The Dickson/torus variant over F_p² is not covered by that measurement.**

### 15+ — the remaining 20 ranked ideas are in `ecdlp/data/wf_ranking.json`,
and the 25 the sweep discarded (with reasons) are in the same file. They are kept
rather than deleted so a later session can re-open one if a measurement here turns.

## Ideas dropped as pre-killed by this session's measurements
`fp-log-quasihom` (T1) · `detectable-difference-set` (K1 + N1-C) ·
`lattes-orbit-graph` (F0's random-map agreement) · `xedni-cm-quantified` (L1) ·
`mw-lift-height-vs-reduction` (L1) · `p-shape-distinguisher-battery` (N1-B, K1) ·
`cm-height-oracle-probe` (N1-A: no coordinate statistic depends on the scalar, and the
`Z[ω]`-norm is a function of the scalar) · `interval-factor-base-decomposition-exponent`
(IC1 + IC2) · `mu3-character-gauss-sum-transfer` (N1-A included the cubic character;
and `χ₃(x(λP)) = χ₃(β)χ₃(x(P))` is an identity relating `P` to `λP`, not to `k`).

---
*Updated 2026-09-17 after F0, N1, N2, K1, L1, T1, IC1, IC2, SAT1, G1, C1, and the
multi-agent sweep (71 agents, 47 ideas, 34 ranked).*
