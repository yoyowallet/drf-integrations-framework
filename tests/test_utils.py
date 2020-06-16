import pytest

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
    for i, j in zip(utils.iter_split_string(values), result):
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
