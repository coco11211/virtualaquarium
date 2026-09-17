# IDEA_QUEUE.md — ranked attack queue

Pull the next idea from the top. Re-rank after every verdict.
Ranking criterion: **information per unit cost** first, then genuine non-genericity, then
probability of an asymptotic win, then cheapness.

Tags: `[E]` established · `[H]` heuristic · `[S]` speculation.

---

## The accounting that drives the ranking

Index calculus with factor base `F`, `|F| = m`, `k`-term decompositions `R = ±P₁ ± … ± Pₖ`:

- `Pr[random R decomposes] ≈ (2m)^k / (k!·n)`  `[E]` (counting)
- relations needed ≈ `m`; decomposition-oracle cost `D`
- relation cost ≈ `m · k!·n/(2m)^k · D = Θ(n·D/m^{k-1})`
- sparse linear algebra ≈ `Θ(m²)`  `[E]`
- balance ⇒ `m = (nD)^{1/(k+1)}`, **total cost `(nD)^{2/(k+1)}`**  `[E]`

With a *perfect* oracle `D = polylog`: `k=3 → n^{1/2}` (ties rho), `k=4 → n^{2/5}`,
`k=5 → n^{1/3}`. **So a win needs `k ≥ 4` AND `D` far below brute force.**
Brute force is `D ≈ m^{k-1}`, which makes the total `Θ(n)` — worse than rho. `[E]`

Over `F_{q^n}` Gaudry/Diem achieve small `D` because Weil descent turns the single Semaev
equation into `n` equations over `F_q`, making the system square and Gröbner-solvable.
**`F_p` has no proper subfield and no `F_q`-linear subspace, so there is no descent. `D` is
the entire game.** Every index-calculus idea below is really a proposal for a substitute
structure that shrinks `D`. Rank accordingly.

---

## Queue

### 1. `IC-SEMAEV-D` — measure the decomposition-oracle cost `D` for structured factor bases over `F_p`
**Surface:** 1+2. **Non-generic structure:** the x-coordinate lives in `F_p`; Semaev's `S_{k+1}`
is an explicit polynomial relation among x-coordinates — pure coordinate structure, invisible
to a generic-group algorithm.
**Hypothesis `[S]`:** for some algebraically-structured `S ⊂ F_p` (multiplicative subgroup
`μ_m`; roots of a sparse polynomial; an interval), the decomposition problem
`∃ x_i ∈ S : S_{k+1}(x₁,…,x_k,x_R)=0` is solvable in `o(m^{k-1})`.
**Prior work:** Semaev 2004 (summation polynomials); Gaudry 2009 and Diem 2011 (index calculus
over extension fields) — both need `F_{q^n}`, `n>1`. `SEARCH: "summation polynomials prime
field index calculus" "Semaev prime field obstruction"`.
**What is different:** we are not claiming a descent; we are *measuring* whether specific
algebraic factor bases admit sub-brute-force elimination (product-tree resultants for `μ_m`,
structured Gröbner for sparse-root sets).
**First experiment:** implement `S₃, S₄, S₅` for `y²=x³+7`; for `S = μ_m` compute
`Res_{x_k}(S_{k+1}, x_k^m − 1)` by product tree in `Õ(m)`; measure wall-clock `D` vs `m` for
`k=2,3,4` on 20–48 bit curves; fit the exponent of `D` in `m`.
**Kill:** fitted `D ∝ m^{k-1±0.1}` for every `S` tried ⇒ that `S` is DEAD.
**Cost:** hours–days.

### 2. `SEMAEV-COPPERSMITH` — quantify the small-root threshold for interval factor bases
**Surface:** 2+8. **Non-generic structure:** integer-size (archimedean) structure of
representatives in `[0,p)` — meaningless in a generic group.
**Hypothesis `[S]`:** taking `S = [0,B]` turns decomposition into a multivariate modular
small-root problem; Coppersmith/LLL might solve it for `B` large enough to be a useful
factor base.
**Prior work `[E]`:** Coppersmith 1996; Jochemsz–May 2006 (multivariate strategy).
Semaev `S_m` has degree `2^{m−2}` in each variable — very high, so the small-root bound is
brutal. `SEARCH: "Coppersmith summation polynomial elliptic curve small roots"`.
**What is different:** nobody seems to have published the *measured* threshold; we produce the
number instead of asserting it.
**First experiment:** for `k=2,3`, build the Jochemsz–May lattice for `S_{k+1} ≡ 0 (mod p)`
with root bounds `B`; measure the largest `B` for which LLL recovers a planted root, on
24–48 bit `p`; compare with the `B = m ≈ n^{1/(k+1)}` that index calculus needs.
**Kill:** measured achievable `B ≤ p^{0.1}` while `n^{1/(k+1)} ≥ p^{0.2}` ⇒ DEAD, with the
gap quantified in exponent units.
**Cost:** days.

### 3. `SPECIAL-PRIME-TADIC` — is `p = 2²⁵⁶ − 2³² − 977` a descent substitute?
**Surface:** 4. **Non-generic structure:** `p = f(t)` at `t = 2³²` for `f(T)=T⁸−T−977`, so
`F_p` is a quotient of `Z[T]/(f)`; every element has a base-`2³²` digit vector, and reduction
is the linear rule `2²⁵⁶ ≡ 2³² + 977`. This is a rank-8 `Z`-module structure with small
generators — the closest thing `F_p` has to a vector space over a subfield.
**Hypothesis `[S]`:** `S_D = {x : all t-adic digits < D}` behaves as a "linear" factor base;
substituting digit variables into `S_{k+1}` gives a system in `8k` small unknowns over `Z`
with carries, attackable by lattice reduction.
**Prior work `[E]`:** SNFS works for `F_p^*` precisely because of this structure; the elliptic
analogue has never been made to work because `E(F_p)` has no height-controlled lift.
**What is different:** we bypass lifting entirely — the structure is used for the factor base,
not for a lift.
**Blocker:** needs toy curves over *special-shape* primes. **Build those first.**
**First experiment:** generate `p = t^k − t − c`, `t = 2^s`, prime, `p ≡ 1 mod 3`,
`#E(y²=x³+7)` prime, at 24–60 bits; then measure decomposition counts and `D` for `S_D`.
**Kill:** decomposition counts for `S_D` match a random set of the same size AND `D` shows no
improvement over brute force ⇒ DEAD.
**Cost:** days.

### 4. `NULL-BATTERY` — measure representation-level non-randomness (guards against self-deception)
**Surface:** 7+8. **Non-generic structure:** the bit/field representation of `x(kP)`.
**Hypothesis `[S]`:** some cheap statistic of `x(kP)` correlates with `k`. Expected result:
exactly none. Value is in mapping the space and in having a calibrated null.
**Tests:** (a) empirical mutual information between low/high bits of `k` and bits of `x(kP)`;
(b) does `x(kP)` land in small multiplicative subgroups of `F_p^*` more often than random?
(c) Legendre-symbol sequence `χ(x(kP))` vs a random binary source; (d) t-adic digit bias on
special-shape primes; (e) is `x((k+1)P) − x(kP)` distributed differently from random?
**Kill:** all statistics within the calibrated null band ⇒ this class is DEAD (and we get a
calibration we can reuse to test future "surprises").
**Cost:** hours.

### 5. `RHO-LSH` — sub-√n collision search via coordinate-metric nearest neighbours
**Surface:** 8. **Non-generic structure:** the coordinate map gives a metric on points;
generic groups have none.
**Hypothesis `[S]`:** if some metric `d` on `E(F_p)` satisfied `d(P+R, Q+R) ≈ d(P,Q)`
(approximate translation invariance), a locality-sensitive hash would let us detect *near*
collisions and amortise, beating the birthday bound.
**Why it should fail `[H]`:** the group law is an algebraic map of degree 2 in the
coordinates; it is provably far from an isometry for any natural metric.
**First experiment:** directly measure translation-distortion: for random `P,Q,R`, the
distribution of `d(P+R,Q+R)` given `d(P,Q)`, for `d` = |Δx|, Hamming on bits, and t-adic
digit distance. A non-trivial correlation would be a genuine finding.
**Kill:** measured mutual information between `d(P,Q)` and `d(P+R,Q+R)` indistinguishable
from zero at 5σ ⇒ DEAD.
**Cost:** hours.

### 6. `CM-LATTICE` — is `E(F_p) ≅ Z[ω]/(π)` exploitable beyond GLV?
**Surface:** 3. **Non-generic structure:** `End(E) = Z[ω]`; Frobenius `π` has `N(π)=p`.
**Hypothesis `[S]`:** representing scalars in `Z[ω]` gives a rank-2 lattice picture in which
the DLP becomes a closest-vector-style problem.
**Why it probably fails `[E]`:** GLV already gives `k = k₁ + k₂λ` with `k₁,k₂ ≈ √n`; searching
that box is `n` work and BSGS on it is `√n` — exactly rho. A change of basis cannot beat
Shoup unless it supplies an oracle linking lattice distance to group data, which it does not.
**What would have to be true:** some efficiently computable function of `Q` alone that
constrains `(k₁,k₂)` to a sublattice or a short-vector region.
**First experiment:** exhaustively test, on 20–28 bit curves, whether any of a battery of
cheap functionals of `Q` correlates with `k₁` or `k₂` (reuse the NULL-BATTERY machinery).
**Kill:** no correlation ⇒ DEAD.
**Cost:** hours.

### 7. `COVER-GENUS` — close the cover/correspondence surface with numbers
**Surface:** 6. **Claim to verify `[E]`:** if `C → E` is a degree-`d` cover over `F_p` with
`g(C)=g`, then `#Jac(C)(F_p) ≈ p^g`, and Gaudry–Thomé–Thériault–Diem index calculus costs
`Õ(p^{2−2/g})` for `g ≥ 3`, which exceeds `√p` for every `g ≥ 3`. Descent helps only when a
*smaller field* exists to descend to; `F_p` has none.
**First experiment:** produce the table of `p^{2−2/g}` vs `√p` for `g = 2…10` and state the
break-even; verify the Jacobian-size claim on toy covers.
**Kill:** table confirms ⇒ surface CLOSED with a citable number.
**Cost:** hours.

### 8. `SAT-SCALING` — measure the real SAT/SMT exponent on ECDLP
**Surface:** 7. **Non-generic structure:** bit-level circuit representation of `F_p` arithmetic.
**Hypothesis `[S]`:** the exponent is ~1 (brute force) or worse. Measure it.
**First experiment:** encode `kG = Q` as CNF for 12–28 bit curves (double-and-add circuit),
run a modern SAT solver, fit `log(time)` vs bits; also test whether adding the endomorphism
constraint or a special-shape prime changes the slope.
**Kill:** slope ≥ 0.5 bits⁻¹ in `log₂ time` (i.e. ≥ `√n`) with no improvement from structure ⇒ DEAD.
**Cost:** hours–days.

### 9. `XEDNI-CM` — Silverman's xedni, re-run with `j=0` CM lifts
**Surface:** 5. **Non-generic structure:** lifting to characteristic 0.
**Prior work `[E]`:** Silverman 1998 (xedni calculus); Jacobson–Koblitz–Menezes–Stein–Teske
1999/2000 analysis showing it fails — lifted points are independent with probability ≈ 1 and
the canonical heights are too large.
**What is different `[S]`:** restrict to CM curves `y²=x³+b` over `Q`, where Mordell–Weil
ranks and height pairings are much better understood, and ask whether the CM structure raises
the probability of a low-height lift. Expected: no, because the obstruction is the
Birch–Swinnerton-Dyer-scale size of generators, not the curve family.
**First experiment:** for toy `p`, lift `r` points to `y²=x³+b` over `Q` by Silverman's recipe
and measure the empirical distribution of canonical heights and the rank of the lifted points
vs `r`; compare with the JKMST prediction.
**Kill:** measured rank = `r` (independent) with the predicted probability ⇒ DEAD, quantified.
**Cost:** days.

### 10. `ANOMALOUS-ESCAPE` — is there any variant of the p-adic elliptic log for `#E ≠ p`?
**Surface:** 5+6. **Established `[E]`:** Smart / Satoh–Araki / Semaev, 1997–1999: for
anomalous curves (`#E = p`) the formal-group logarithm on `E(Q_p)` solves the DLP in
polynomial time. secp256k1 is not anomalous.
**Precise obstruction to attack `[E]`:** the kernel of `E(Z/p²) → E(F_p)` is `p`-torsion;
multiplying by `#E` (coprime to `p`) lands in that kernel only when `p | #E`.
**First experiment:** implement the anomalous attack, verify it on a purpose-built anomalous
toy curve, then measure precisely what breaks as `#E` moves away from `p`. Produces a clean
boundary and a reusable p-adic toolkit.
**Kill:** no variant recovers information once `gcd(#E, p) = 1` ⇒ DEAD, with the mechanism shown.
**Cost:** days.

### 11. `ML-FACTORBASE` — machine-search the factor base
**Surface:** 7+1. Search (evolutionary / SAT-guided) over parametrised families of `S` for one
that maximises decomposition probability per unit of `D`. Only meaningful once `IC-SEMAEV-D`
gives a measurement harness. **Kill:** best found `S` no better than random of equal size.

### 12. `LATTES-DYNAMICS` — arithmetic dynamics of `x(kP)` on `P¹`
**Surface:** 8. Multiplication-by-`m` on `E` descends to a Lattès map on `P¹`. Test whether
iterate factorisation patterns, periodic-point structure, or the Galois theory of iterates
gives any handle on `x(kP)=x(Q)`. **Kill:** no measurable structure beyond the known degree-`m²`
rational map ⇒ DEAD.

### 13. `J0-SYMMETRY-GROEBNER` — symmetrise Semaev systems under the order-6 automorphism group
**Surface:** 2+3. The `j=0` automorphisms act on `S_{k+1}`; quotienting by the invariants may
lower the Gröbner degree of regularity. **Kill:** measured degree of regularity unchanged.

### 14. `ISOGENY-SCAN` — small-degree isogenies for `D = −3`
**Surface:** 6. Isogenies preserve the group order, so no direct win `[E]`; scan anyway for any
`ℓ`-isogeny whose kernel structure leaks information, and to have the modular machinery.
**Kill:** order preserved and no side channel ⇒ surface CLOSED.

### 15. `HNP-FREE-BITS` — is any partial information about `k` free?
**Surface:** 8. Hidden-number-problem attacks are devastating *given* leaked bits. Measure
whether any function of `Q` alone predicts any bit of `k` above chance. **Kill:** no ⇒ DEAD.

### 16. `MULT-SUBGROUP-BIAS` — does `x(kP)` favour small multiplicative subgroups?
**Surface:** 1+4. Directly tests whether `μ_m` is a *statistically* better factor base than a
random set of the same size. Cheap. **Kill:** counts match random ⇒ DEAD.

### 17. `SNFS-ANALOGUE` — characterise exactly what an elliptic SNFS would need
**Surface:** 4+5. Write down the precise missing object (a lift of `E(F_p)` to a
finitely-generated group with height control and small generators), then test the weakest
sub-claim that could make it exist. **Kill:** sub-claim measurably false ⇒ surface CLOSED.

### 18. `ENDO-FACTORBASE` — combine CM with index calculus
**Surface:** 1+3. Use the `λ`-action to fold the factor base by 6 and to add relations
`λP = βx` for free. Reduces `m` by a constant, not the exponent — but it also adds
*equations*, which is what a descent substitute needs. Measure the effect on `D`.
**Kill:** `D` exponent unchanged ⇒ DEAD as an exponent-level idea.

---
*Seeded 2026-09-17. A parallel multi-agent literature/idea sweep is running; its output will be
merged and the queue re-ranked.*
