from typing import Any, Iterable, Iterator, List, Optional, Union

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


def is_instance_of_all(obj, classes: Iterable[type]) -> bool:
    """
    Returns ``True`` if the ``obj`` argument is an instance of all of the
    classes in the ``classes`` argument.

    :raises TypeError: If any element of classes is not a type.
    """
    if any(not isinstance(classinfo, type) for classinfo in classes):
        raise TypeError("classes must contain types")
    return all(isinstance(obj, classinfo) for classinfo in classes)
