from datetime import timedelta


def featured_periods(buckets):
    """Rank up to four disjoint windows of thermal readings in half-hour buckets."""
    candidates = []
    left = 0
    readings = channels = 0
    for right, (start, end, count, channel_count) in enumerate(buckets):
        if right and start - buckets[right - 1][1] > timedelta(hours=8):
            left = right
            readings = channels = 0
        readings += count
        channels += channel_count
        while end - buckets[left][0] > timedelta(hours=72):
            readings -= buckets[left][2]
            channels -= buckets[left][3]
            left += 1
        hours = (end - buckets[left][0]).total_seconds() / 3600
        occupied = right - left + 1
        if hours >= 48 and occupied >= 0.75 * (2 * hours):
            candidates.append((occupied, channels, end, buckets[left][0], readings))

    selected = []
    for _, _, end, start, count in sorted(candidates, reverse=True):
        if all(end < a or start > b for a, b, _ in selected):
            selected.append((start, end, count))
            if len(selected) == 4:
                break
    return [{'de': a.isoformat(), 'ate': b.isoformat(), 'count': n} for a, b, n in selected]
