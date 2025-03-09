def cbrt(x):
    "Basic Newton-Raphson cube-root function."
    x1 = x/2
    x0 = 0
    while abs(x1 - x0) > 0.000001:
        x0 = x1
        x0_2 = x0*x0
        x0_3 = x0_2*x0
        x1 = x0 - (x0_3 - x) / (3*x0_2)
    return x1

def lerp(low, high, t):
    """Linear interpolation between 'low' and 'high'. 't' should
    (usually) be a in the range 0-1.
    """
    return low + t*(high - low)
