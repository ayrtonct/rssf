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


def test_all_qualifying_runs_are_returned_in_full_and_in_date_order():
    start = datetime(2026, 4, 10, 16)
    rows = []
    for i, length in enumerate([97, 241, 101, 145, 111, 99]):
        rows.extend(run(start + timedelta(days=i * 10), length))
    periods = featured_periods(rows)
    assert [p['count'] for p in periods] == [97, 241, 101, 145, 111, 99]
    assert periods[1]['ate'] == (start + timedelta(days=15)).isoformat()


def test_shorter_august_campaign_requires_second_node_threshold():
    rows = run(datetime(2026, 8, 28, 16), 77)
    assert featured_periods(rows) == []
    assert featured_periods(rows, minimum_hours=36)[0]['count'] == 77
