"""Binary search bounds over sorted lists."""


def lower_bound(arr, x):
    """Index of the first element >= x in ascending-sorted arr (len(arr) if none)."""
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] <= x:
            lo = mid + 1
        else:
            hi = mid
    return lo
