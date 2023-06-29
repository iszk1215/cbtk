import dateutil.parser

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


def filter_tags(tags, use=None):
    if tags is None:
        return None
    return ",".join(f"{k}={v}" for k, v in tags_to_dict(tags, use=use).items())


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
                use_runner_tags=None) -> Record:
    if len(durations) == 0:
        raise RuntimeError("empty durations")

    if suite_tags is None and use_suite_tags is not None:
        suite_tags = filter_tags(tags, use_suite_tags)

    if runner_tags is None and use_runner_tags is not None:
        runner_tags = filter_tags(tags, use_runner_tags)

    run_at_ = dateutil.parser.parse(run_at)

    suite = Suite(suite_name, suite_tags)
    runner = Runner(runner_name, Version.parse(runner_version), runner_tags)

    values = {k: {"duration": v} for k, v in durations.items()}

    return Record(suite=suite,
                  runner=runner,
                  hostname=hostname,
                  run_at=run_at_,
                  values=values)
