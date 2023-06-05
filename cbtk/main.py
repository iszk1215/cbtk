import argparse
import dateutil.parser
import glob
import json
import os

import jinja2

from cbtk.core import Record, Runner, Suite, Version


def tags_to_dict(raw, use=None):
    if len(raw) == 0:
        return {}

    ret = {}
    for s in raw.split(","):
        k, v = s.split("=")
        if use is None or k in use:
            ret[k] = v
    return ret


def get_tags(raw, use=None):
    if raw is None:
        return None
    return ",".join(f"{k}={v}" for k, v in tags_to_dict(raw, use=use).items())


def sort_by_run_at(records):
    return sorted(records, key=lambda record: record.run_at)


def load_file(filename):
    records = []

    def make_records(raw):
        values = {}
        for name, dur in raw["duration"].items():
            values[name] = {"duration": dur}

        metadata = raw["metadata"]
        runner = Runner.from_dict(metadata["runner"])
        suite = Suite.from_dict(metadata["suite"])
        run_at = dateutil.parser.parse(metadata["run_at"])

        return Record(suite=suite,
                      runner=runner,
                      run_at=run_at,
                      hostname=metadata["hostname"],
                      values=values)

    with open(filename) as f:
        dic = json.load(f)
        assert dic["version"] == 1
        records += [make_records(raw) for raw in dic["records"]]

    return sort_by_run_at(records)


def load_directory(directory):
    filenames = glob.glob(os.path.join(directory, "**/*.json"), recursive=True)
    return sort_by_run_at(
        sum([load_file(filename) for filename in filenames], []))


def load_records(config):
    records = []
    if config.data_dir is not None:
        records += load_directory(config.data_dir)
    for filename in config.filenames:
        records += load_file(filename)
    return records


def make_record(suite_name: str,
                runner_name: str,
                runner_version: str,
                hostname: str,
                run_at: str,
                durations: dict,
                suite_tags=None,
                runner_tags=None,
                tags=None,
                use_suite_tags=None,
                use_runner_tags=None):
    if len(durations) == 0:
        raise RuntimeError("empty durations")

    if suite_tags is None and use_suite_tags is not None:
        suite_tags = get_tags(tags, use_suite_tags)

    if runner_tags is None and use_runner_tags is not None:
        runner_tags = get_tags(tags, use_runner_tags)

    run_at = dateutil.parser.parse(run_at)

    suite = Suite(suite_name, suite_tags)
    runner = Runner(runner_name, Version.parse(runner_version), runner_tags)

    values = {k: {"duration": v} for k, v in durations.items()}

    return Runner(suite=suite,
                  runner=runner,
                  hostname=hostname,
                  run_at=run_at,
                  values=values)


def record_to_dict(record):
    durations = record.get_values_by_metric("duration")

    return {
        "metadata": {
            "suite": {
                "name": record.suite.name,
                "tags": record.suite.tags
            },
            "runner": {
                "name": record.runner.name,
                "version": str(record.runner.version),
                "tags": record.runner.tags
            },
            "hostname": record.hostname,
            "run_at": record.run_at.isoformat(),
        },
        "duration": durations,
    }


def records_to_json(records):
    return json.dumps(
        {
            "version": 1,
            "records": [record_to_dict(r) for r in records]
        },
        indent=2)


def store_records(filename, records):
    with open(filename, "w") as f:
        f.write(records_to_json(records))


def cmd_publish(args):

    if args.resource_dir is None:
        import cbtk.www
        args.resource_dir = cbtk.www.__path__[0]

    if args.runner_order is not None:
        args.runner_order = args.runner_order.split(",")

    if args.runner_display_order is not None:
        args.runner_display_order = args.runner_display_order.split(",")

    records = load_records(args)

    # Since some pages does not hostname-aware, filter by a hostname.
    records = [r for r in records if r.hostname == args.hostname]

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(
        os.path.join(args.resource_dir, "templates")),
                             autoescape=jinja2.select_autoescape())

    output_dir = args.output

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    from cbtk.pages import PageMaker
    maker = PageMaker("", env, output_dir)
    maker.copy_file(args, "output.css")

    print("making home page...")
    from cbtk.pages import make_home_page
    make_home_page("", env, output_dir, args, records)

    print("making timeline page...")
    from cbtk.pages import make_timeline_page
    make_timeline_page("timeline", env, output_dir, args, records)

    print("making runner page...")
    from cbtk.pages import make_runners_page
    make_runners_page("runners", env, output_dir, args, records)


def main():
    parser = argparse.ArgumentParser()

    parent_parser = argparse.ArgumentParser()
    parent_parser.add_argument("filenames", nargs="*")
    parent_parser.add_argument("-d", "--data-dir", default=None)

    subparsers = parser.add_subparsers(title="command",
                                       metavar="command",
                                       required=True,
                                       dest="command")

    publish_parser = subparsers.add_parser(name="publish",
                                           parents=[parent_parser],
                                           add_help=False)
    publish_parser.add_argument("-r", "--resource-dir", default=None)
    publish_parser.add_argument("-o", "--output", default="public")
    publish_parser.add_argument("-b", "--base-url", default="/")
    publish_parser.add_argument("--runner-order", default=None)
    publish_parser.add_argument("--runner-display-order", default=None)
    publish_parser.add_argument("--title", default="Benchmark")
    publish_parser.add_argument("--geomean", action="store_true")
    publish_parser.add_argument("--hostname", default=None, required=True)
    publish_parser.set_defaults(func=cmd_publish)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
