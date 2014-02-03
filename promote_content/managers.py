from django.db import models

from .queryset import CuratedQuerySet


class CurationManager(models.Manager):
    def get_query_set(self):
        return CuratedQuerySet(self.model)

    def __getattr__(self, attr):
        """
        This allows us to set the custom manager on an abstract base class by preventing infinite recursion
        when the manager is copied, as copy calls hasattr(x, '__copy__') (or deepcopy)
        see here: http://bugs.python.org/issue19364
        """
        if attr.startswith('__'):
            raise AttributeError("%r object has no attribute %r" %
                                 (self.__class__, attr))
        return getattr(self.get_query_set(), attr)
