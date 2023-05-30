from collections import namedtuple
import functools

from cbtk.core import groupby
from cbtk.speedup import make_speedup_matrices, SpeedupMatrix


def print_speedups(matrix):
    for suite in matrix:
        suite_and_tag = suite.suite + (f"({suite.tags})" if suite.tags else "")
        runners = matrix[suite].runners()
        for r0 in runners:
            for r1 in runners:
                record = matrix[suite].get(r0, r1)
                speedups = record.get_values_by_metric("_speedup")
                average = speedups["_average"]
                print(f"{suite_and_tag:20} {r0:20} -> {r1:20}: {average:.3}")


def get_oldest(records):

    def cmp_run_at(x, y):
        return x if x.run_at < y.run_at else y

    return functools.reduce(cmp_run_at, records)


def get_latest(records):

    def cmp_run_at(x, y):
        return x if x.run_at > y.run_at else y

    return functools.reduce(cmp_run_at, records)


def convert_to_table(key, matrix):
    Table = namedtuple("Table", ["caption", "header", "rows"])

    caption = key.suite + (f"({key.tags})" if key.tags else "")
    header = [f"{r.name}-{r.version}" for r in matrix.runners()]

    rows = []
    for r0 in matrix.runners():
        row = [f"{r0.name}-{r0.version}"]
        row += [
            f"{matrix.get(r0, r1).value('_speedup', '_average'):.2f}"
            for r1 in matrix.runners()
        ]
        rows += [row]

    return Table(caption=caption, header=header, rows=rows)


def make_host_section(config, hostname, records, matrix):
    Section = namedtuple(
        "Data",
        ["hostname", "latest_run_at", "oldest_run_at", "num_runs", "tables"])

    oldest = get_oldest(records)
    latest = get_latest(records)

    tables = [convert_to_table(k, v) for k, v in matrix.items()]

    return Section(hostname=hostname,
                   latest_run_at=latest.run_at.strftime("%c"),
                   oldest_run_at=oldest.run_at.strftime("%c"),
                   num_runs=len(records),
                   tables=tables)


def make_html(maker, config, sections):
    home_template = maker.get_template("home.html")
    contents = home_template.render(sections=sections)

    data = {
        "site_title": config.title,
        "title": "Home",
        "contents": contents,
    }

    return maker.render_page(config, **data)


def drop_older_patch(runners):
    dropped = []
    for r0 in runners:
        is_older = any([r0.is_older_patch(r1) for r1 in runners])
        if not is_older:
            dropped += [r0]

    return dropped


def drop_patch(matrix):
    runners = matrix.runners()
    runners = drop_older_patch(runners)

    dropped = SpeedupMatrix()
    for r0 in runners:
        for r1 in runners:
            dropped.set(r0, r1, matrix.get(r0, r1))

    return dropped


def make_page(maker, config, records):
    groups = groupby(records, key=lambda r: r.hostname)

    sections = []
    for hostname in groups:
        matrices = make_speedup_matrices(groups[hostname], config)
        matrices = {k: drop_patch(v) for k, v in matrices.items()}
        # print_speedups(matrices)
        section = make_host_section(config, hostname, groups[hostname],
                                    matrices)
        sections += [section]

    maker.write("index.html", make_html(maker, config, sections))
