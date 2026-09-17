# Attacking the ECDLP on secp256k1 — a measured negative result

**Session date:** 2026-09-17 · **Branch:** `claude/secp256k1-dlog-attack-y3sc35`
**Everything here is reproducible from `ecdlp/`.** Raw data in `ecdlp/data/`, figures in
`ecdlp/results/`, per-idea verdicts in `ATTACK_LOG.md`, the ranked queue in `IDEA_QUEUE.md`.

---

## Headline

**No attack found. Nothing measured falls below the rho bar.** What this session produced
instead is a measurement apparatus and a set of quantitative closures: for each major
non-generic attack surface, a number saying how far it is from beating
`√(πn/12) ≈ 2^127.8`, obtained by building the attack and running it rather than by
argument.

Three of the results are sharper than I expected going in:

1. **`y² = x³ + 7` has no rational points at all.** secp256k1's own defining equation has
   `E(Q) = {O}` — rank 0, trivial torsion, `L(E,1) = 3.041… ≠ 0`, and a brute-force scan
   over `|a| ≤ 90000, c ≤ 300` finds nothing while the control `y² = x³ + 1` finds exactly
   its known 5 points. Every lifting-based attack on the natural lift begins with an
   **empty** factor base.

2. **There is no filtration on `E(F_p)` visible from the coordinates.** Wagner's k-tree
   would put index calculus at `n^{2/5}` — below rho — if the group admitted a chain of
   coordinate-testable predicates compatible with addition. Measured across 104 tests on
   11 curves, every predicate returns compatibility ratio `ρ = 1.00`, while the `Z_n`
   positive control returns `ρ = 2050` against a theoretical 2048.

3. **The algebraic decomposition oracle has no sparsity to exploit.** At `k = 3` the
   eliminant `∏_{s∈S} S_4(x_1,x_2,s,x_R)` is **completely dense** (density 1.000,
   `nnz ∝ m^1.956`, `r² = 1.0000`), and the multiplicative subgroup `μ_m` — the richest
   algebraic subset `F_p` offers — is indistinguishable from a random set.

4. **The lattice branch closes with a gap that grows the wrong way.** Box factor bases
   turn decomposition into a Coppersmith small-root problem. Relations exist only for
   `e ≥ 1/k`; lattices solve only for `e < 2(s+1)^k/(k(d+s)(d+s+1)^k)`. Measured
   `e* ≈ 0.12–0.14`, stable across 32/40/48 bits and saturating as the lattice dimension
   triples. The shortfall is 5.6× at `k=2`, **47.6× at `k=4`** — the first `k` that could
   win at all — and 2422× at `k=8`.

---

## Why the three surfaces fail for one shared reason

Index calculus works in `F_p^*` because the *representative carries the group structure*:
an integer's factorisation **is** its decomposition over the factor base, and factoring is
subexponential. A point's coordinates say nothing about its decomposition. That is a
structural claim, and this session's measurements are its empirical form:

- no feature of `x(kP)` depends on `k` (2028 χ² tests, 0 pass Bonferroni);
- no coordinate predicate is compatible with the group law (`ρ = 1.00` across the board);
- the sumset of a coordinate-structured set is indistinguishable from uniform (270 tests);
- integer smoothness of `x` does not propagate through addition (540669 pairs, `ρ = 1.03`);
- no map out of the group — including `log_g x(P)` into `F_p^*`, where the DLP is
  subexponential — respects addition even approximately.

---

## The bar, measured

`ecdlp/csrc/rho.c` — van Oorschot–Wiener parallel collision search, distinguished points,
batched inversions, deterministic fruitless-cycle escapes. 66 toy curves `y² = x³ + 7`
over `p ≡ 1 (mod 3)` with prime order `n ≡ 1 (mod 3)`, 20–62 bits, each carrying the same
`β`/`λ` endomorphism structure as secp256k1.

| mode | measured `C` in `ops = C√n` | theory | fitted exponent | r² |
|---|---|---|---|---|
| plain | 1.2485 | `√(π/2) = 1.2533` | 0.5051 | 0.9989 |
| negation | 0.9270 | `√(π/4) = 0.8862` | 0.4979 | 0.9983 |
| negation + endomorphism | 0.5518 | `√(π/12) = 0.5117` | 0.5072 | 0.9983 |

Projected to 256 bits: `2^128.8` measured, `2^127.8` theoretical.
**Every candidate had to beat a fitted exponent of 0.507 on measured total cost.**

---

## Discipline: three times my own statistics manufactured a discovery

Each was caught by the same rule — **every test ships with a control constructed to
satisfy the null** — and each is logged in `ATTACK_LOG.md` rather than quietly deleted.

| apparent result | what it really was | how it was caught |
|---|---|---|
| `z = −245` for multiplicative-subgroup factor bases | a 3-element set sampled **with replacement** 60000 times | exact enumeration; the null-rate control |
| `p = 4e-126` for group-law metric distortion | tie-degenerate rank binning of an integer metric | the control returned `p = 6e-126` |
| `p = 1.6e-7` for a transfer via `log_g x(kP)` at 20 bits | sampling a **deterministic table** with replacement inflates χ² by `N·dof/n` | a random bijection reproduced it (`p = 2.6e-10`), and the predicted excess matched at every size |

Two more in the lattice harness: PARI's `qflll` treats *columns* as the basis while its
matrix literal is row-major, so reading results row-wise returned vectors that were not
lattice elements; and scoring "two short vectors vanish at the root" is too weak, since
Coppersmith only works if elimination leaves a nonzero univariate polynomial.

A further near-miss: index calculus at `k=6` fits a **total** exponent below 0.5 on toy
curves. That is not a win — it is the `m²` linear-algebra term, which has the *smallest*
asymptotic exponent of the three cost terms and still dominates at these sizes. The
three-term model, fitted to the components and then optimised over `m`, projects `n^{3/5}`.
`ecdlp/py/ic_components.py` and `ecdlp/py/project.py` exist specifically to tell these
apart, and the component table prints which term dominates so the fitted exponent cannot
be read naively.

---

## What was built and run

| surface | what was built | measured result | verdict |
|---|---|---|---|
| baseline | `rho.c` — VW parallel collision search, 3 modes, fruitless-cycle escapes | `n^0.5072`, `C = 0.5518` vs theory 0.5117 | the bar |
| 1 · index calculus | **a complete working attack** (`indexcalc.c` + sparse Wiedemann), solving and verifying real instances | `k=2: n^0.977` · `k=3: n^0.605→2/3` · `k=6: n^0.465→3/5` | **DEAD** |
| 1 · factor bases | exact enumeration of `μ_m`, intervals, power residues, t-adic sets vs the curve's x-set | deviation `∝ m^{−0.589}`; sampling noise is `−0.5` | **DEAD** |
| 2 · Semaev | `S_3, S_4` derived and verified against real relations; eliminant density measured | density **1.000**, `nnz ∝ m^1.956` | **DEAD** |
| 2 · lattices | Coppersmith shift lattices on `S_3`, real LLL, planted roots, resultant-elimination scoring | `e* ≈ 0.13` vs `1/k` needed; shortfall 47.6× at `k=4` | **DEAD** |
| 3 · `j=0` / CM | automorphism-invariant predicates; cubic character; xedni on CM curves; `μ_3` grading of `S_3`, `S_4` | `ρ = 1.002`; 0/1080 dependent lifts; grading real but broken by fixing `x_R` — eliminant splits into exactly equal thirds | **DEAD** |
| 4 · the special prime | **toy curves over primes of secp256k1's exact `p = t⁸ − t − c` form** (24–56 bits) | t-adic digit sets: null hit rate, `ρ = 1.07` | **DEAD** |
| 5 · lifting | rank/height counts; xedni with height-pairing independence tests | `E(Q) = {O}`; 0/1080 dependencies | **DEAD** |
| 6 · transfer | quasi-homomorphism defect; 12-map machine search | defect uniform; only estimator bias found | **DEAD** |
| 7 · SAT/SMT | Z3 bitvector encoding, precomputed multiples, affine chain | **slope 2.21 bits⁻¹** → `2^551` seconds at 256 bits | **DEAD** |
| 8 · wildcards | leak battery, metric distortion, k-tree filtration, smooth points | all null against calibrated controls | **DEAD** |

**Figure:** `ecdlp/results/scaling.png` — measured cost vs rho, the transient analysis,
cost composition, 256-bit projections, and the SAT scaling.

---

## The central accounting

Index calculus with `|F| = m` and `k`-term decompositions:

- guess-and-check relation generation costs `Θ(n)` **in total, for every `m` and `k`** —
  each probe succeeds with probability `m/p` and `m` successes are needed. So a win
  requires a real **decomposition oracle**.
- with an oracle of cost `T = m^θ`: **a win needs `θ ≤ k−3`, while brute force is
  `θ = k−1`.** Any winning oracle must beat brute force by *two full exponent units*, at
  every `k`.

Three oracle families exist. All three are now measured:

| family | best `θ` | exponent | status |
|---|---|---|---|
| combinatorial (`j`-sum table + meet-in-the-middle) | `j` | `n^{j/(2j−1)}` → `1/2` **from above**, never below; and needs `n^{j/(2j−1)}` *memory* where rho needs none | measured: 2^257, 2^174, 2^157 at 256 bits for `j = 1,2,3` |
| Wagner k-tree | would give `n^{2/5}` — **a genuine win** | requires a filtration of coordinate-testable predicates compatible with `+` | measured: **no such predicate exists** (`ρ = 1.00`; control `ρ = 2050`) |
| algebraic (eliminant) | `k−1` | `Θ(n)` | measured: **eliminant density 1.000** |

The `j = 1,2,3` projections — `2^257 → 2^174 → 2^157` — approach rho's `2^127.8` from
above exactly as `n^{j/(2j−1)} → n^{1/2}` predicts, and never cross it.

---

## Reproducing

```bash
cd ecdlp
gp -q tools/gen_curves.gp > data/curves_raw.json     # 66 toy curves
gp -q tools/gen_special.gp > data/curves_special.json # secp256k1-shaped primes
gcc -O3 -march=native -fPIC -shared -o lib/librho.so csrc/rho.c
gcc -O3 -march=native -fPIC -shared -o lib/libic.so  csrc/indexcalc.c csrc/wiedemann.c
python3 py/test_core.py        # arithmetic, targets, leak audit, rho correctness
python3 py/crosscheck.py       # rho and index calculus must agree on hidden targets
python3 py/bench_rho.py small  # the bar
python3 py/null_battery2.py    # leak / factor-base / metric tests
python3 py/ktree.py all        # the filtration test, with the Z_n positive control
python3 py/lift_gap.py all     # rank counts and xedni independence
python3 py/hom_search.py       # transfer search, with the random-table control
python3 py/eliminant.py        # eliminant density
python3 py/ic_sweep.py all     # the index calculus scaling sweep
python3 py/ic_recomp.py 32 && python3 py/ic_recomp.py 63
python3 py/project.py && python3 py/figure.py
```

Environment: Python 3.11, PARI/GP 2.15.4, numpy, sympy, gmpy2, z3-solver, gcc 13.
No Sage, no Magma.

---

## Integrity of the measurements

- **The solver never sees the scalar.** `Target` name-mangles the secret; solvers receive
  `Target.public()`. Both C entry points were audited to carry only public parameters:
  `rho_solve(p, nn, b_std, Gx, Gy, Qx, Qy, beta_std, lambda_std, mode, dbits, nwalk,
  rparts, seed, maxsteps, logtab, out)` and `index_calculus(p, nn, b_std, Gx, Gy, Qx, Qy,
  m, k, j, seed, max_targets, k_out, st)`.
- **Runtime decoy test**: a solver that secretly read the scalar would return a decoy
  substituted after `Q` was computed. It does not.
- **Cross-validation**: rho and index calculus were run on the same hidden targets and
  agree on **24/24**, each verifying against the sealed target.
- **Sanity**: the answer to target 0 must fail to verify against target 1. It does.
- **Full cost accounting**: factor base + sum table + relation search + linear algebra,
  never just the fast phase.
- **Many targets per size**, seeded and logged; 30 per size for the rho baseline.

---

## Honest limits of this work

- Toy curves reach 62 bits for rho and 36 bits for index calculus. Projections to 256 bits
  come from fitted models, not measurements, and are labelled as such throughout.
- IC2 closes the **resultant/eliminant** route by measurement. It does *not* prove that no
  algebraic oracle exists — a Gröbner strategy that never materialises the eliminant is
  not excluded by this data. Measuring the `μ₆`-symmetrised solving degree is the top
  remaining algebraic item in `IDEA_QUEUE.md`.
- K1 tests predicates from a finite battery plus a general sumset-distinguishability test.
  The latter is the stronger statement — if the sumset of a structured set is
  indistinguishable from uniform, no predicate can satisfy the filtration condition — but
  it is a statistical test at finite sample size, not a proof.
- The SAT measurement uses one encoding family (Z3 bitvectors, precomputed multiples). The
  ablation arms (special-prime shape, `λ` constraint, ladder encoding) are queued, not run.
- C1 measures the standard triangular shift lattice. A cleverer Jochemsz–May shift set
  could raise `e*` somewhat; it cannot plausibly raise it by the 47.6× needed at `k = 4`,
  but that is an extrapolation from the closed form, not a measurement.
- A parallel multi-agent sweep (71 agents) produced 47 ideas and its own experiments.
  **Only its rank-1 claim was independently re-derived and re-measured here** (as C1);
  its other closures are recorded as reported, not verified.
- Nothing here bears on quantum algorithms, on implementation faults, or on the security
  of any deployed system. **No real key or address was targeted at any point**; every
  instance was generated in this repository from a seeded RNG.

---

## Bottom line

secp256k1's discrete logarithm problem survived every attack in this program, and the
failures are quantitative rather than vague: the winning route would need a decomposition
oracle two exponent units better than brute force, and the three known oracle families
miss by 2^29.5, by the non-existence of any coordinate-visible filtration, and by an
eliminant that is dense to three decimal places. The `j = 0` CM structure, which is
secp256k1's most distinctive feature, buys nothing beyond the known `√6` rho speedup, and
its own defining equation `y² = x³ + 7` has no rational points at all.

**No disclosure is warranted. Nothing here should change anyone's threat model.**
