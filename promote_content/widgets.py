from django.forms.widgets import Input
from django.core.urlresolvers import reverse
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.forms.util import flatatt
from django.utils.encoding import force_unicode
from django.template import Context


class CurateWidget(Input):
    input_type = "hidden"

    def get_admin_url(self, klass, action, args=[]):
        return reverse('admin:%s_%s_%s' % (klass._meta.app_label, klass._meta.module_name, action), args=args)

    def render(self, name, value, attrs=None):
        instance = self.form_instance.instance

        Curation = instance._meta.get_field(name).rel.to

        final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)

        if value is not None:
            final_attrs['value'] = force_unicode(self._format_value(value))

        add_url = self.get_admin_url(Curation, 'add')
        change_url = self.get_admin_url(Curation, 'change', args=[value])
        delete_url = self.get_admin_url(Curation, 'delete', args=[value])

        try:
            curation_obj = Curation._default_manager.get(pk=value)
        except Curation.DoesNotExist:
            value = ''
        else:
            value = "%s" % curation_obj

        c = Context(
            {
                'final_attrs': mark_safe(flatatt(final_attrs)),
                'add_url': add_url,
                'change_url': change_url,
                'delete_url': delete_url,
                'value': value,
                'name': name,
            }
        )
        t = get_template('promote_content/field.html')
        return t.render(c)
