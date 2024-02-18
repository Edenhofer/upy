#!/usr/bin/env python3

from collections import deque, namedtuple


Timed = namedtuple(
    "Timed",
    ("time", "number", "repeat", "median", "q16", "q84", "mean", "std"),
    rename=True,
)


def timeit(stmt, setup=lambda: None, *, number=None, repeat=7):
    import timeit
    import numpy as np

    t = timeit.Timer(stmt)
    if number is None:
        number, _ = t.autorange()

    setup()
    t = np.array(t.repeat(number=number, repeat=repeat)) / number
    return Timed(
        time=np.median(t),
        number=number,
        repeat=repeat,
        median=np.median(t),
        q16=np.quantile(t, 0.16),
        q84=np.quantile(t, 0.84),
        mean=np.mean(t),
        std=np.std(t),
    )
