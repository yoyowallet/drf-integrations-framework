import csv
import io
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.encoding import force_str
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

from drf_integrations.utils import split_string


def get_json_field():
    try:
        return import_string(settings.DB_BACKEND_JSON_FIELD)
    except ImportError:
        raise ImportError(
            "drf_integrations can only work with a backend that supports JSON fields, "
            "please make sure you set the DB_BACKEND_JSON_FIELD setting to the "
            "JSONField of your backend."
        )


class CommaSeparatedValueField(models.TextField):
    description = "Comma-separated values"

    def __init__(self, deduplicate=True, **kwargs):
        super(CommaSeparatedValueField, self).__init__(**kwargs)
        self.deduplicate = deduplicate

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return split_string(value)

    def to_python(self, value):
        if not value:
            return []
        if type(value) in (list, tuple):
            return value
        if isinstance(value, str):
            value = split_string(value)
            if self.deduplicate:  # Deduplicate values
                value = sorted(set(value))
            return value

        # Neither a string nor a list/tuple
        raise ValidationError(
            _("Enter only values separated by commas."),
            code="invalid",
            params={"value": value},
        )

    def get_prep_value(self, value):
        def _encode(val):
            val = sorted(val)
            output = io.StringIO()
            csv.writer(output, quoting=csv.QUOTE_MINIMAL).writerow(val)
            return output.getvalue().strip()

        if value is None:
            return ""
        if type(value) in (list, tuple):
            return _encode(value)
        if isinstance(value, str):
            try:
                return _encode(self.to_python(value))
            except ValidationError:
                pass
        return ""

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)

    def value_from_object(self, obj):
        # We need an array if we are displaying choices, otherwise convert to string as
        # usual
        if self.choices:
            return getattr(obj, self.attname)
        return self.get_prep_value(getattr(obj, self.attname))

    def validate(self, value, model_instance):
        # Override parent's validate to avoid issues with choices
        if not self.editable:
            # Skip validation for non-editable fields.
            return

        if self.choices and value not in self.empty_values:
            for item in value:
                for option_key, option_value in self.choices:
                    if isinstance(option_value, (list, tuple)):
                        # This is an optgroup, so look inside the group for
                        # options.
                        for optgroup_key, _optgroup_value in option_value:
                            if item == optgroup_key:
                                break
                    elif item == option_key:
                        break
                else:
                    raise ValidationError(
                        self.error_messages["invalid_choice"],
                        code="invalid_choice",
                        params={"value": item},
                    )
            return

        if value is None and not self.null:
            raise ValidationError(self.error_messages["null"], code="null")

        if not self.blank and value in self.empty_values:
            raise ValidationError(self.error_messages["blank"], code="blank")

    def formfield(self, **kwargs):
        kwargs = kwargs or dict()
        if self.choices:
            kwargs["choices_form_class"] = forms.TypedMultipleChoiceField
            kwargs["widget"] = forms.SelectMultiple
            kwargs["coerce"] = lambda value: value
        return super(CommaSeparatedValueField, self).formfield(**kwargs)

    def get_choices(self, *args, **kwargs):
        if args:
            args = (False,) + args[1:]
        kwargs = kwargs or dict()
        # Avoid displaying the empty element, not selecting choices should do it
        kwargs["include_blank"] = False
        return super(CommaSeparatedValueField, self).get_choices(*args, **kwargs)

    def contribute_to_class(self, cls, name, private_only=False):
        super().contribute_to_class(cls, name, private_only=private_only)
        if self.choices:
            # Override the default _get_FIELD_display in the model to be able to
            # fetch more than one value
            def _get_field_display(_self):
                values = getattr(_self, self.attname)
                if not values:
                    # If there are no selected values return None
                    return None

                choices_dict = dict(self.flatchoices)
                return ", ".join(
                    # force_str() to coerce lazy strings.
                    force_str(choices_dict.get(value, value), strings_only=True)
                    for value in values
                )

            setattr(self.model, "get_%s_display" % self.name, _get_field_display)
