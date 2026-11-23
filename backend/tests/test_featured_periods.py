from datetime import datetime, timedelta
from featured_periods import featured_periods


def run(start, n, step=30, count=1):
    times = [start + timedelta(minutes=i * step) for i in range(n)]
    return [(t, t, count, 4) for t in times]


def test_continuous_windows_prioritize_coverage_over_bursts():
    start = datetime(2026, 11, 1, 17)
    later = start + timedelta(days=10)
    windows = featured_periods(run(start, 145) + run(later, 97) +
                              run(later + timedelta(days=6), 8, count=200))
    assert [w['count'] for w in windows] == [145, 97]
    assert windows[0]['de'] == start.isoformat()
    assert windows[0]['ate'] == (start + timedelta(days=3)).isoformat()


def test_sparse_days_and_short_runs_do_not_join_across_outage():
    start = datetime(2026, 11, 1)
    assert featured_periods(run(start, 70) + run(start + timedelta(days=2), 60)) == []
    assert featured_periods(run(start, 80, step=60)) == []
