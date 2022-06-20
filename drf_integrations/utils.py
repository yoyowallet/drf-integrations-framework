from typing import Any, Iterable, Iterator, List, Optional, Union

import django
import logging
from django.utils.module_loading import import_string
from environ import Env

AnyString = Union[str, Iterable[Any]]

env = Env()


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


logger = logging.getLogger(__name__)


def get_json_form_field_import_name():
    # if the Django version >= 3.2 then user the new default JSONField
    if django.VERSION[0:2] >= (3, 2):
        default = "django.forms.JSONField"
    else:
        default = "django.contrib.postgres.forms.JSONField"

    # Allow for override
    form_field = env.str("DB_BACKEND_JSON_FORM_FIELD", default)
    logger.info(f"Using django form JSONField: {form_field}")
    return form_field


def get_json_form_field():
    form_field = get_json_form_field_import_name()
    try:
        return import_string(form_field)
    except ImportError:
        raise ImportError(
            "drf_integrations can only work with a backend that supports JSON fields, "
            "please make sure you set the DB_BACKEND_JSON_FORM_FIELD setting to the "
            "JSONField of your backend."
        )


def get_json_model_field_import_name():
    # if the Django version >= 3.2 then user the new default JSONField
    if django.VERSION[0:2] >= (3, 2):
        default = "django.db.models.JSONField"
    else:
        default = "django.contrib.postgres.fields.JSONField"

    # Allow for override
    model_field = env.str("DB_BACKEND_JSON_FIELD", default)
    logger.info(f"Using django model JSONField: {model_field}")
    return model_field


def get_json_model_field():
    model_field = get_json_model_field_import_name()
    try:
        return import_string(model_field)
    except ImportError:
        raise ImportError(
            "drf_integrations can only work with a backend that supports JSON fields, "
            "please make sure you set the DB_BACKEND_JSON_FIELD setting to the "
            "JSONField of your backend."
        )
