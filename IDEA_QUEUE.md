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
| `LATTES-DYNAMICS` | functional-graph anomalies of the Lattès walk | **DEAD** (indirect) | rho's measured constant matches random-map theory to a few % at every size — the walk *is* random-like |
| `COVER-GENUS` | higher-genus covers | **DEAD** (analytic) | a degree-`d` cover has `#Jac ≈ p^g`; index calculus there costs `Õ(p^{2−2/g}) > p^{1/2}` for every `g ≥ 2`. Descent needs a *smaller field*; `F_p` has none |
| `ANOMALOUS-ESCAPE` | p-adic elliptic log when `#E ≠ p` | **DEAD** (analytic) | `v = k·u + n·w` with `u,v,w ∈ pZ_p`; dividing by `p` leaves `n·(w/p)` unknown mod `p` unless `p | n`. Information is recoverable mod `p`, the scalar lives mod `n`; they coincide only for anomalous curves |

---

## LIVE QUEUE

### 1. `IC-SWEEP-FINISH` — finish the measured index-calculus curve at `k=3,4,6`
**Source:** seed · **Cost:** running · **Why top:** it is the mission's central artifact —
a real attack, measured across sizes, plotted against rho. `k=2` is in (`n^0.977`);
`j=2` should land near `n^{2/3}` and `j=3` near `n^{3/5}`, demonstrating the approach to
`n^{1/2}` **from above** empirically rather than by assertion.
**Kill:** all fitted exponents `≥ 0.5` ⇒ the combinatorial family is closed with data.

### ~~2. `MU6-GRADED-SEMAEV`~~ — **CLOSED, see ATTACK_LOG G1.** The grading is real
(`S_3` weight 1, `S_4` weight 0 under the diagonal `μ_3` action) but does not survive
fixing the target, because the action moves `R` to `λR` rather than fixing it. The
eliminant splits into exactly equal thirds. What remains untested is the Gröbner solving
degree itself, which needs an F4/F5 engine this environment does not have; the eliminant
measurement is the strongest available proxy.

### 2b. `MU6-GROEBNER-DEGREE` (needs tooling) — measure the degree of regularity directly
**Source:** `gen:semaev` + `gen:cm-j0` · **Cost:** days · **Non-generic:** the order-6
automorphism group acts on `S_m`; the quotient of `E` by `⟨ω⟩` is rational, so the
Weber coordinate `u = x³` is a genuine change of the polynomial system.
**Hypothesis `[S]`:** re-grading Semaev systems by `μ_6`-invariants lowers the first-fall
/ solving degree by ~3 per variable.
**Why it survives IC2:** IC2 measured the *eliminant*, not the Gröbner solving degree.
This is the one algebraic quantity still unmeasured.
**Experiment:** build `S_3, S_4` in `u = x³`, measure the degree of regularity and the
solving exponent for the decomposition system, symmetrised vs not, over 5 sizes.
**Kill:** solving exponent `≥ (k−1)−0.1` in both encodings, or no degree drop.

### 3. `U3-QUADRATIC-PHASE` — Fourier-analytic search above the linear level
**Source:** `gen:wild` · **Cost:** days · **Non-generic:** characters of the coordinate
representation. **Established `[E]`:** linear Fourier is dead — Weil gives square-root
cancellation for `χ(x(kP))`, which is exactly what N1 measured.
**Hypothesis `[S]`:** the quadratic (Gowers `U³`) level is not covered by that bound;
a large `U³` norm would be a genuine structural finding.
**Experiment:** estimate `‖f‖_{U³}` for `f(k) = χ(x(kG))` at `n = 2^20…2^26` with a
permutation-calibrated null; also the largest Fourier coefficient of the derivative
`Δ_h f`. **Kill:** every statistic inside the control's 99.9th percentile with no
trend in `n`.

### 4. `PREPROCESSING-ADVICE` — can coordinate-based advice beat `ST² = Θ(n)`?
**Source:** `gen:ml-sat` · **Cost:** weeks · **Non-generic:** the advice is computed from
and queried against the explicit representation. **`[E]`:** the generic preprocessing
trade-off `ST² = Θ̃(n)` (Corrigan-Gibbs–Kogan; Mihalcik; Bernstein–Lange) is proved in the
generic model only. **Hypothesis `[S]`:** a *learned* advice string exploiting the
coordinate structure beats it. **Experiment:** at 20–30 bits, compare a learned advice
arm against a classical table arm at equal storage, fit the `S` vs `T` slope.
**Kill:** fitted slope `≥ −0.55` at every size and the learned arm never beats the table.

### 5. `EISENSTEIN-BALL` — the automorphism-invariant lattice factor base
**Source:** `gen:semaev` · **Cost:** days · **Non-generic:** `F_p ≅ Z[ω]/π`, and
multiplication by `ω` (= `β` on x-coordinates) is an **isometry** of the Eisenstein
lattice, so a norm ball is simultaneously a factor base and automorphism-stable.
**Status:** partially pre-killed — K1 already measured the automorphism-invariant
interval predicate `orbmin(x) < p/2^d` at `ρ = 1.002`. The lattice-ball version is a
2-D rather than 1-D variant of the same thing.
**Experiment:** add the Eisenstein ball to the K1 predicate battery and to the Group B
hit-rate test. **Kill:** `ρ = 1` and null hit rate (expected).

### 6. `SAT-ABLATION` — does structure help a bit-level solver at all?
**Source:** seed + `gen:ml-sat` · **Cost:** hours · **Status:** base measurement running
(`SAT1`). The ablation arms — special-prime shape, `λ` constraint, ladder encoding —
are the part that could surprise: if any ablation *shifts the slope*, that is a real
(if small) non-generic effect. **Kill:** slope unchanged by `< 0.05` bits⁻¹ across arms.

### 7. `POINT-TO-CLASS-GROUP` — a partial map to a group with subexponential DLP
**Source:** `gen:transfer` · **Cost:** days · **Non-generic:** class-group arithmetic.
**Hypothesis `[S]`:** some `Ψ` computable from coordinates is multiplicative on a
noticeable fraction of triples. **Why it is not already dead:** T1 tested `F_p^*` only.
**Kill:** every candidate is constant or fails `Ψ(R+S)=Ψ(R)Ψ(S)` on more than a `1/h`
fraction — i.e. behaves like a random function.

### 8. `CONDUCTOR-VOLCANO` — the isogeny class as a search space
**Source:** `gen:cm-j0` · **Cost:** days · **`[E]`:** isogenies preserve group order, so no
direct win. **Hypothesis `[S]`:** some curve in the `F_p`-isogeny class has an encoding
with lower measured rho cost (a constant-factor engineering result at best).
**Kill:** measured rho cost `≥` the `j=0` baseline on every reachable curve.

### 9. `ELLIPTIC-NET-2D` — inverting a bilinear recurrence over `Z[ω]`
**Source:** `gen:transfer` · **Cost:** days · **Non-generic:** the EDS/division-polynomial
bilinear identity is an algebraic relation on coordinates. **Hypothesis `[S]`:** the
rank-2 `Z[ω]` index lattice substitutes for descent. **Kill:** solving degree grows
linearly in the number of unknown digits ⇒ never better than `√n`.

### 10. `CM-HEEGNER-ORBITS` — the only known source of many height-controlled points
**Source:** `gen:special-prime` · **Cost:** weeks · Directly targets the gap L1 measured:
`E(Q)` is trivial, but CM/Heegner orbits give exponentially many points of controlled
height over class fields. **Kill:** the dlog function on `Cl(D)` is Fourier-flat and
admits no relations beyond Euler-system ones.

### 11–18 (lower priority, one line each)
- `SPARSE-LIMB-CP` `gen:index-calculus` — limb-sparse factor base for `p = 2^256−2^32−977`
  attacked by constraint propagation. Kill: solver time `∝ |S|^{k−1}`.
- `SEMAEV-SKEW-COPPERSMITH` `gen:index-calculus` — skewed multivariate Coppersmith on
  `j=0` summation polynomials. Kill: recoverable exponent stays `≤ 1/4` while relations
  need `≥ 1/(k+1)`. *(The exponent gap is large; see ATTACK_LOG's arithmetic.)*
- `SPECIAL-P-CARRYFREE` `gen:semaev` — carry-free Weil restriction along `t^8−t−977`.
  Kill: carry-free `|B| ≤ p^{1/4}` for `S_3`, `p^{1/12}` for `S_4`.
- `LOCAL-DUALITY-TORSOR` `gen:lifting` — local Tate duality as a dlog functional.
  Kill: the Miller value over `Q_p` is an `n`-th power in every case (pairing trivial).
- `CANONICAL-LIFT-DIGITS` `gen:wild` — higher `p`-adic digits of the canonical lift.
  Kill: digits statistically independent of `k` (the splitting argument in ATTACK_LOG's
  `ANOMALOUS-ESCAPE` entry says they must be).
- `ALPHA-MOD-PI-COTANGENT` `gen:cm-j0` — the cotangent scalar `α mod π`.
  Kill: the étale/formal splitting is computable without `k`.
- `MULTIPLICATIVE-COSET-LEAK` `gen:wild` — a multiplicative character of `k` would buy
  `√(n/d)`. Kill: MI below `10^-3` bits at 24/28/32 bits with no trend. *(N1 already
  covers the additive-character version.)*
- `FOURIER-HEAVY-HUNT` `gen:ml-sat` — sparse recovery over bit-level coordinate
  functions. Kill: peak inside `1.3×` the permutation-null band with no trend.

---

## Ideas dropped as pre-killed by this session's measurements
`fp-log-quasihom` (T1) · `detectable-difference-set` (K1 + N1-C) ·
`lattes-orbit-graph` (F0's random-map agreement) · `xedni-cm-quantified` (L1) ·
`mw-lift-height-vs-reduction` (L1) · `p-shape-distinguisher-battery` (N1-B, K1) ·
`cm-height-oracle-probe` (N1-A: no coordinate statistic depends on the scalar, and the
`Z[ω]`-norm is a function of the scalar) · `interval-factor-base-decomposition-exponent`
(IC1 + IC2) · `mu3-character-gauss-sum-transfer` (N1-A included the cubic character;
and `χ₃(x(λP)) = χ₃(β)χ₃(x(P))` is an identity relating `P` to `λP`, not to `k`).

---
*Updated 2026-09-17 after F0, N1, N2, K1, L1, T1, IC1, IC2, SAT1, G1.*
