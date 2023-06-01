from collections import defaultdict, namedtuple
import json
from typing import List, Optional

from cbtk.core import Record
from cbtk.speedup import make_speedup_matrices


def get_chart_options(title, ylabel):
    return {
        "animation": False,
        "pointRadius": 2,
        "scales": {
            "y": {
                "title": {
                    "display": True,
                    "text": ylabel,
                }
            },
        },
        "datasets": {
            "line": {
                "borderWidth": 1
            }
        },
        "plugins": {
            # "legend": {"display": False},
            "title": {
                "display": True,
                "text": title
            },
        }
    }


def make_chart_config(records, title):

    def to_chart_data(x, values):
        formatted_run_at = formatted_duration = ""
        if "run_at" in values:
            formatted_run_at = values["run_at"].isoformat()
        if "duration" in values:
            formatted_duration = f'{round(values["duration"], 3)} sec'

        return {
            "x": x,
            "y": values["_speedup"],
            "run_at": formatted_run_at,
            "duration": formatted_duration,
        }

    datasets = []
    for records in records:
        data = [
            to_chart_data(bench, records.get_values_by_bench(bench))
            for bench in records.benchmarks
        ]
        datasets += [{"label": f"{records.runner}", "data": data}]

    return {
        "type": "bar",
        "data": {
            "datasets": datasets
        },
        "options": get_chart_options(title, "speedup")
    }


def get_latest_version(matrix, runner_order) -> Optional[List[Record]]:
    latest_runners = {}
    for r in sorted(matrix.runners()):
        latest_runners[r.name] = r

    for name in runner_order:
        runner = latest_runners.get(name)
        if runner is not None:
            return [matrix.get(runner, r) for r in latest_runners.values()]

    return None


def make_speedup_data(config, records):
    matrices = make_speedup_matrices(records, config)

    suites = {}
    for key, matrix in matrices.items():
        suites[key] = get_latest_version(matrix, config.runner_order)

    return {k: v for k, v in suites.items() if v is not None and len(v) > 1}


def make_chart_config_json(config, suites):
    chart_configs = []
    for suite, records in suites.items():
        chart_configs += [make_chart_config(records, str(suite))]

    return json.dumps(chart_configs, indent=2)


def make_html(maker, config, suites):
    Section = namedtuple("Section", ["title", "records"])
    sections = []
    for suite, records in suites.items():
        sections += [Section(title=str(suite), records=records)]

    nav = maker.get_template("nav.html").render(sections=sections)
    contents = maker.get_template("runners.html").render(sections=sections)

    return {
        "title": "Runners",
        "nav": nav,
        "contents": contents,
        "use_chart": True,
        "script": "runners.js"
    }


def make_page(maker, config, records):
    suites = make_speedup_data(config, records)

    # ignore suite without speedup
    suites = {k: v for k, v in suites.items() if v is not None}

    maker.copy_file(config, "runners.js")
    maker.write("data.json", make_chart_config_json(config, suites))
    maker.write("index.html",
                maker.render_page(config, **make_html(maker, config, suites)))
