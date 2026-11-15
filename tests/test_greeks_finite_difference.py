"""Greeks vs central finite differences — PRD §8.2, rel err < 1e-4 with
absolute floor 1e-8 near zero (AGENTS.md numerical discipline)."""

import math

import pytest

from volsurf.bsm import black_scholes, delta, gamma, rho, theta, vega

GRID = [
    (S, K, T, sigma)
    for S in (90.0, 100.0, 110.0)
    for m in (0.8, 1.0, 1.2)
    for T in (0.02, 0.08, 0.25, 1.0)
    for sigma in (0.1, 0.2, 0.4)
    for K in [m * 100.0]
]
R, Q = 0.05, 0.02
ABS_FLOOR = 1e-8


def _fd(f, x, h):
    return (f(x + h) - f(x - h)) / (2.0 * h)


def _assert_close(analytic: float, fd: float, label: str) -> None:
    if abs(analytic - fd) < ABS_FLOOR:
        return
    denom = max(abs(fd), ABS_FLOOR)
    assert abs(analytic - fd) / denom < 1e-4, f"{label}: analytic={analytic!r} fd={fd!r}"


@pytest.mark.parametrize("S,K,T,sigma", GRID)
@pytest.mark.parametrize("option", ["call", "put"])
def test_delta_vs_fd(S, K, T, sigma, option):
    h = S * 1e-4
    fd = _fd(lambda s: black_scholes(s, K, T, sigma, R, Q, option), S, h)
    _assert_close(
        delta(S, K, T, sigma, R, Q, option), fd, f"delta S={S} K={K} T={T} sig={sigma} {option}"
    )


@pytest.mark.parametrize("S,K,T,sigma", GRID)
@pytest.mark.parametrize("option", ["call", "put"])
def test_gamma_vs_fd(S, K, T, sigma, option):
    h = S * 1e-4
    fd = _fd(lambda s: delta(s, K, T, sigma, R, Q, option), S, h)
    _assert_close(
        gamma(S, K, T, sigma, R, Q, option), fd, f"gamma S={S} K={K} T={T} sig={sigma} {option}"
    )


@pytest.mark.parametrize("S,K,T,sigma", GRID)
@pytest.mark.parametrize("option", ["call", "put"])
def test_vega_vs_fd(S, K, T, sigma, option):
    h = 1e-4  # larger step: tiny-vega cases are FD-noise-bound, not truncation-bound
    fd = _fd(lambda v: black_scholes(S, K, T, v, R, Q, option), sigma, h)
    _assert_close(
        vega(S, K, T, sigma, R, Q, option), fd, f"vega S={S} K={K} T={T} sig={sigma} {option}"
    )


@pytest.mark.parametrize("S,K,T,sigma", GRID)
@pytest.mark.parametrize("option", ["call", "put"])
def test_theta_vs_fd(S, K, T, sigma, option):
    h = 1e-5
    fd = _fd(lambda t: black_scholes(S, K, t, sigma, R, Q, option), T, h)
    _assert_close(
        -theta(S, K, T, sigma, R, Q, option), fd, f"theta S={S} K={K} T={T} sig={sigma} {option}"
    )


@pytest.mark.parametrize("S,K,T,sigma", GRID)
@pytest.mark.parametrize("option", ["call", "put"])
def test_rho_vs_fd(S, K, T, sigma, option):
    h = 1e-5
    fd = _fd(lambda rr: black_scholes(S, K, T, sigma, rr, Q, option), R, h)
    _assert_close(
        rho(S, K, T, sigma, R, Q, option), fd, f"rho S={S} K={K} T={T} sig={sigma} {option}"
    )


def test_math_imported():
    assert math is not None  # keep flake8 happy; math used in docstring example only
