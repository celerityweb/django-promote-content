import itertools

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
        self._curated_qs = []

    def _clone(self, klass=None, setup=False, **kwargs):
        c = super(CuratedQuerySet, self)._clone(klass=klass, setup=setup, **kwargs)
        # persist _is_curated through cloning
        c._is_curated = self._is_curated
        c._curated_qs = self._curated_qs
        return c

    def curated(self):
        """
        Returns a queryset of instances
        """
        assert self.query.can_filter(), \
            "Cannot reorder a query once a slice has been taken."

        now = timezone.now()

        obj = self._clone().filter(Q(curation__isnull=True) | Q(curation__start__gt=now) | Q(curation__end__lt=now))

        curated = self._clone()
        curated = curated.filter(curation__isnull=False)

        curated = curated.filter(Q(curation__start__lte=now) | Q(curation__start__isnull=True))
        curated = curated.filter(Q(curation__end__gte=now) | Q(curation__end__isnull=True))

        curated.query.clear_ordering()
        curated.query.add_ordering('-curation__weight')

        obj._curated_qs = curated

        obj._is_curated = True

        return obj

    def __iter__(self):
        """
        Custom method to support curated querysets
        """
        if self._prefetch_related_lookups and not self._prefetch_done:
            # We need all the results in order to be able to do the prefetch
            # in one go. To minimize code duplication, we use the __len__
            # code path which also forces this, and also does the prefetch
            len(self)

        if self._result_cache is None:
            # if this queryset has been curated
            if self._is_curated:
                # return an iterator for both curated and non curated querysets
                self._iter = itertools.chain(super(CuratedQuerySet, self._curated_qs).iterator(), self.iterator())
            else:
                self._iter = self.iterator()
            self._result_cache = []
        if self._iter:
            return self._result_iter()
        # Python's list iterator is better than our version when we're just
        # iterating over the cache.
        return iter(self._result_cache)


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
