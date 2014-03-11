from django.contrib import admin

from .models import Curation

from genericadmin.admin import GenericAdminModelAdmin, GenericTabularInline, GenericStackedInline

# TODO move form to forms.py
from django import forms
class CurateAutoContextForm(forms.ModelForm):
    class Meta:
        model = Curation
        exclude = ['context_id', 'context_type', ]


class CurateAdmin(GenericAdminModelAdmin):
    generic_fk_fields = [{
        'ct_field': 'context_type',
        'fk_field': 'context_id',
    },
    {
        'ct_field': 'content_type',
        'fk_field': 'content_id',
    }]

    def add_view(self, request, form_url='', extra_context=None):
        # Calling add_view with a querystring of the form ?context_type=34&context_id=152&_popup=1
        # will result in a form with context related fields hidden. They will be automatically
        # set to the ids in the querystring
        if request.GET.get('context_id', None) and request.GET.get('context_type', None):
            request.session['_for_context'] = True
            request.session['context_id'] = request.GET['context_id']
            request.session['context_type'] = request.GET['context_type']
        return super(CurateAdmin, self).add_view(request, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if type(form) == CurateAutoContextForm:
            obj.context_type_id = request.session.get('context_type', None)
            obj.context_id = request.session.get('context_id', None)
        obj.save()
        if not request.POST.get('_continue', None):
            request.session.pop('_for_context')
            request.session.pop('context_type')
            request.session.pop('context_id')

    def get_form(self, request, obj=None, **kwargs):
        if request.session.get('_for_context', None):
            form = CurateAutoContextForm
        else:
            form = super(CurateAdmin, self).get_form(request, obj, **kwargs)
        return form

admin.site.register(Curation, CurateAdmin)


class CurateContentBase(object):
    model = Curation
    ct_field = 'content_type'
    ct_fk_field = 'content_id'


class CurateContextBase(object):
    model = Curation
    ct_field = 'context_type'
    ct_fk_field = 'context_id'


class CurateContentTabularInline(CurateContentBase, GenericTabularInline):
    pass


class CurateContextTabularInline(CurateContextBase, GenericTabularInline):
    pass


class CurateContentStackedInline(CurateContentBase, GenericStackedInline):
    pass


class CurateContextStackedInline(CurateContextBase, GenericStackedInline):
    pass
