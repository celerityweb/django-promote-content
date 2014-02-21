from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from .managers import CurationManager


class Curation(models.Model):
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    weight = models.IntegerField(default=0)

    def __unicode__(self):
        return "Start: %s - End: %s: Weight %s" % (self.start, self.end, self.weight)



class CurationContext(models.Model):
    curation = models.OneToOneField(Curation)

    context_type = models.ForeignKey(ContentType, related_name="context_type")
    context_id = models.PositiveIntegerField()
    context_object = generic.GenericForeignKey('context_type', 'context_id')

    content_type = models.ForeignKey(ContentType, related_name="content_type")
    content_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'content_id')

    objects = CurationManager()

    def content(self):
        return self.content_object

    def __unicode__(self):
        return "Context: %s, Content: %s" % (self.context_type, self.content_object)

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^promote_content\.fields\.CurationField"])
except:
    pass
