from urlparse import urlparse

from django.contrib import admin
from django.conf.urls import patterns, url
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.utils.encoding import force_unicode
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse, resolve
from django.contrib.admin.templatetags.admin_static import static

from .models import Curation

from genericadmin.admin import GenericAdminModelAdmin, GenericTabularInline, GenericStackedInline

from django import forms
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory, inlineformset_factory

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

    def get_urls(self):
        custom_urls = patterns('',
                               url(r'^multi-context/$', self.admin_site.admin_view(self.multi_context), name='multi_context'),
        )
        return custom_urls + super(CurateAdmin, self).get_urls()

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

    def multi_context(self, request, form_url='', extra_context=None):
        opts = self.model._meta
        context_content_type = None
        context_object = None

        if not self.has_add_permission(request) and self.has_change_permission(request):
            raise PermissionDenied

        if request.GET.get('cts', None):
            request.session['content_type_whitelist'] = (request.GET['cts'])

        context_id = request.GET.get('context_id', None)
        context_type = request.GET.get('context_type', None)

        if context_id is not None and context_type is not None:
            CurationFormSet = modelformset_factory(Curation, extra=3, can_delete=True, form=CurateAutoContextForm)
        else:
            CurationFormSet = modelformset_factory(Curation, extra=3, can_delete=True)

        if request.method == "POST":
            formset = CurationFormSet(request.POST, request.FILES)
            if formset.is_valid():
                commit = True

                context_type = request.POST.get('context_type', None)
                context_id = request.POST.get('context_id', None)
                if context_type and context_id:
                    context_content_type = ContentType.objects.get_for_id(context_type)
                    context_object = context_content_type.get_object_for_this_type(pk=context_id)
                    commit = False

                instances = formset.save(commit=commit)

                if not commit:
                    for obj in instances:
                        obj.context_object = context_object
                        obj.save()
                    return self.response_add(request, context_object)
                else:
                    return HttpResponseRedirect(reverse('admin:%s_%s_changelist' %
                                                        (opts.app_label, opts.module_name),
                                                        current_app=self.admin_site.name))
        else:
            if context_id and context_type:
                context_content_type = ContentType.objects.get_for_id(context_type)
                context_object = context_content_type.get_object_for_this_type(pk=context_id)
                formset = CurationFormSet(
                    queryset=Curation.objects.filter(
                        context_type=context_type, context_id=context_id
                    ).order_by('-weight', 'content_type'))
            else:
                formset = CurationFormSet(
                    queryset=Curation.objects.none().order_by('-weight'))

        js = ["inlines.min.js", "calendar.js", "admin/DateTimeShortcuts.js", "collapse.js"]
        media = self.media + forms.Media(js=[static("admin/js/%s" % path) for path in js])

        context = {
            'opts': opts,
            'is_popup': "_popup" in request.REQUEST,
            'media': media,
            'title': _('Add %s') % force_unicode(opts.verbose_name_plural),
            'app_label': opts.app_label,
            'formset':formset,
            'context_type': context_type,
            'context_id': context_id,
            'context_content_type': context_content_type,
            'context_object': context_object,
        }
        context.update(extra_context or {})
        return render(request, "admin/curation/multi_context.html", context)


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

    # hack for supporting multi_context view with formsets
    def get_generic_field_list(self, request, prefix=''):
        view, args, kwargs = resolve(urlparse(request.META['HTTP_REFERER'])[2])
        if view.__name__ == "multi_context":
            prefix = "form"
        field_list = super(CurateAdmin, self).get_generic_field_list(request, prefix)
        return field_list

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
