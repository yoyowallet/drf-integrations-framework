from typing import Any, Iterable, Iterator, List, Optional, Union

import pkg_resources

AnyString = Union[str, Iterable[Any]]


def split_string(string: Optional[AnyString], separator: str = ",") -> List[str]:
    """
    Breaks given *string* by the specified *separator*.

    If *string* is a non-``str`` iterable, then return a list if it is not already.

    >>> split_string('A, B, C')  # Str
    ['A', 'B', 'C']

    >>> split_string(['A', 'B', 'C'])  # List, a non-str iterable
    ['A', 'B', 'C']

    >>> split_string(('A', 'B', 'C'))  # Tuple, a non-str iterable
    ['A', 'B', 'C']
    """
    return list(iter_split_string(string=string, separator=separator))


def iter_split_string(string: Optional[AnyString], separator: str = ",") -> Iterator[str]:
    """Generator version of :func:`split_string`."""

    if string is None:
        return

    elif isinstance(string, str):
        parts = str(string).split(separator)
        for part in parts:
            part = part.strip()
            if part:
                yield part

    elif isinstance(string, Iterable):
        # NOTE: Text is also an Iterable, so this should always be after the Text check.
        for part in string:
            part = str(part).strip()
            if part:
                yield part

    else:
        raise TypeError("Cannot split string of {!r}".format(type(string)))


def package_semver(package_name: str):
    version = pkg_resources.get_distribution(package_name).version
    return tuple(map(int, version.split(".")))
