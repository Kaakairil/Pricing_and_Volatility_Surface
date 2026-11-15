# Black-Scholes-Merton Pricing & Greeks Derivation

## Dynamics under risk-neutral measure Q

With continuous dividend yield $q$ and risk-free rate $r$:

$$dS_t = (r - q) S_t \, dt + \sigma S_t \, dW_t^{\mathbb{Q}}, \qquad S_T = S_0 \exp\!\left((r - q - \tfrac{1}{2}\sigma^2)T + \sigma\sqrt{T}\, Z\right), \quad Z \sim \mathcal{N}(0,1).$$

## Closed-form price

Risk-neutral expectation $V_0 = e^{-rT}\,\mathbb{E}^{\mathbb{Q}}[\text{payoff}(S_T)]$:

$$C = S e^{-qT} N(d_1) - K e^{-rT} N(d_2), \qquad P = K e^{-rT} N(-d_2) - S e^{-qT} N(-d_1)$$

$$d_1 = \frac{\ln(S/K) + (r - q + \tfrac{1}{2}\sigma^2)T}{\sigma\sqrt{T}}, \qquad d_2 = d_1 - \sigma\sqrt{T}.$$

Subtracting gives European put-call parity: $C - P = S e^{-qT} - K e^{-rT}$.

## Analytical Greeks

Using the key identity $S e^{-qT} N'(d_1) = K e^{-rT} N'(d_2)$:

| Greek | Call | Put |
|---|---|---|
| $\Delta = \partial V/\partial S$ | $e^{-qT} N(d_1)$ | $e^{-qT}(N(d_1) - 1)$ |
| $\Gamma = \partial^2 V/\partial S^2$ | $\dfrac{e^{-qT} N'(d_1)}{S \sigma \sqrt{T}}$ | same |
| $\mathcal{V} = \partial V/\partial \sigma$ | $S e^{-qT} N'(d_1)\sqrt{T}$ | same |
| $\Theta = \partial V/\partial t = -\partial V/\partial T$ | $-\dfrac{S e^{-qT} N'(d_1)\sigma}{2\sqrt{T}} + q S e^{-qT} N(d_1) - r K e^{-rT} N(d_2)$ | $-\dfrac{S e^{-qT} N'(d_1)\sigma}{2\sqrt{T}} - q S e^{-qT} N(-d_1) + r K e^{-rT} N(-d_2)$ |
| $\rho = \partial V/\partial r$ | $K T e^{-rT} N(d_2)$ | $-K T e^{-rT} N(-d_2)$ |

Theta is per year; divide by 365 for per-calendar-day decay. At $T=0$ or $\sigma=0$, `black_scholes` returns the discounted intrinsic $\max(\pm(S e^{-qT} - K e^{-rT}), 0)$ without dividing by zero.

## Reference

Hull, J. C., *Options, Futures, and Other Derivatives*, 11th ed., Chs. 15 & 19.
