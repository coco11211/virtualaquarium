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
