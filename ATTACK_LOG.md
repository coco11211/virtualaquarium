# ATTACK_LOG.md — secp256k1 ECDLP attack program

Adversarial research log. Every idea tried, its verdict, where its data lives, and why it died.

**Ground rules in force**
- The solver never receives the secret scalar. `Target` stores it under a name-mangled
  attribute; solvers get `Target.public()` only. A static leak audit runs in the test suite.
- Targets are generated from a seeded RNG the solver cannot read. Many targets per size.
- Cost accounting includes precomputation, linear algebra and Gröbner time — not just the fast step.
- A heuristic complexity argument is never a result. Only measured scaling counts.
- Claims are tagged [ESTABLISHED] / [HEURISTIC] / [SPECULATION].
- Papers are cited only when their existence is certain; otherwise a `SEARCH:` term is given.

**Verdict vocabulary:** `DEAD` · `INCONCLUSIVE` · `SURVIVING`

---

## F0 — Foundation: toy curves, arithmetic, and the rho bar
**Status:** COMPLETE · **Date:** 2026-09-17

**What was built**
- `ecdlp/tools/gen_curves.gp` — PARI/GP generator for toy curves `y² = x³ + 7` over primes
  `p ≡ 1 (mod 3)` with **prime** group order `n`, `n ≡ 1 (mod 3)`, so that both the negation map
  and the `j = 0` endomorphism `(x,y) ↦ (βx, y) = λ·(x,y)` exist exactly as on secp256k1.
  66 curves: 22 sizes (20…62 bits) × 3 curves each.
- `ecdlp/csrc/fp.h` — Montgomery arithmetic mod `p < 2^63` (the bound keeps REDC free of
  128-bit overflow), affine curve arithmetic.
- `ecdlp/csrc/rho.c` — van Oorschot–Wiener parallel collision search with distinguished
  points and batched (Montgomery-trick) inversions. Three modes: plain, negation,
  negation+endomorphism. Fruitless 2-cycles are detected and escaped by doubling the
  lexicographically smaller point of the cycle — a function of the cycle, not the path, so
  the iteration map stays deterministic and collisions stay meaningful.
- `ecdlp/py/toolkit.py` — curve loading, pure-python reference arithmetic, ctypes bridge,
  sealed-target generation, log-log scaling fits.
- `ecdlp/py/test_core.py` — C-vs-python scalar-multiplication agreement over all 66 curves,
  target-pipeline round trip, static secret-leak audit, and rho correctness in all three
  modes on every curve ≤ 32 bits. All pass.

**Curve invariants verified for all 66 curves:** `G` on curve · `nG = O` · `n` prime ·
`p ≡ n ≡ 1 (mod 3)` · `β³ = 1, β ≠ 1` · `λ² + λ + 1 ≡ 0 (mod n)` · `λG = (βx_G, y_G)` · `p < 2^63`.

**The bar (measured, not assumed).** 33 curves, 20–40 bits, 30 independent hidden targets each.

| mode | measured C in `ops = C·√n` | theory | fitted exponent | r² |
|---|---|---|---|---|
| plain | 1.2485 ± 0.1147 | √(π/2) = 1.2533 | 0.5045 | 0.9983 |
| negation | 0.9270 ± 0.0848 | √(π/4) = 0.8862 | 0.4979 | 0.9983 |
| negation+endomorphism | 0.5518 ± 0.0597 | √(π/12) = 0.5117 | 0.5034 | 0.9978 |

Fruitless-cycle escapes: ≲ 3·10⁻⁴ of steps. Stall-restarts: **zero** on every run.

**Conclusion.** The measured baseline reproduces `√(πn/12)` to within a few percent, with the
expected `n^0.5` exponent. **Any candidate attack must beat a fitted exponent of 0.503 and
must beat it on measured total cost, not on a step-count of its fast phase.**

Projected bar at 256 bits: `0.5117 · √n ≈ 2^127.8` group operations.

**Data:** `ecdlp/data/curves_raw.json`, `ecdlp/data/rho_bench_small.json`,
`rho_bench_mid.json`, `rho_bench_big.json`, `rho_bench_huge.json`.
**Verdict:** n/a (infrastructure).

---

## Ideas under test

_(none closed yet — see IDEA_QUEUE.md for the ranked queue)_

---

## N1 — NULL-BATTERY: is there any exploitable structure in the representation?
**Status:** COMPLETE · **Verdict: DEAD** (leak and metric channels) · **Date:** 2026-09-17
**Data:** `ecdlp/data/null_battery.json` (v1, contains the bugs below),
`ecdlp/data/null_battery2.json` (corrected) · **Code:** `ecdlp/py/null_battery{,2}.py`

**Group A — leak test.** 2028 χ² independence tests pairing a feature of the secret
scalar `k` (bits, residues mod 3/5/7/11/16, top bits, octile) with a feature of
`x(kP)` (bits, residues, octile, Legendre symbol, **cubic residue class** — the
character natural to `j=0` — and popcount parity), over 8 curves (6 generic, 2 of
secp256k1's special prime shape), 60000 samples each.

| | min p | #(p<0.05) | #(p<Bonferroni 2.47e-5) | KS distance from uniform |
|---|---|---|---|---|
| real | 3.96e-4 | 93 (expect 101.4) | **0** | 0.0177 |
| control (marginals preserved, link destroyed) | 2.29e-5 | 110 | 1 | 0.0149 |

The real data is, if anything, cleaner than the calibrated control. **No leak.**

**Group B — factor-base structure.** Rate at which a structured set `S` meets
`X = {x : x³+7 is a QR}`; exact enumeration, exact null rate `ρ = |X|/p`.

| family | tests | mean z | sd z | max abs z |
|---|---|---|---|---|
| CONTROL random sets | 33 | −0.334 | 1.177 | 2.47 |
| intervals | 33 | +0.260 | 1.120 | 2.63 |
| multiplicative subgroups `μ_m` | 120 | +0.044 | 1.489 | 4.08 |
| t-adic small-digit sets | 6 | −0.306 | 0.761 | 1.09 |

192 tests, max abs z = 4.08 against a Bonferroni threshold of 3.65 — and the excess is
**not exploitable**: fitting the deviation against set size over `m ≥ 30` gives
`|rate − ρ| ∝ m^(−0.589)` (pure sampling noise predicts exactly −0.5) and
`corr(log m, |z|) = −0.206`, i.e. the bias *shrinks* as the factor base grows. A
constant-factor excess would change `m` by a constant and leave every exponent alone.

*Genuine structural observation (not an attack)* `[ESTABLISHED, elementary]`: for
`x` in a multiplicative subgroup `μ_m` with `3 | m`, the cube map collapses `x³` onto
`μ_{m/3}`, so the on-curve test `χ(x³+7)` is a character sum over a *smaller* subgroup
with multiplicity rather than an independent coin — e.g. on `μ_3` the value `x³+7` is
the constant 8, so `μ_3` is entirely on or entirely off the curve. This is a real
`j=0`-specific interaction. It moves constants, not exponents.

**Group C — metric/translation distortion (the premise of `RHO-LSH`).** Permutation
null (300 permutations), statistics = adjusted mutual information and Spearman ρ,
60000 (P,Q,R) triples per test, metrics `|Δx| mod p`, Hamming distance of `x`,
top-8-bit equality, top-8-bit XOR.

MI z-scores lie in [−1.69, +1.42]; smallest permutation p-value 0.0066 against a
Bonferroni threshold of 6e-4; 3 of 88 p-values below 0.05 where 4.4 are expected.
**No translation distortion.** `RHO-LSH` loses its premise and is DEAD.

**Two bugs in my own statistics, found and fixed before reporting** (both manufactured
enormous fake signals, and both are logged here as a caution):
1. Group B v1 sampled structured sets **with replacement** 60000 times even when the
   set had 3 elements, inflating z by `sqrt(60000/|S|)` — it reported `z = −245`.
2. Group C v1 rank-binned the Hamming metric, which is a small integer with heavy ties,
   giving a degenerate χ² and `p = 4e-126`. The control returned `p = 6e-126`, which is
   what exposed it.

---

## K1 — KTREE-FILTRATION: the k-tree obstruction, measured
**Status:** COMPLETE · **Verdict: DEAD** · **Date:** 2026-09-17
**Data:** `ecdlp/data/ktree.json` · **Code:** `ecdlp/py/ktree.py`

**Why this is the decisive question for the whole index-calculus surface.**
With factor base size `m` and `k`-term decompositions, relation generation by
guess-and-check always costs `Θ(n)` in total, so a win requires a *decomposition
oracle*. The only known fast oracle family for `k`-sums is Wagner's k-tree algorithm,
which on `2^l` lists reaches `n^{1/(l+1)}` and would put index calculus at
`n^{2/(l+1)}` — **below rho as soon as `l ≥ 4` (16 lists, `n^{2/5}`)**. Wagner needs a
FILTRATION: predicates `π_j` on group elements, efficiently testable, with
`π_j(P) ∧ π_j(Q) ⟹ π_{j−1}(P+Q)`. In `Z/2^b` these are subgroups; in `Z_m`
(Minder–Sinclair's extended k-tree) they are short intervals, which work because the
integer *value* of an element is visible. `E(F_p)` has **prime** order — no subgroups
at all — and its only integer-valued quantity, the discrete log, is exactly what we
cannot see. So: **is there any predicate on the coordinate representation that is
approximately compatible with the group law?** That is non-generic by construction.

**Test 1 — compatibility ratio** `ρ = Pr[π(P+Q) | π(P), π(Q)] / Pr[π(R)]`, null `ρ = 1`.

| predicate | curves | base rate | mean ρ | max ρ | max abs z |
|---|---|---|---|---|---|
| **[Z_n POSITIVE CONTROL] a < n/2^4** | 11 | 6.25e-2 | **7.98** | 8.00 | 511 |
| **[Z_n POSITIVE CONTROL] a < n/2^8** | 11 | 3.91e-3 | **127.8** | 128.1 | 2251 |
| **[Z_n POSITIVE CONTROL] a < n/2^12** | 11 | 2.44e-4 | **2050.0** | 2058 | 9093 |
| x < p/2^4 · p/2^8 · p/2^12 | 33 | — | 0.998 / 1.022 / 1.014 | 1.43 | 3.84 |
| orbmin(x) < p/2^4, p/2^8 (`j=0` automorphism-invariant) | 22 | — | 1.002 / 1.007 | 1.06 | 2.83 |
| popcount(x) ≤ w (6 settings) | 22 | — | 0.968 … 1.020 | 1.06 | 2.59 |
| x is a 3rd / 5th power residue | 14 | — | 1.001 / 0.997 | 1.01 | 2.01 |
| x is 256-smooth (integer smoothness of the coordinate) | 9 | 3.7e-3 | 1.142 | 4.00 | 3.00 |
| t-adic small digits (special-shape primes) | 4 | — | 1.073 | 1.08 | 1.30 |

The positive control is the point: the interval predicate in `Z_n` at density `2^-12`
returns `ρ = 2050` against the theoretical `1/(2δ) = 2048` — the instrument is
calibrated *quantitatively*, not just qualitatively. Across 104 real-curve tests,
mean z = +0.070, sd 1.326, max abs z = 3.84 against a Bonferroni threshold of 3.49.
**Every predicate on the coordinate representation sits at ρ = 1.00.** The control
fires 2400× harder than the largest real deviation.

**Test 2 — the general version.** Even if every predicate we guessed fails, some other
function of the representation might work. So: is the *sumset* of a structured set
distinguishable from uniform at all? If not, no predicate whatsoever can satisfy the
filtration condition. Two-sample χ² of a rich point-feature vector (top/low/middle
6 bits of `x`, octile, residue mod 29, popcount, top bits of `y`, Legendre symbol,
maximum t-adic digit), structured sums vs uniform points.

| sample | tests | min p | #(p<0.05) |
|---|---|---|---|
| A = {x < p/2^4} sums | 90 | 0.0210 | 2 (expect 4.5) |
| A = {x < p/2^8} sums | 90 | 5.48e-4 | 6 (expect 4.5) |
| CONTROL uniform sums | 90 | 0.0241 | 4 (expect 4.5) |

270 tests, min p = 5.5e-4 against a Bonferroni threshold of 1.85e-4; KS distance of the
p-value set from uniform 0.045. **The sumset of a structured set is statistically
indistinguishable from uniform on the curve.**

**Verdict: DEAD.** There is no filtration on `E(F_p)` visible from the coordinate
representation. Wagner-style k-tree index calculus — the one route whose arithmetic
would put index calculus below `√n` — has no foothold on a prime-order elliptic curve.
The single borderline signal (integer smoothness, ρ up to 4.0 at |z| = 3.0 on 5000
pairs) is being re-run at 40× power as `N2`.

---

## L1 — LIFTING / SNFS-ANALOGUE: why there is no elliptic number-field sieve
**Status:** COMPLETE · **Verdict: DEAD** (and sharper than expected) · **Date:** 2026-09-17
**Data:** `ecdlp/data/lift_gap_1.json`, `lift_gap_2.json` · **Code:** `ecdlp/py/lift_gap.py`

**Part 1 — the factor-base asymmetry, measured.**
Index calculus in `F_p^*` works for one concrete reason: the factor base is
`{primes ≤ B}`, of size `~B/log B`, and a group element's *integer representative*
is decomposed by **factoring it** — subexponential, because `Z` has unique
factorisation and the representative literally carries the group's multiplicative
structure. The elliptic analogue of a prime is a Mordell–Weil generator, and `E(Q)`
is finitely generated of small rank, so points of naive height `≤ H` number
`~(log H)^{r/2}`, not `~H/log H`.

Counted with PARI (`ellrank`, plus independent brute force over `x = a/c²`):

| curve | rank over Q | pts of height ≤ 10² | ≤ 10³ | ≤ 10⁴ | ≤ 10⁵ | primes ≤ 10⁵ |
|---|---|---|---|---|---|---|
| **y² = x³ + 7  (secp256k1)** | **0** | **0** | **0** | **0** | **0** | 9592 |
| y² = x³ + 1 | 0 | 5 | 5 | 5 | 5 | 9592 |
| y² = x³ + 2 | 1 | 4 | 6 | 6 | 8 | 9592 |
| y² = x³ + 3 | 1 | 4 | 4 | 6 | 6 | 9592 |
| y² = x³ + 17 | 2 | 24 | 32 | 50 | 56 | 9592 |

A 1000-fold increase in `H` multiplies the rank-2 point count by 2.3 (the
`(log H)^{r/2}` law predicts 2.5) while multiplying the prime count by 384 (linear).
**The factor base is polylogarithmic where the multiplicative one is linear.**

**The headline fact** `[ESTABLISHED — verified four independent ways]`:
`y² = x³ + 7`, secp256k1's own defining equation, has `E(Q) = {O}`.
- `ellrank` returns bounds `0 .. 0`
- `elltors` returns the trivial group
- analytic rank 0 with `L(E,1) = 3.0414172284…` (nonzero)
- brute force over `|a| ≤ 90000`, `c ≤ 300` finds **zero** affine rational points,
  while the same scan on the control `y² = x³ + 1` finds exactly the expected 5:
  `(0,±1), (−1,0), (2,±3)`
- conductor 21168, `j = 0`, discriminant −21168

So for secp256k1 the natural lift to characteristic 0 has an **empty** factor base.
Not small — empty. Every "lift and find relations among small points" scheme, the
elliptic-SNFS analogue included, starts from nothing on this curve.

**Part 2 — xedni calculus, re-run on CM curves.** Silverman's xedni (1998) sidesteps
the natural lift: it lifts `r` points of `E(F_p)` to integer coordinates and fits a
*new* cubic through them, hoping the lifted points satisfy a relation. Jacobson,
Koblitz, Menezes, Stein and Teske (≈1999–2000) showed this fails because the lifted
points are independent with probability ≈ 1. We re-ran it on `j = 0` CM curves, in
case the CM structure raises the chance of a low-rank lift.

Lift `r` random points, solve the 5-coefficient linear system for a general
Weierstrass cubic through them, verify every point lies on the fitted curve, then
test independence via the determinant of the canonical-height pairing matrix
(`ellbil`), scaled by the product of the diagonal so the test is relative.

| r | curves | trials | fitted OK | **dependent** | singular | bad fit |
|---|---|---|---|---|---|---|
| 3 | 9 (20/24/28-bit, j=0) | 360 | 360 | **0** | 0 | 0 |
| 4 | 9 | 360 | 360 | **0** | 0 | 0 |
| 5 | 9 | 360 | 360 | **0** | 0 | 0 |

**0 dependencies in 1080 lifts** (95% upper bound on the dependency rate: 0.0028).
The CM structure does not help. This reproduces the published result exactly, on
curves chosen to be as favourable as possible.

**Synthesis — and why it agrees with N1 and K1.** The reason index calculus works on
`F_p^*` and not on `E(F_p)` is that the *representative carries the group structure*
in one case and not the other. An integer's factorisation is its decomposition into
factor-base elements; a point's coordinates say nothing about its decomposition.
That is a structural statement, and N1/K1 are its empirical form: no feature of
`x(kP)` depends on `k`, no coordinate predicate is compatible with the group law, and
the sumset of a coordinate-structured set is indistinguishable from uniform.
Surfaces 1, 4 and 5 fail for one shared reason, now measured three different ways.

---

## N2 — SMOOTH POINTS: is integer smoothness of `x(P)` compatible with the group law?
**Status:** COMPLETE · **Verdict: DEAD** · **Date:** 2026-09-17
**Data:** `ecdlp/data/smooth_followup.json` · **Code:** `ecdlp/py/smooth_followup.py`

K1 left exactly one borderline signal: the predicate "`x(P)` is 256-smooth as an
integer" showed mean ρ = 1.14 with one curve at ρ = 4.0 (|z| = 3.0, Bonferroni
threshold 3.49) — on only 5000 pairs. "`x` is smooth" is an honest candidate for a
new notion of a *smooth point*, so it earned a proper test.

Re-run at 108× the sample size: B-smooth x-coordinates collected by **sieving random
windows of [0,p)** (the first attempt trial-divided millions of candidates and was
hopeless), 540,669 pairs over 11 curves, with a matched control on uniform points.

| | mean ρ | mean z | max abs z |
|---|---|---|---|
| real (both x's smooth) | **1.0277** | +0.152 | 2.17 |
| control (uniform points) | — | −0.604 | **2.55** |

The control deviates *more* than the real data. The original ρ = 4.0 was a
small-sample artifact (1 hit where 2.7 were expected, at the 48-bit curve's
base rate of 8e-5). **Integer smoothness of the x-coordinate does not propagate
through the group law.** K1's verdict stands with no loose ends.

---

## T1 — HOM-SEARCH: is there any map out of `E(F_p)` that respects the group law?
**Status:** COMPLETE · **Verdict: DEAD** · **Date:** 2026-09-17
**Data:** `ecdlp/data/hom_search.json` · **Code:** `ecdlp/py/hom_search.py`

A homomorphism `f : E(F_p) → H` with easy DLP in `H` breaks ECDLP; MOV/Frey–Rück is
the classical instance and is dead for secp256k1 because the embedding degree is
astronomically large. But the x-coordinate already *lives* in `F_p^*`, where the DLP
is subexponential — and for secp256k1 the prime is a degree-8 polynomial in `2^32`, so
SNFS makes it cheaper still. So the natural question is whether
`L(P) := log_g x(P) ∈ Z/(p−1)` carries anything. Tested on 20/22/24-bit curves small
enough to tabulate the entire `F_p^*` discrete log.

**T2 — quasi-homomorphism defect.** Is `D = L(P+Q) − L(P) − L(Q) mod (p−1)` non-uniform?
A homomorphism would force `D ≡ 0`; any bias could in principle be amplified.
p-values across 9 curves: 0.042 … 0.937, with a pairing-destroyed control at
0.122 … 0.943. **Uniform.**

**T3 — machine search over candidate maps** (`x`, `y`, `xy`, `x+y`, `x²`, `x³`, `y/x`,
`log x`, `log y`, `log(xy)`, `x mod 1009`, `χ(x)`), scored by the information
`H(f(P+Q)) − H(f(P+Q) | f(P), f(Q))`. Every map on every curve returns
**+0.0236 to +0.0246 bits out of 4.000** — flat across maps, which is the signature of
estimator bias, not signal. The plug-in conditional-entropy bias for 256 joint bins at
`N = 120000` is `(256·16 − 256)/(2N ln 2) = 0.023` bits, matching to three digits.
**No map leaks anything.**

**T1 — direct transfer, and the third statistics bug I caught in my own work.**
The raw test "is `L(kG)` dependent on `k`" returned `p = 1.6e-7, 2.1e-5, 4.4e-5` on the
three 20-bit curves — and nothing at 22 or 24 bits. Vanishing with size is the
signature of an artifact, so it was treated as a bug.

It is one. Sampling **any** deterministic table with replacement inflates χ² by about
`N·dof/n` regardless of the table's content. Predicted excess and measured outcome:

| curve | n | predicted χ² excess | predicted z | real p | **random-bijection control p** |
|---|---|---|---|---|---|
| c20_0 | 524269 | 234.2 | 5.18 | 1.64e-7 | **2.56e-10** |
| c20_1 | 533887 | 229.9 | 5.08 | 2.13e-5 | **1.08e-7** |
| c20_2 | 541543 | 226.7 | 5.01 | 4.36e-5 | **3.26e-4** |
| c22_* | ≈2.1e6 | 58.3 | 1.29 | 0.07 … 0.42 | 0.003 … 0.73 |
| c24_* | ≈8.4e6 | 14.6 | 0.32 | 0.12 … 0.46 | 0.46 … 0.92 |

Replacing the real discrete-log table with a **random bijection** reproduces the effect
and at c20_0 exceeds it (`p = 2.6e-10` vs `1.6e-7`). The predicted artifact size
matches the observed pattern at every size, including its disappearance as `n` grows.
**There is no transfer through `log_g x(kP)`.** The control is now a permanent part of
the test.

*Method note.* This is the third time in this program that a naive statistic
manufactured a "discovery" (after the resampling bug and the tie-degenerate binning in
N1). All three were caught by the same rule: **every test ships with a control built
to satisfy the null.** Without the random-bijection control this one would have read
as a 5σ transfer result on the smallest curves.

---

## IC2 — ELIMINANT DENSITY: closing the algebraic decomposition oracle
**Status:** COMPLETE · **Verdict: DEAD** (for the resultant/eliminant route) · **Date:** 2026-09-17
**Data:** `ecdlp/data/eliminant.json` · **Code:** `ecdlp/py/eliminant.py`

K1 killed the *combinatorial* decomposition oracle. The other family is *algebraic*:
solve `S_{k+1}(x_1..x_k, x_R) = 0` with `x_i ∈ S` by elimination. Over `F_{q^n}` Weil
descent makes this cheap; over `F_p` there is no descent, so everything depends on
whether some structured `S` makes the eliminant small.

- `k = 2`: the eliminant is `E(x_1) = ∏_{s∈S} S_3(x_1, s, x_R)`, degree `2|S|`,
  computable by a product tree in `Õ(|S|)` — **for any `S`, structured or not**. That
  already ties brute force, so `k = 2` settles nothing (and `k = 2` index calculus is
  `Θ(n)` regardless).
- `k = 3`: the eliminant is `E(x_1,x_2) = ∏_{s∈S} S_4(x_1, x_2, s, x_R)`, of bidegree
  `(4|S|, 4|S|)`. Dense, that is `~16|S|²` coefficients — already brute force. **An
  algebraic win requires the eliminant to be sparse.**

Measured directly: build `E` by product tree over `S = μ_m` (the canonical
intermediate-size algebraic subset of `F_p`, and the one with the richest structure)
and over a random control set of the same size, then count nonzero coefficients.

| curve | m | eliminant shape | nnz for `μ_m` | density | nnz for random `S` | density |
|---|---|---|---|---|---|---|
| c14_0 | 16 | 65×65 | 4223 / 4225 | 1.000 | 4223 | 1.000 |
| c14_0 | 24 | 97×97 | 9409 / 9409 | **1.000** | 9409 | 1.000 |
| c14_0 | 36 | 145×145 | 21023 / 21025 | 1.000 | 21021 | 1.000 |
| c14_0 | 38 | 153×153 | 23399 / 23409 | 1.000 | 23405 | 1.000 |
| c20_0 | 27 | 109×109 | 11881 / 11881 | **1.000** | 11881 | 1.000 |

Fitted over 17 (curve, m) pairs:

```
S = μ_m    :  nnz ~ m^1.956   (r² = 1.0000)
S = random :  nnz ~ m^1.956   (r² = 1.0000)
```

**The eliminant is completely dense, and the multiplicative subgroup is
indistinguishable from a random set.** At `k = 3` the counting target is `θ ≤ k−3 = 0`
— the oracle would have to be polylogarithmic — while merely *writing down* the
eliminant costs `Θ(m²)`. The richest algebraic structure `F_p` offers buys exactly
nothing.

**Scope, stated honestly** `[SPECULATION vs ESTABLISHED boundary]`: this closes the
resultant/eliminant route with a measurement. It does **not** prove that no algebraic
oracle exists — a Gröbner strategy that never materialises the eliminant is not
excluded by this data. What it does establish is that the one concrete mechanism by
which algebraic structure could have helped — sparsity induced by the structure of `S`
— is absent, and absent to three decimal places.

---

## IC1 — INDEX CALCULUS, BUILT AND MEASURED
**Status:** COMPLETE · **Verdict: DEAD** · **Date:** 2026-09-17
**Data:** `ecdlp/data/ic_sweep_k*.json`, `ic_comp_k*.json`, `ecdlp/results/ic_projection.json`
**Code:** `ecdlp/csrc/indexcalc.c`, `ecdlp/csrc/wiedemann.c`, `ecdlp/py/{ic_sweep,ic_recomp,project,figure}.py`

Rather than argue about index calculus over prime fields, it is **built and run**: a
complete working attack that solves real ECDLP instances on the toy curves, with every
cost counted — factor base, sum table, relation search, and linear algebra.

- Factor base: the `m` points of smallest x-coordinate (public, canonical).
- Decomposition: a precomputed table of all `j`-fold sums, then enumeration of the
  remaining `k−j` with signs, working in `E/{±1}` so the table covers a sum and its
  negative at once.
- Linear algebra: **sparse Wiedemann** over `F_n`, measured at `26·C²` field operations
  with a stable constant. Dense elimination is `Θ(C³)` and would have dominated the very
  scaling being measured — using it would have produced a meaningless number.
- Correctness: every instance solved and verified against the sealed target; `crosscheck.py`
  confirms rho and index calculus agree on 24/24 hidden targets.

**Measured, 3 hidden targets per point, `m` swept at every size:**

| config | sizes | fitted total exponent | r² | asymptote |
|---|---|---|---|---|
| `k=2, j=1` | 20–28 (5) | **0.9770** | 0.9991 | 1 |
| `k=3, j=2` | 20–36 (9) | **0.6047** | 0.9977 | 2/3 |
| `k=6, j=3` | 20–36 (9) | **0.4645** | 0.9944 | 3/5 |

**The `k=6` number is below 0.5 and is NOT a win.** It is the `m²` linear-algebra term,
which has the *smallest* asymptotic exponent of the three (`2/(2j−1) = 0.4` versus `0.6`)
and still dominates at toy sizes. Three independent checks establish this:

1. **Component shares** (measured separately, not derived). For `k=6`, linear algebra
   falls from **75.0% → 20.8%** of total cost between 20 and 36 bits while the 3-sum table
   rises from **7.8% → 40.6%**. The `n^0.6` terms are visibly taking over.
2. **Per-component exponents** match the model: table `n^0.6214` (model 0.600), relations
   `n^0.5309` (0.600), linear algebra `n^0.3518` (0.400).
3. **The local exponent rises through 0.5 inside the measured range.** Fitting the first
   four sizes vs the last four:

| config | first 4 sizes | last 4 sizes | asymptote |
|---|---|---|---|
| `k=3, j=2` | 0.5300 | **0.6444** | 0.6667 |
| `k=6, j=3` | 0.3858 | **0.5302** | 0.6000 |

**256-bit projections** from the three-term model `A·m^j + B·n·m^{1−j} + C·m²`, with `A`,
`B`, `C` fitted to their own component measurements (well conditioned, 15–17% mean
relative error) and then minimised over `m`:

| config | fitted A / B / C | effective exponent 2^128→2^256 | at 256 bits | vs rho |
|---|---|---|---|---|
| `k=2, j=1` | 1661 / 1.90 / 0 | 1.0000 | `2^256.9` | 2^129.9 worse |
| `k=3, j=2` | 1.02 / 1.65 / 31.4 | 0.6667 | `2^173.7` | 2^46.7 worse |
| `k=6, j=3` | 0.355 / 20.1 / 66.6 | 0.6000 | `2^156.6` | **2^29.5 worse** |

(theory: `A ~ 1/j!`, `C ~ 26` — both recovered within a factor of 2, which is the check
that the fitted model is the physical one.)

The projections `2^257 → 2^174 → 2^157` approach rho's `2^127.8` **from above** exactly as
`n^{j/(2j−1)} → n^{1/2}` predicts, and never cross. Larger `j` also demands
`n^{j/(2j−1)}` *memory*, where rho needs essentially none.

---

## SAT1 — SAT/SMT SCALING
**Status:** COMPLETE · **Verdict: DEAD** · **Date:** 2026-09-17
**Data:** `ecdlp/data/sat_scaling.json` · **Code:** `ecdlp/py/sat_scaling.py`

Non-generic structure: the bit-level circuit representation of `F_p` arithmetic, which a
generic-group algorithm cannot see. The encoding is deliberately the friendliest honest
one — Z3 bitvectors, all multiples `2^i·G` **precomputed as constants**, an affine
addition chain with division replaced by the multiplication constraint
`λ·(x₂−x₁) = y₂−y₁`, so the solver is handed the whole algebraic structure and only has
to find `bits` boolean unknowns. Toy curves of 8–19 bits were generated for this
(`ecdlp/data/curves_small.json`), all with the same prime-order, `j = 0` structure.

| bits | median seconds | correct |
|---|---|---|
| 8 | 12.2 | 3/3 |
| 9 | 87.6 | 3/3 |
| 10 | 260.5 | 3/3 |
| 11 | hit the 420 s wall | — |

```
fit:  log2(seconds) = 2.2059 · bits − 13.823
```

**Slope 2.21 bits⁻¹**, against 1.0 for brute force and 0.5 for rho. Projection to 256
bits: `2^550.9` seconds. A bit-level solver is worse than brute force by more than a
factor of two *in the exponent*; giving it the full algebraic structure does not help.
The ablation arms (special-prime shape, `λ` constraint, ladder encoding) are queued in
`IDEA_QUEUE.md` as the part that could still surprise — a slope *shift* would be a real,
if small, non-generic effect.

---

## G1 — MU6-GRADED-SEMAEV: does the `j=0` symmetry lower the algebraic complexity?
**Status:** COMPLETE · **Verdict: DEAD as an exponent-level idea** · **Date:** 2026-09-17
**Data:** `ecdlp/data/mu6_graded.json` · **Code:** `ecdlp/py/mu6_graded.py`

`IDEA_QUEUE.md`'s top algebraic item, and the one quantity IC2 did not cover. The order-3
automorphism `(x,y) ↦ (βx, y) = λ(x,y)` means `P_1 + … + P_k = O ⟹ λP_1 + … + λP_k = O`,
so the solution set of `S_k` is stable under the **diagonal** action `x_i ↦ βx_i`.

**G1 — the grading is real.** Every monomial of `S_k` lies in a single residue class of
total degree mod 3:

| | monomials | total degree mod 3 | weight |
|---|---|---|---|
| `S_3` | 9 | all ≡ 1 | `S_3(βx₁,βx₂,βx₃) = β·S_3` |
| `S_4` | 191 | all ≡ 0 | `S_4(βx₁,…,βx₄) = S_4` |

**G2 — but the grading does not survive fixing the target.** IC2 found the eliminant
`E(x₁,x₂) = ∏_{s∈S} S_4(x₁,x₂,s,x_R)` completely dense. If the `μ_3` action produced
sparsity, `E`'s nonzero coefficients would concentrate on one residue class of
`(e₁+e₂) mod 3` — density `1/3`, max class share ≈ 1.000. Measured over 14 `(curve, m)`
pairs with `S = μ_m`, `3 | m` (so `S` is genuinely `μ_3`-stable):

| curve | m | nnz | by `(e₁+e₂) mod 3` | max share | random `S` max share |
|---|---|---|---|---|---|
| c14_0 | 24 | 9409/9409 | 3137 / 3136 / 3136 | **0.333** | 0.333 |
| c14_0 | 36 | 21025/21025 | 7009 / 7008 / 7008 | **0.333** | 0.333 |
| c20_0 | 27 | 11881/11881 | 3961 / 3960 / 3960 | **0.333** | 0.333 |

**Exactly equal thirds, identical to a random set.** The mechanism is clear once stated:
the action is *diagonal on all variables including `x_R`*, so it relates decompositions of
`R` to decompositions of `λR` — not to other decompositions of the same `R`. Fixing the
target breaks the grading, and with it any hope of graded sparsity.

**G3 — what the symmetry actually buys.** Working in `E/⟨λ, −1⟩` shrinks the factor base
by exactly 6 and the reduced space to `(n−1)/6` (confirmed by orbit-representative counts
at 24/28/32 bits). In the cost model `A·m^j + B·n·m^{1−j} + C·m²`, replacing `m` by `m/6`
rescales the terms by `6^j` and `6^{j−1}`: **a constant factor. The exponent
`j/(2j−1)` is unchanged.**

This is the same `√6` that rho already gets, and for the same reason. The `j=0` CM
structure — secp256k1's most distinctive feature — is worth a constant, at every level of
the attack, and nothing more.
