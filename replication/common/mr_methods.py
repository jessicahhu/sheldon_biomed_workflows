"""Shared summary-data MR estimators and harmonisation used by every replication.

All functions take numpy arrays: bx = SNP-exposure effects, by = SNP-outcome log-ORs
(already aligned to the exposure-increasing allele), sy = SE of by.
"""
import numpy as np
from scipy import stats

COMP = {"A": "T", "T": "A", "C": "G", "G": "C"}
_rng = np.random.default_rng(2015)


def ivw(bx, by, sy, random=False):
    """First-order IVW (Burgess 2013). random=True gives multiplicative random effects."""
    w = bx**2 / sy**2
    b = np.sum(bx * by / sy**2) / np.sum(w)
    se = 1 / np.sqrt(np.sum(w))
    q = np.sum(w * (by / bx - b) ** 2)
    df = len(bx) - 1
    if random and df > 0:
        se *= np.sqrt(max(1.0, q / df))
    return b, se, 2 * stats.norm.sf(abs(b / se)), q, df


def egger(bx, by, sy):
    s = np.sign(bx); bx, by = np.abs(bx), by * s
    X = np.column_stack([np.ones_like(bx), bx]); W = np.diag(1 / sy**2)
    XtWX = X.T @ W @ X; coef = np.linalg.solve(XtWX, X.T @ W @ by)
    df = len(bx) - 2
    sigma2 = max(1.0, ((by - X @ coef) ** 2 / sy**2).sum() / df)
    se = np.sqrt(np.diag(np.linalg.inv(XtWX)) * sigma2)
    p = 2 * stats.t.sf(np.abs(coef / se), df)
    return {"intercept": coef[0], "int_se": se[0], "int_p": p[0],
            "slope": coef[1], "slope_se": se[1], "slope_p": p[1]}


def _wm_point(ratio, w):
    o = np.argsort(ratio); r, w = ratio[o], w[o] / w.sum()
    cum = np.cumsum(w) - 0.5 * w
    i = np.searchsorted(cum, 0.5)
    if i == 0:
        return r[0]
    if i == len(r):
        return r[-1]
    return r[i - 1] + (r[i] - r[i - 1]) * (0.5 - cum[i - 1]) / (cum[i] - cum[i - 1])


def weighted_median(bx, by, sy, nboot=2000):
    w = (bx / sy) ** 2
    est = _wm_point(by / bx, w)
    se = np.std([_wm_point(_rng.normal(by, sy) / bx, w) for _ in range(nboot)], ddof=1)
    return est, se, 2 * stats.norm.sf(abs(est / se))


def max_likelihood(bx, sx, by, sy):
    """Two-sample ML estimator (Burgess 2013; TwoSampleMR mr_two_sample_ml), accounting for SE of bx.
    Profiles out the true SNP-exposure effects; SE from the observed information (no heterogeneity inflation)."""
    from scipy import optimize
    nll = lambda b: 0.5 * np.sum((by - b * bx) ** 2 / (sy**2 + b**2 * sx**2))
    b0 = ivw(bx, by, sy)[0]
    b = optimize.minimize_scalar(nll, bracket=(b0 - 1, b0, b0 + 1)).x
    h = 1e-4 * max(1.0, abs(b))
    d2 = (nll(b + h) - 2 * nll(b) + nll(b - h)) / h**2
    se = 1 / np.sqrt(d2)
    return b, se, 2 * stats.norm.sf(abs(b / se))


def se_from_p(beta, p):
    return np.abs(beta) / stats.norm.isf(np.asarray(p) / 2)


def se_from_ci(lo, hi):
    return (np.log(hi) - np.log(lo)) / (2 * 1.959964)


def harmonise(ea, oa, eaf, beta, long_allele, ref_long_freq=None):
    """Return (sign, note). sign=+1/-1 aligns beta to long_allele; None if unresolved.
    Palindromic SNPs are resolved by allele frequency against ref_long_freq (must be < 0.42 or > 0.58)."""
    ea, oa, la = ea.upper(), oa.upper(), long_allele.upper()
    if COMP.get(ea) == oa:  # palindromic
        if ref_long_freq is None or 0.42 <= ref_long_freq <= 0.58:
            return None, "palindromic, frequency unusable -> dropped"
        f_long_if_same = eaf if la == ea else 1 - eaf
        same = abs(f_long_if_same - ref_long_freq) < abs((1 - f_long_if_same) - ref_long_freq)
        sign = (1 if la == ea else -1) * (1 if same else -1)
        return sign, f"palindromic; long-allele ref freq {ref_long_freq:.2f}; " + \
            ("strand consistent" if same else "STRAND FLIPPED (inferred from frequency)")
    if la == ea:
        return 1, ""
    if la == oa:
        return -1, ""
    if la == COMP.get(ea):
        return 1, "strand flip"
    if la == COMP.get(oa):
        return -1, "strand flip"
    return None, "allele mismatch -> dropped"


def fixed_meta(betas, ses):
    w = 1 / np.asarray(ses) ** 2
    return float(np.sum(w * betas) / w.sum()), float(1 / np.sqrt(w.sum()))


def fmt(b, se, p):
    return f"OR {np.exp(b):.2f} ({np.exp(b-1.96*se):.2f}-{np.exp(b+1.96*se):.2f}), P={p:.2g}"
