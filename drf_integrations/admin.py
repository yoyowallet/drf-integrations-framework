from django.contrib import admin, messages
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlquote
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from drf_integrations import forms, models
from drf_integrations.integrations import Registry


class ApplicationInstallationAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "application",
        models.get_application_installation_install_attribute_name(),
        "config",
        "get_is_active",
    ]
    list_select_related = ["application"]
    form = forms.ApplicationInstallationForm

    def get_is_active(self, obj):
        return not bool(obj.deleted_at)

    get_is_active.boolean = True
    get_is_active.short_description = "Is active"

    def save_model(self, request, obj, form, change):
        obj.deleted_at = None
        super().save_model(request, obj, form, change)

    def render_change_form(self, request, context, *args, **kwargs):
        form = context["adminform"].form

        fieldsets = self.fieldsets or [(None, {"fields": list(form.fields.keys())})]
        adminform = admin.helpers.AdminForm(form, fieldsets, self.prepopulated_fields)
        media = mark_safe(self.media + adminform.media)

        context.update(adminform=adminform, media=media)

        return super().render_change_form(request, context, *args, **kwargs)

    def response_post_save_add(self, request, obj):
        # If an application provides a custom config class, we want to redirect back to
        # the change form so that the user can fill the settings in.
        try:
            has_config_class = obj.application.has_config_class
        except Registry.IntegrationUnavailableException:
            has_config_class = False

        if has_config_class:
            opts = self.model._meta
            preserved_filters = self.get_preserved_filters(request)

            msg_dict = {
                "name": opts.verbose_name,
                "obj": format_html('<a href="{}">{}</a>', urlquote(request.path), obj),
            }
            msg = format_html(
                _(
                    'The {name} "{obj}" was added successfully. '
                    "You may fill in the configuration settings below."
                ),
                **msg_dict,
            )
            self.message_user(request, msg, messages.SUCCESS)
            redirect_url = reverse(
                "admin:%s_%s_change" % (opts.app_label, opts.model_name),
                args=(obj.pk,),
                current_app=self.admin_site.name,
            )
            redirect_url = add_preserved_filters(
                {"preserved_filters": preserved_filters, "opts": opts}, redirect_url
            )
            return HttpResponseRedirect(redirect_url)

        return super().response_post_save_add(request, obj)


ApplicationInstallation = models.get_application_installation_model()

admin.site.register(ApplicationInstallation, ApplicationInstallationAdmin)
