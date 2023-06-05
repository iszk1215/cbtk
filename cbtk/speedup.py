from collections import defaultdict, namedtuple
from statistics import geometric_mean
from typing import List

from cbtk.core import Record, groupby, Runner


class SpeedupMatrix:

    def __init__(self):
        self.dic = defaultdict(dict)

    def runners(self) -> List[Runner]:
        return list(self.dic.keys())

    def get(self, from_: Runner, to: Runner) -> Record:
        return self.dic[from_][to]

    def set(self, from_: Runner, to: Runner, record: Record):
        self.dic[from_][to] = record


def make_speedup_record(record, base_durs, use_geomean=False):
    curr_durs = record.get_values_by_metric("duration")

    record = record.deepcopy()

    for name in curr_durs:
        if name in base_durs:
            speedup = base_durs[name] / curr_durs[name]
        else:
            speedup = None
        record.add_value(name, "_speedup", speedup)
    speedups = record.get_values_by_metric("_speedup")
    speedups = {k: v for k, v in speedups.items() if v is not None}
    if use_geomean:
        average = geometric_mean(speedups.values())
    else:
        average = sum(speedups.values()) / len(speedups)
    # TODO: check record has no benchmark named "_average"
    record.add_value("_average", "_speedup", average)

    return record


def drop_old_dev_version(runners):
    dic = defaultdict(list)
    for runner in sorted(runners):
        dic[runner.drop_dev_version()] += [runner]

    return [lst[-1] for lst in dic.values()]


def groupby_runner(records):
    grouped = defaultdict(list)
    for record in records:
        grouped[record.runner] += [record]
    return grouped


# records with the same suite
def make_speedup_matrix_for_suite(records, config):
    runner_records = groupby_runner(records)

    new_runners = drop_old_dev_version(runner_records.keys())
    runner_records = {r: runner_records[r] for r in new_runners}

    matrix = SpeedupMatrix()
    for r0 in runner_records:
        assert len(runner_records[r0]) == 1
        base_record = runner_records[r0][0]
        base_durs = base_record.get_values_by_metric("duration")
        for r1 in runner_records:
            assert len(runner_records[r1]) == 1
            target_record = runner_records[r1][0]
            speedup_record = make_speedup_record(target_record, base_durs,
                                                 config.geomean)
            matrix.set(r0, r1, speedup_record)

    return matrix


def groupby_srvt(records):
    Key = namedtuple("Key", ["suite", "runner"])

    def key_func(record):
        return Key(suite=record.suite, runner=record.runner)

    return groupby(records, key=key_func)


def make_fastest_record(suite, runner, records):
    values = defaultdict(list)
    for record in records:
        for name, dur in record.get_values_by_metric("duration").items():
            values[name] += [{"run_at": record.run_at, "duration": dur}]

    values = {
        name: min(values[name], key=lambda x: x["duration"])
        for name in values
    }

    return Record(suite=suite, runner=runner, values=values)


def groupby_fastest(records):
    grouped = groupby_srvt(records)

    aggregated = {}
    for key in grouped:
        aggregated[key] = make_fastest_record(key.suite, key.runner,
                                              grouped[key])

    return aggregated


def make_speedup_matrices(records, config):
    fastests = groupby_fastest(records)

    suites = defaultdict(list)
    for key, record in fastests.items():
        suites[key.suite] += [record]

    return {
        key: make_speedup_matrix_for_suite(suites[key], config)
        for key in suites
    }
