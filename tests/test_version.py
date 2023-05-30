import pytest
from cbtk.core import Version


def test_parse():
    v = Version.parse("1.2.3.dev4+ghash+dYYYYMMDD")
    assert v.major == 1
    assert v.minor == 2
    assert v.patch == 3


def test_parse_malformed():
    with pytest.raises(ValueError):
        Version.parse("1.2")


def test_parse_malformed_dev():
    with pytest.raises(ValueError):
        Version.parse("1.2.3.dev+g")


def test_is_older_patch_than():
    v0 = Version.parse("1.2.3")
    v1 = Version.parse("1.2.4")
    assert v0.is_older_patch(v1)


def test_is_older_patch_than_same():
    v0 = Version.parse("1.2.3")
    v1 = Version.parse("1.2.3")
    assert not (v0.is_older_patch(v1))


def test_is_older_patch_than_different_minor():
    v0 = Version.parse("1.2.3")
    v1 = Version.parse("1.3.4")
    assert not (v0.is_older_patch(v1))


def test_lt():
    v0 = Version.parse("1.2.3")
    v1 = Version.parse("1.2.4")
    assert v0 < v1


def test_lt_eq():
    v0 = Version.parse("1.2.3")
    v1 = Version.parse("1.2.3")
    assert not (v0 < v1)


def test_lt_dev():
    v0 = Version.parse("1.2.3")
    v1 = Version.parse("1.2.3.dev4")
    assert v0 > v1


def test_lt_devs():
    v0 = Version.parse("1.2.3.dev12")
    v1 = Version.parse("1.2.3.dev4")
    assert v0 > v1


def test_drop_dev():
    v0 = Version.parse("1.2.3")
    v1 = Version.parse("1.2.3.dev4")
    assert v0 != v1
    assert v0 == v1.drop_dev()
