from django.contrib.contenttypes.generic import GenericRelation
from django.utils.translation import ugettext_lazy as _

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
