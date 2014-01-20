import datetime

from django.db import models
from django.db.models.query import QuerySet
from django.db.models import Q
from django.utils import timezone


class CuratedQuerySet(QuerySet):
    """
    Custom query set to support chainable object curation
    """

    def __init__(self, model=None, query=None, using=None):
        super(CuratedQuerySet, self).__init__(model, query, using)
        self._is_curated = False

    def _clone(self, klass=None, setup=False, **kwargs):
        c = super(CuratedQuerySet, self)._clone(klass=klass, setup=setup, **kwargs)
        # persist _is_curated through cloning
        c._is_curated = self._is_curated
        return c

    def curated(self):
        """
        Returns a new QuerySet instance ordered by curation
        """
        now = timezone.now()  # datetime.datetime.now()
        assert self.query.can_filter(), \
                "Cannot reorder a query once a slice has been taken."
        self.filter(
            Q(curation__start__lte=now) | Q(curation__start__isnull=True)
        ).filter(
            Q(curation__end__gte=now) | Q(curation__end__isnull=True)
        )
        obj = self._clone()
        obj.query.clear_ordering()
        obj.query.add_ordering('-curation__weight')

        # set flag to denote queryset is curated
        obj._is_curated = True

        return obj

    def _curated_set(self):
        """
        Returns curated queryset containing only curated objects
        """
        return self.curated().filter(curation__isnull=False)

    def order_by(self, *field_names):
        """
        Returns a new QuerySet instance with the ordering changed.
        """
        assert self.query.can_filter(), \
                "Cannot reorder a query once a slice has been taken."
        obj = self._clone()
        obj.query.clear_ordering()

        # if queryset is curated
        if obj._is_curated:
            obj.query.add_ordering('-curation__weight', *field_names)
            curated = self._curated_set()
            combined = curated | obj
            obj = combined
        else:
            obj.query.add_ordering(*field_names)

        return obj


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
