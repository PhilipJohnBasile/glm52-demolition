"""Kernighan & Pike: clarity over cleverness; small honest functions; names that explain; no dead code."""


def merge_intervals(intervals):
    """Merge overlapping [start, end] intervals into a sorted, non-overlapping list.

    >>> merge_intervals([[1, 3], [2, 6], [8, 10]])
    [[1, 6], [8, 10]]
    """
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda interval: interval[0])
    merged = [list(ordered[0])]
    for start, end in ordered[1:]:
        last = merged[-1]
        if start <= last[1]:                 # overlaps the previous interval → extend it
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    return merged
