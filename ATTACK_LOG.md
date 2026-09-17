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
