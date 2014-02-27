from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


class Curation(models.Model):
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    weight = models.IntegerField(default=0)

    context_type = models.ForeignKey(ContentType, null=True, blank=True, related_name="contexts")
    context_id = models.PositiveIntegerField(null=True, blank=True)
    context_object = generic.GenericForeignKey('context_type', 'context_id')

    content_type = models.ForeignKey(ContentType, related_name="content")
    content_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'content_id')

    def __unicode__(self):
        common_str = "Start: %s - End: %s, Weight: %s" % (self.start, self.end, self.weight)
        if self.context_object:
            rel_str = "%s (%s), " % (self.content_object, self.context_object)
        else:
            rel_str = "%s, " % self.content_object
        return rel_str + common_str
