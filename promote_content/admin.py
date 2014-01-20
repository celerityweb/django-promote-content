from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import escape, escapejs
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.db import transaction

from .models import Curation

csrf_protect_m = method_decorator(csrf_protect)


class CurateAdmin(admin.ModelAdmin):
    def dismiss_response(self, pk, obj):
        return HttpResponse(
            '<!DOCTYPE html><html><head><title></title></head><body>'
            '<script type="text/javascript">opener.dismissCurateModify(window, "%s", "%s");</script></body></html>' %
            # escape() calls force_unicode.
            (escape(pk), escapejs(obj)))

    def response_add(self, request, obj, post_url_continue='../%s/'):
        pk_value = obj._get_pk_val()
        return self.dismiss_response(pk_value, obj)

    def response_change(self, request, obj):
        pk_value = obj._get_pk_val()
        return self.dismiss_response(pk_value, obj)

    @csrf_protect_m
    @transaction.commit_on_success
    def delete_view(self, request, object_id, extra_context=None):
        response = super(CurateAdmin, self).delete_view(request, object_id, extra_context)
        if request.POST:
            return HttpResponse(
                '<!DOCTYPE html><html><head><title></title></head><body>'
                '<script type="text/javascript">opener.clearFk(window);</script></body></html>')
        else:
            return response
admin.site.register(Curation, CurateAdmin)


class CuratedAbstractBaseAdmin(admin.ModelAdmin):
    class Media:
        js = ('curate.js',)
