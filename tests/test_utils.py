import pytest
from contextlib import ExitStack as does_not_raise

from drf_integrations import utils


@pytest.mark.parametrize(
    "values",
    [
        " 0,1, 2 , 3   ,4 ",
        ["0", "1", "2", "3", "4"],
        ("0", "1", "2", "3", "4"),
        (str(i) for i in range(5)),
    ],
)
def test_iter_split_string(values):
    result = ["0", "1", "2", "3", "4"]
    for i, j in zip(utils.iter_split_string(values), result):  # noqa B905
        assert i == j


@pytest.mark.parametrize(
    "values",
    [
        " 0,1, 2 , 3   ,4 ",
        ["0", "1", "2", "3", "4"],
        ("0", "1", "2", "3", "4"),
        (str(i) for i in range(5)),
    ],
)
def test_split_string(values):
    assert utils.split_string(values) == ["0", "1", "2", "3", "4"]


@pytest.mark.parametrize(
    "obj,classes,expected,expectation",
    [
        (1, [int], True, does_not_raise()),
        (1, [int, str], False, does_not_raise()),
        (1, [], True, does_not_raise()),
        (1, [1], False, pytest.raises(TypeError)),
    ],
)
def test_is_instance_of_all(obj, classes, expected, expectation):
    with expectation:
        assert utils.is_instance_of_all(obj, classes) == expected
