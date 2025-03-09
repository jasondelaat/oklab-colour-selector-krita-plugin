"""This module contains the actual implementation of the OKLab colour
space transformations to and from sRGB.

With the exception of the 'clip' function everything here is mostly a
direct copy/paste from Björn Ottosson's blog post introducing OKLab
with only minor alterations. The functions have been edited to conform
to Python syntax and renamed for clarity and the per-channel
transformations between RGB and sRGB have been included directly in
the relevant sRGB <-> OKLab functions. The 'oklab_to_srgb' function
has been modified to return middle gray [128, 128, 128] in case of
gamut clipping as well as a boolean indicating whether clipping has
occured or not.

Björn Ottosson's OKLab blog post can be found here:
https://bottosson.github.io/posts/oklab/

This module is offered under the terms Ottosson's original copyright
notice below:

Copyright (c) 2020 Björn Ottosson
Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

from collections import namedtuple

from .util import *

Lab = namedtuple('Lab', ['L', 'a', 'b'])
RGB = namedtuple('RGB', ['r', 'g', 'b'])

def srgb_to_oklab(c):
    #c = RGB(*map(srgb_channel_to_rgb_channel, c))
    l = 0.4122214708 * c.r + 0.5363325363 * c.g + 0.0514459929 * c.b
    m = 0.2119034982 * c.r + 0.6806995451 * c.g + 0.1073969566 * c.b
    s = 0.0883024619 * c.r + 0.2817188376 * c.g + 0.6299787005 * c.b
    
    l_ = cbrt(l)
    m_ = cbrt(m)
    s_ = cbrt(s)
    
    return Lab(
        0.2104542553*l_ + 0.7936177850*m_ - 0.0040720468*s_,
        1.9779984951*l_ - 2.4285922050*m_ + 0.4505937099*s_,
        0.0259040371*l_ + 0.7827717662*m_ - 0.8086757660*s_
    )

def oklab_to_srgb(c):
    l_ = c.L + 0.3963377774*c.a + 0.2158037573*c.b
    m_ = c.L - 0.1055613458*c.a - 0.0638541728*c.b
    s_ = c.L - 0.0894841775*c.a - 1.2914855480*c.b

    l = l_*l_*l_
    m = m_*m_*m_
    s = s_*s_*s_

    rgb = [
        4.0767416621*l - 3.3077115913*m + 0.2309699292*s,
        -1.2684380046*l + 2.6097574011*m - 0.3413193965*s,
        -0.0041960863*l - 0.7034186147*m + 1.7076147010*s
    ]

    rgb, clipped = clip(map(rgb_channel_to_srbg_channel, rgb))
    return rgb, clipped

def rgb_channel_to_srbg_channel(x):
    if x > 0.0031308:
        return (1.055) * x**(1.0/2.4) - 0.055
    else:
        return 12.92 * x

def srgb_channel_to_rgb_channel(x):
    if x >= 0.04045:
        return ((x + 0.055)/(1 + 0.055))**2.4
    else:
        return x / 12.92

def clip(col):
    data = []
    for c in col:
        if c < 0 or c > 1:
            return [128, 128, 128], True
        data.append(int(255*c))
    return data, False

