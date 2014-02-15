from django.db import models
from django.utils.translation import ugettext_lazy as _
from .models import Curation


class CurationField(models.OneToOneField):
    """
    A db field for promote content curation
    """
    description = _("Curation field")
    def __init__(self, to=Curation, to_field=None, on_delete=models.SET_NULL, **kwargs):
        kwargs['null'] = True
        kwargs['blank'] = True
        super(CurationField, self).__init__(to, to_field, on_delete=on_delete, **kwargs)
