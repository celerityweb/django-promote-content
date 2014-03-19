from django import forms

from django.contrib.contenttypes.generic import GenericRelation
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from .models import Curation


class CurationField(GenericRelation):
    """
    A db field for promote content curation
    """
    description = _("Curation field")
    def __init__(self, to=Curation, **kwargs):
        kwargs['object_id_field'] = kwargs.pop("object_id_field", "content_id")
        kwargs['content_type_field'] = kwargs.pop("content_type_field", "content_type")
        super(CurationField, self).__init__(to, **kwargs)



class CurationsWidget(forms.Widget):
    """
    Form widget for rendering Curations pop up link
    """
    # def __init__(self, attrs=None,
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        return mark_safe(u'<a href="javascript:window.open(\'%s\', \'manage_curations\', \'height=500,width=800,resizable=yes,scrollbars=yes\')">Manage Curations</a>' % reverse('admin:multi_context'))


class Curations(forms.Field):
    widget = CurationsWidget
    validators = []
    initial = ''
    required = False

    def __init__(self, label=None, help_text='', widget=None):
        self.label = label
        self.help_text = help_text
        widget = widget or self.widget
        self.widget = widget()
