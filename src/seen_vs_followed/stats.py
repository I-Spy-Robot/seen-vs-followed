"""Small-sample statistics for 10-30 episodes per cell. Standard library only."""
from math import comb, sqrt


def wilson(k, n, z=1.96):
    """Wilson score interval (lo, hi) for k of n."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - m) / d), min(1.0, (c + m) / d))


def fisher_greater(a, n1, b, n2):
    """One-sided Fisher exact p-value: P(at least a of n1 | a+b successes among n1+n2)."""
    k_total = a + b
    tot = comb(n1 + n2, k_total)
    return sum(comb(n1, k) * comb(n2, k_total - k) for k in range(a, min(k_total, n1) + 1)) / tot


def _pmf(n, k, p):
    return comb(n, k) * p**k * (1 - p) ** (n - k)


def power(n, p_control, p_follow, alpha=0.05):
    """Chance that n episodes in a cell vs n in a control give one-sided Fisher p <= alpha, when the true rates are given."""
    pw = 0.0
    for a in range(n + 1):
        for b in range(n + 1):
            w = _pmf(n, a, p_follow) * _pmf(n, b, p_control)
            if w > 1e-12 and fisher_greater(a, n, b, n) <= alpha:
                pw += w
    return pw
