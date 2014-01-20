from django.db import models


class Curation(models.Model):
    start = models.DateTimeField(null=True, blank=True)
    end = models.DateTimeField(null=True, blank=True)
    weight = models.IntegerField(default=0)

    def __unicode__(self):
        return "Start: %s - End: %s: Weight %s" % (self.start, self.end, self.weight)
