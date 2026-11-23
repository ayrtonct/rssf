from datetime import timedelta


def featured_periods(buckets, minimum_hours=48):
    """Keep entire collection runs containing a well-covered multi-day window."""
    periods = []
    start_index = left = total = 0
    qualifies = False

    def finish(last):
        if qualifies:
            periods.append({'de': buckets[start_index][0].isoformat(),
                            'ate': buckets[last][1].isoformat(), 'count': total})

    for right, (start, end, count, _) in enumerate(buckets):
        if right and start - buckets[right - 1][1] > timedelta(hours=8):
            finish(right - 1)
            start_index = left = right
            total = 0
            qualifies = False
        total += count
        while end - buckets[left][0] > timedelta(hours=72):
            left += 1
        hours = (end - buckets[left][0]).total_seconds() / 3600
        if hours >= minimum_hours and right - left + 1 >= 0.75 * (2 * hours):
            qualifies = True

    if buckets:
        finish(len(buckets) - 1)
    return periods
