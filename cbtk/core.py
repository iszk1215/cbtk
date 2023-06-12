from collections import defaultdict
import copy
import re


class Runner:

    def __init__(self, name, version: "Version", tags=None):
        self.name = name
        self.version = version
        self.tags = tags

    @classmethod
    def from_dict(self, dic):
        return Runner(dic["name"], Version.parse(dic["version"]), dic["tags"])

    def __format__(self, spec):
        return f"{str(self):{spec}}"

    def __repr__(self):
        return f"{self.name}-{self.version}"

    @property
    def longname(self):
        if self.tags:
            return f"{self.name}-{self.version}({self.tags})"
        return f"{self.name}-{self.version}"

    def drop_dev_version(self):
        return Runner(self.name, self.version.drop_dev(), self.tags)

    def is_older_patch(self, other):
        return (self.name == other.name
                and self.version.is_older_patch(other.version))

    def __lt__(self, other):
        if self.name != other.name:
            return self.name < other.name
        return self.version < other.version

    def __eq__(self, other):
        return self.name == other.name and self.version == other.version

    def __hash__(self):
        return hash((self.name, str(self.version), self.tags))


class Suite:

    def __init__(self, name, tags=None):
        self.name = name
        self.tags = tags

    @classmethod
    def from_dict(cls, dic):
        return Suite(dic["name"], dic.get("tags"))

    def __repr__(self):
        if self.tags:
            return f"{self.name}({self.tags})"
        return self.name

    def __eq__(self, other):
        return self.name == other.name and self.tags == other.tags

    def __hash__(self):
        return hash((self.name, self.tags))

    def __lt__(self, other):
        return self.name < other.name


class Version:

    def __init__(self, major, minor, patch, dev=None, dist=None):
        self._version = (major, minor, patch, dev)
        self._dist = dist

    @classmethod
    def parse(cls, text):
        m = re.match(r"(\d+)\.(\d+)\.(\d+)\.?(dev.*)?", text)
        if m is None:
            raise ValueError(f"Unexpected version string: {text}")
        major, minor, patch = [int(x) for x in m.groups()[:3]]
        dev = m.group(4)
        dist = None
        if dev is not None:
            m = re.match(r"dev(\d+).*", dev)
            if m is None:
                raise ValueError(f"illegal dev version: {dev}")
            dist = int(m.group(1))
        return Version(major, minor, patch, dev, dist)

    @property
    def major(self):
        return self._version[0]

    @property
    def minor(self):
        return self._version[1]

    @property
    def patch(self):
        return self._version[2]

    def drop_dev(self):
        return Version(self.major, self.minor, self.patch)

    def is_older_patch(self, other):
        """Return true if self has the same major and minor as other, and older
        than other
        """
        return (self.major == other.major and self.minor == other.minor
                and self < other)

    def __eq__(self, other):
        return self._version == other._version

    def __hash__(self):
        return hash(self._version)

    def __repr__(self):
        ver = ".".join([str(x) for x in self._version[0:3]])
        dev = self._version[3]
        if dev is not None:
            return ver + "." + dev
        return ver

    def __lt__(self, other):
        if self._version[:3] == other._version[:3]:
            # compare dev version.
            # 0.5.1 is newer, or greater, than 0.5.1.devXXX
            if self._dist is None:
                return False
            if other._dist is None:
                return True
            return self._dist < other._dist
        return self._version < other._version


class Record:

    def __init__(self,
                 *,
                 suite,
                 runner,
                 run_at=None,
                 hostname=None,
                 values=None):
        self.suite = suite
        self.runner = runner
        self.run_at = run_at
        self.hostname = hostname
        self._values = values

    def deepcopy(self):
        return Record(suite=Suite(self.suite.name, self.suite.tags),
                      runner=Runner(self.runner.name, self.runner.version,
                                    self.runner.tags),
                      run_at=self.run_at,
                      hostname=self.hostname,
                      values=copy.deepcopy(self._values))

    @property
    def benchmarks(self):
        return list(self._values.keys())

    def value(self, metric, name):
        return self._values[name][metric]

    def get_values_by_metric(self, metric):
        values = {}
        for name, dic in self._values.items():
            values[name] = dic[metric]
        return values

    def get_values_by_bench(self, bench):
        return self._values[bench]

    def add_value(self, name, metric, value):
        if name not in self._values:
            self._values[name] = {}
        self._values[name][metric] = value


def groupby(records, *, key, agg_func=None, sort_func=None):
    assert callable(key)
    grouped = defaultdict(list)
    for record in records:
        grouped[key(record)] += [record]

    sort_func = sort_func or sorted

    result = {}
    for key in sort_func(grouped):
        result[key] = agg_func(grouped[key]) if agg_func else grouped[key]

    return result
