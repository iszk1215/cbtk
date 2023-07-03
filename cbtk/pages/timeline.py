from collections import defaultdict, namedtuple
from dataclasses import dataclass
import json

from cbtk.core import groupby, Suite, Runner


class TimelineSeries:
    def __init__(
        self,
        hostname: str,
        suite: Suite,
        benchmark: str,
        runner: Runner,
        points: dict,
    ):
        self.hostname = hostname
        self.suite = suite
        self.benchmark = benchmark
        self.runner = runner
        self.points = points

    @property
    def label(self):
        return self.runner.longname


class TimelineChart:
    def __init__(self, suite, benchmark, runner_name):
        self.suite = suite
        self.benchmark = benchmark
        self.runner_name = runner_name
        self.records = []

    def add(self, record: TimelineSeries):
        self.records += [record]

    @property
    def chart_id(self):
        return f"{self.suite}/{self.runner_name}/{self.benchmark}"


def make_sorter_by_runner(runner_orders=None):
    def key(runner_name):
        if runner_orders is None:
            return runner_name
        else:
            try:
                runner_order = runner_orders.index(runner_name)
            except ValueError:
                runner_order = len(runner_orders)
            return (runner_order, runner_name)

    def sorter(runner_names):
        return sorted(runner_names, key=key)

    return sorter


# Unstack by bench
def make_timeline_points(records, metric):
    points = defaultdict(list)
    for record in records:
        durations = record.get_values_by_metric(metric)
        version = str(record.runner.version)
        for bench, value in durations.items():
            # add data point
            points[bench] += [
                {
                    "x": record.run_at.isoformat(),
                    "y": value,
                    "version": version,  # JSON serializable
                    "tags": record.runner.tags,
                }
            ]

    return points


def make_timeline_series(records):
    Key = namedtuple("Key", ["hostname", "suite", "runner"])
    g = groupby(
        records,
        key=lambda r: Key(r.hostname, r.suite, r.runner.drop_dev_version()),
    )

    series = []
    for key, records in g.items():
        points = make_timeline_points(records, "duration")
        for bench, pts in points.items():
            ser = TimelineSeries(
                key.hostname, key.suite, bench, key.runner, pts
            )
            series += [ser]

    return series


# input records are sorted by run_at
def make_timeline_charts(records, config):
    series = make_timeline_series(records)

    # group by suite, benchmark and runner_name
    Key = namedtuple("Key", ["suite", "benchmark", "runner_name"])
    grouped = defaultdict(list)
    for ser in series:
        key = Key(ser.suite, ser.benchmark, ser.runner.name)
        grouped[key] += [ser]

    charts = []
    for key in grouped:
        chart = TimelineChart(key.suite, key.benchmark, key.runner_name)
        for ser in grouped[key]:
            chart.add(ser)
        charts += [chart]

    return charts


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
                "title": {"display": True, "text": "duration sec"},
            },
        },
        "datasets": {"line": {"borderWidth": 1}},
        "plugins": {
            "legend": {
                "display": False,
            },
            "title": {"display": False, "text": title},
        },
    }


def make_chart_config(chart: TimelineChart):
    title = f"{chart.suite}.{chart.benchmark}"
    ds = [{"label": ser.label, "data": ser.points} for ser in chart.records]

    return {
        "type": "line",
        "data": {
            "datasets": ds,
        },
        "options": get_line_chart_options(f"{title}"),
    }


def make_chart_config_json(config, charts):
    return json.dumps(
        {c.chart_id: make_chart_config(c) for c in charts}, indent=2
    )


def make_timeline_subsection(runner_name, charts):
    SubSection = namedtuple("SubSection", ["title", "charts"])
    Chart = namedtuple("Chart", ["title", "index", "benchmark"])
    tmp = [
        Chart(f"{c.suite}.{c.benchmark}", c.chart_id, c.benchmark)
        for c in charts
    ]

    return SubSection(title=runner_name, charts=tmp)


def make_timeline_section(config, suite, charts):
    by_runner_names = defaultdict(list)
    for chart in charts:
        by_runner_names[chart.runner_name] += [chart]

    sorter = make_sorter_by_runner(config.runner_display_order)
    runner_names = sorter(by_runner_names.keys())

    subsecs = [
        make_timeline_subsection(name, by_runner_names[name])
        for name in runner_names
    ]

    Section = namedtuple("Section", ["title", "children"])
    return Section(title=str(suite), children=subsecs)


def make_timeline_sections(config, charts):
    by_suite = defaultdict(list)
    for chart in charts:
        by_suite[chart.suite] += [chart]

    return [make_timeline_section(config, k, v) for k, v in by_suite.items()]


def make_main_page(config, maker, charts, sections):
    contents = maker.render("timeline/main.html", config, sections=sections)
    nav = maker.render("timeline/nav.html", config, sections=sections)

    page_data = {
        "title": "Timeline",
        "nav": nav,
        "contents": contents,
        "script": "timeline.js",
        "use_chart": True,
    }

    maker.copy_file(config, "timeline.js")
    maker.write("data.json", make_chart_config_json(config, charts))
    maker.write("index.html", maker.render_page(config, **page_data))


def make_page(maker, config, records):
    charts = make_timeline_charts(records, config)
    sections = make_timeline_sections(config, charts)

    make_main_page(config, maker, charts, sections)
