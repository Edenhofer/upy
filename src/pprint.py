#!/usr/bin/env python3


def format_timedelta(seconds):
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):d}:{int(m):02d}:{s:05.2f}"


def progress_bar(
    iterable,
    total=None,
    prefix: str = "",
    suffix: str = "",
    decimals: int = 1,
    length: int = 20,
    fill: str = "█",
):
    """Create a terminal progress bar while yielding elements of an iterator."""
    import sys
    import time

    N_UPDATES_PER_SECOND = 10

    total = len(iterable) if not total else total

    def print_progress(
        iteration: int,
        time_elapsed: float,
        time_of_arrival: float,
        it_per_second: float,
    ):
        percent = f"{{0:{decimals+5}.{decimals}%}}".format(iteration / total)
        filled_len = length * iteration // total
        bar = fill * filled_len + "-" * (length - filled_len)
        # f-string expression is at most `9 = 4 + 5` spaces wide
        fmt_its = "{0:>9s} it/s".format(f"{it_per_second:#6.4g}")
        msg = (
            f"\r{prefix}|{bar}| {percent}{suffix}"
            " ["
            f"{format_timedelta(time_elapsed)}"
            f", ETA {format_timedelta(time_of_arrival)}"
            f", {fmt_its}"
            "]"
        )
        sys.stdout.write(msg)
        sys.stdout.flush()

    # `time.time()` is faster than `datetime.datetime.now()`
    start_time = prev_time = time.time()
    prev_it = -1
    update_it = 1
    print_progress(0, 0.0, 0.0, 0.0)
    for i, item in enumerate(iterable):
        yield item
        if i - prev_it == update_it:
            cur_time = time.time()
            time_diff = cur_time - prev_time
            prev_time = cur_time
            time_elapsed = cur_time - start_time
            it_per_second = (i + 1) / time_elapsed
            eta = (total - (i + 1)) / it_per_second
            # Update via the harmonic mean to always be close to the minimum
            cur_it_per_s = (i - prev_it) / time_diff
            update_it = int(
                round(2 / (1 / update_it + N_UPDATES_PER_SECOND / cur_it_per_s))
            )
            update_it = max(1, update_it)
            print_progress(
                i + 1,
                time_elapsed=time_elapsed,
                time_of_arrival=eta,
                it_per_second=it_per_second,
            )
            prev_it = i
    time_diff = time.time() - start_time
    print_progress(total, time_diff, 0.0, total / time_diff)
    sys.stdout.write("\n")
    sys.stdout.flush()
