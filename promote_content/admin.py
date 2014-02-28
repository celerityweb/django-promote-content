from django.contrib import admin

from .models import Curation

from genericadmin.admin import GenericAdminModelAdmin, GenericTabularInline


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


class CurateContentInline(GenericTabularInline):
    model = Curation
    ct_field = 'content_type'
    ct_fk_field = 'content_id'


class CurateContextInline(GenericTabularInline):
    model = Curation
    ct_field = 'context_type'
    ct_fk_field = 'context_id'
