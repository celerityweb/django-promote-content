from django.db import models

from ..models import Curation
from ..managers import CurationManager


class Content(models.Model):
    curation = models.OneToOneField(Curation, null=True, blank=True, on_delete=models.SET_NULL)

    objects = CurationManager()

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.id


class TestContent(Content):
    name = models.CharField(max_length=20)

    def __unicode__(self):
        return self.name
