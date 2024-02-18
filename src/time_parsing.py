#!/usr/bin/env python3

import re

re_timedelta = (
    r"^((?P<days>[\.\d]+?)d)"
    r"?((?P<hours>[\.\d]+?)h)"
    r"?((?P<minutes>[\.\d]+?)m)"
    r"?((?P<seconds>[\.\d]+?)s)?$"
)
regex = re.compile(re_timedelta)


def parse_timedelta(time_str):
    """Parses a time string, e.g. (2h13m), into a timedelta object.

    Adapted from https://stackoverflow.com/a/4628148/851699

    Parameters
    ----------
    time_str: str
        Time duration, e.g. `2h13m`.

    Returns
    -------
    time_delta : datetime.timedelta
        Time difference representation of the input string
    """
    from datetime import timedelta

    parts = regex.match(time_str)
    if parts is None:
        ve = f"unable to parse time '{time_str!r}'"
        raise ValueError(ve)
    time_params = {
        name: float(param) for name, param in parts.groupdict().items() if param
    }
    return timedelta(**time_params)
