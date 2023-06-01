from collections import defaultdict, namedtuple
import json

from cbtk.core import groupby


def make_sorter_by_runner(runner_orders=None):

    def key(keys):
        if runner_orders is None:
            return keys[1]
        else:
            try:
                runner_order = runner_orders.index(keys[2])
            except ValueError:
                runner_order = len(runner_orders)
            return (keys.hostname, keys.suite, runner_order)

    def sorter(records):
        return sorted(records, key=key)

    return sorter


def groupby_suite_runner(records, sort_func=None):
    Key = namedtuple("Key", ["hostname", "suite", "runner"])

    def key_func(record):
        return Key(record.hostname, record.suite, record.runner.name)

    return groupby(records, key=key_func, sort_func=sort_func)


# Unstack by bench
def to_timeline_data(records, metric):
    benchmarks = defaultdict(list)
    for record in records:
        durations = record.get_values_by_metric(metric)
        version = str(record.runner.version)
        for name, value in durations.items():
            benchmarks[name] += [{
                "x": record.run_at.isoformat(),
                "y": value,
                "version": version,  # JSON serializable
                "tags": record.runner.tags,
            }]
    return benchmarks


# records are sorted by run_at
def make_timeline_data(records, config):
    sorter = make_sorter_by_runner(config.runner_display_order)
    grouped = groupby_suite_runner(records, sort_func=sorter)

    aggregated = {}
    for key, records in grouped.items():
        group_by_version = groupby(records,
                                   key=lambda r: r.runner.drop_dev_version())

        datasets_by_bench = defaultdict(list)
        for runner, records in group_by_version.items():
            benchmarks = to_timeline_data(records, "duration")
            for bench, data in benchmarks.items():
                datasets_by_bench[bench] += [{
                    "label": str(runner),
                    "data": data
                }]

        aggregated[key] = datasets_by_bench

    return aggregated


def get_line_chart_options(title):
    return {
        "animation": False,
        "aspectRatio": 1.5,
        "pointRadius": 2,
        "scales": {
            "x": {
                "type": "time",
                "ticks": {
                    "font": {
                        "size": 10,
                    },
                },
            },
            "y": {
                "type": "linear",
                "beginAtZero": True,
                "title": {
                    "display": True,
                    "text": "duration sec"
                }
            },
        },
        "datasets": {
            "line": {
                "borderWidth": 1
            }
        },
        "plugins": {
            "legend": {
                "display": False,
            },
            "title": {
                "display": True,
                "text": title
            },
        }
    }


def make_chart_config(title, label, datasets):
    return {
        "type": "line",
        "data": {
            "datasets": datasets
        },
        "options": get_line_chart_options(f"{title}")
    }


def make_chart_config_json(config, data):
    out = []
    for key, datasets_by_bench in data.items():
        configs = [
            make_chart_config(f"{key.suite}.{bench}", bench, datasets)
            for bench, datasets in datasets_by_bench.items()
        ]
        out += configs

    return json.dumps(out, indent=2)


def make_chart_indices(data):
    Key = namedtuple("Key", ["hostname", "suite"])
    dic = defaultdict(lambda: defaultdict(list))
    idx = 0
    for key, records in data.items():
        n = len(records)
        k = Key(key.hostname, key.suite)
        dic[k][key.runner] += list(range(idx, idx + n))
        idx += n
    return dic


def make_timeline_sections(config, data):
    chart_indices = make_chart_indices(data)

    Section = namedtuple("Section", ["title", "children"])
    SubSection = namedtuple("SubSection", ["title", "charts", "hidden"])
    Chart = namedtuple("Chart", ["index"])

    sections = []
    for key in chart_indices:
        subsecs = []
        for i, (runner, indices) in enumerate(chart_indices[key].items()):
            charts = [Chart(index=j) for j in indices]
            hidden = "" if i == 0 else "hidden"
            subsecs += [SubSection(title=runner, charts=charts, hidden=hidden)]

        sections += [Section(title=str(key.suite), children=subsecs)]

    return sections


def make_html(maker, config, data):
    sections = make_timeline_sections(config, data)

    contents = maker.get_template("timeline.html").render(sections=sections)
    nav = maker.get_template("nav.html").render(sections=sections)

    return {
        "title": "Timeline",
        "nav": nav,
        "contents": contents,
        "script": "timeline.js",
        "use_chart": True
    }


def make_page(maker, config, records):
    data = make_timeline_data(records, config)
    maker.copy_file(config, "timeline.js")
    maker.write("data.json", make_chart_config_json(config, data))
    maker.write("index.html",
                maker.render_page(config, **make_html(maker, config, data)))
