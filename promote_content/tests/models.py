from django.db import models
from django.contrib.contenttypes import generic

from ..models import Curation
from ..managers import CurationManager


class Content(models.Model):
    curation = models.OneToOneField(Curation, null=True, blank=True, on_delete=models.SET_NULL)

    curation = generic.GenericRelation(
        Curation,
        object_id_field="content_id",
        content_type_field="content_type",
    )

    objects = CurationManager()

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.id


class TestContent(Content):
    name = models.CharField(max_length=20)

    def __unicode__(self):
        return self.name


class TestContextTarget(models.Model):
    name = models.CharField(max_length=20)

    def __unicode__(self):
        return self.name
