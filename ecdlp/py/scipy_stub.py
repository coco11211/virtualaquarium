"""Minimal chi-square survival function (regularised upper incomplete gamma),
so the battery does not depend on scipy."""
import math

def _gammainc_upper_reg(s, x):
    if x < 0 or s <= 0:
        return float("nan")
    if x == 0:
        return 1.0
    if x < s + 1:
        # lower series
        term = 1.0 / s
        total = term
        n = 1
        while n < 100000:
            term *= x / (s + n)
            total += term
            if abs(term) < abs(total) * 1e-16:
                break
            n += 1
        low = total * math.exp(-x + s * math.log(x) - math.lgamma(s))
        return 1.0 - low
    # continued fraction for the upper part (Lentz)
    tiny = 1e-300
    b = x + 1 - s
    c = 1 / tiny
    d = 1 / b if b != 0 else 1 / tiny
    h = d
    for i in range(1, 100000):
        an = -i * (i - s)
        b += 2
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1 / d
        de = d * c
        h *= de
        if abs(de - 1) < 1e-16:
            break
    return h * math.exp(-x + s * math.log(x) - math.lgamma(s))

def chi2_sf(x, k):
    if k <= 0:
        return 1.0
    return max(0.0, min(1.0, _gammainc_upper_reg(k / 2.0, x / 2.0)))

if __name__ == "__main__":
    for x, k, want in [(0.0, 1, 1.0), (3.841, 1, 0.05), (1.0, 1, 0.3173),
                       (11.07, 5, 0.05), (18.307, 10, 0.05), (100.0, 10, 2.3e-17)]:
        print(f"chi2_sf({x},{k}) = {chi2_sf(x,k):.6g}  (expect ~{want})")
