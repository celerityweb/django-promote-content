from django.contrib import admin

from .models import Curation

from genericadmin.admin import GenericAdminModelAdmin, GenericTabularInline, GenericStackedInline

# TODO move form to forms.py
from django import forms
class CurateAutoContextForm(forms.ModelForm):
    class Meta:
        model = Curation
        exclude = ['context_id', 'context_type', ]

# imports for genericadmin_js_init
from django.contrib.contenttypes.models import ContentType
try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text
from django.contrib.admin.widgets import url_params_from_lookup_dict
try:
    from django.contrib.admin.views.main import IS_POPUP_VAR
except ImportError:
    from django.contrib.admin.options import IS_POPUP_VAR
import json
from django.http import HttpResponse

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
        if request.GET.get('cts', None):
            request.session['content_type_whitelist'] = (request.GET['cts'])

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
            request.session.pop('content_type_whitelist')

    def get_form(self, request, obj=None, **kwargs):
        if request.session.get('_for_context', None):
            form = CurateAutoContextForm
        else:
            form = super(CurateAdmin, self).get_form(request, obj, **kwargs)
        return form

    # hackey fix for overridding/setting content_type_whitelist per request
    def genericadmin_js_init(self, request):
        if request.method == 'GET':
            obj_dict = {}
            for c in ContentType.objects.all():
                val = force_text('%s/%s' % (c.app_label, c.model))
                params = self.content_type_lookups.get('%s.%s' % (c.app_label, c.model), {})
                params = url_params_from_lookup_dict(params)
                whitelist = None
                if request.session.get('content_type_whitelist', None):
                    whitelist = request.session['content_type_whitelist']
                elif self.content_type_whitelist:
                    whitelist = self.content_type_whitelist

                if whitelist:
                    if val in whitelist:
                        obj_dict[c.id] = (val, params)
                elif val not in self.content_type_blacklist:
                    obj_dict[c.id] = (val, params)

            data = {
                'url_array': obj_dict,
                'fields': self.get_generic_field_list(request),
                'popup_var': IS_POPUP_VAR,
            }
            resp = json.dumps(data, ensure_ascii=False)
            return HttpResponse(resp, mimetype='application/json')
        return HttpResponseNotAllowed(['GET'])

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
