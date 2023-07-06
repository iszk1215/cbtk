from datetime import datetime, timedelta
from typing import List

from cbtk.core import Record
from cbtk.speedup import groupby_fastest


def filter_records_by_run_at(records, run_at):
    return [r for r in records if r.run_at >= run_at]


def split_records(records, run_at):
    before = []
    after = []
    for r in records:
        if r.run_at >= run_at:
            after += [r]
        else:
            before += [r]
    return before, after


def find(records: List[Record], suite, runner):
    outs = []
    for record in records:
        if record.suite == suite and record.runner.name == runner.name:
            outs += [record]
    return outs


def sorted_list_intersect(a: List, b: List):
    return sorted(list(set(a).intersection(set(b))))


def compute_difference(before: Record, after: Record, metric="duration"):
    assert before.suite == after.suite
    assert before.runner.name == after.runner.name

    values_before = before.get_values_by_metric(metric)
    values_after = after.get_values_by_metric(metric)

    benchmarks = sorted_list_intersect(values_before, values_after)
    # print(benchmarks)

    threshold = 0.1

    for bench in benchmarks:
        if bench in values_before and bench in values_after:
            vb = values_before[bench]
            va = values_after[bench]
            diff = va - vb
            ratio = diff / vb
            if abs(ratio) > threshold:
                print(
                    f"{before.suite} {after.runner.name} {bench}: {before.runner.version}->{after.runner.version} {vb:12.6f} -> {va:12.6f} = {diff:12.6f} {ratio*100:8.1f} %"
                )
        else:
            print("No data at least one-side")


def notify(records):
    now = datetime.now()
    run_at = now - timedelta(days=3)
    print(run_at)
    before, after = split_records(records, run_at)
    print(f"{len(records)} -> {len(before)} | {len(after)}")

    # for r in before:
    #     print(f"{r.suite} {r.runner:<20} {r.run_at}")

    fastests = groupby_fastest(before)

    for r in fastests.values():
        print(f"fastest: {r.suite} {r.runner:<20} {r.run_at}")

    for record in after:
        outs = find(fastests.values(), record.suite, record.runner)
        latest = outs[-1]
        print(
            f"{record.suite} {record.runner:<20} -> {len(outs)} {latest.suite}, {latest.runner}"
        )
        compute_difference(record, latest)
