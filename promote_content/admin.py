from django.contrib import admin

from .models import Curation

from genericadmin.admin import GenericAdminModelAdmin, GenericTabularInline, GenericStackedInline


class CurateAdmin(GenericAdminModelAdmin):
    generic_fk_fields = [{
        'ct_field': 'context_type',
        'fk_field': 'context_id',
    },
    {
        'ct_field': 'content_type',
        'fk_field': 'content_id',
    }]
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
