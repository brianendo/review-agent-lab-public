"""Binary search utilities over sorted lists."""


def search_insert(arr, target):
    """Return the index of target in the ascending-sorted arr, or the index
    where it should be inserted to keep arr sorted."""
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] < target:
            lo = mid
        else:
            hi = mid
    return lo
