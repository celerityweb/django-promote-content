import itertools

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

    def __getitem__(self, k):
        """
        Retrieves an item or slice from the set of results.
        """
        if not isinstance(k, (slice, int, long)):
            raise TypeError
        assert ((not isinstance(k, slice) and (k >= 0))
                or (isinstance(k, slice) and (k.start is None or k.start >= 0)
                    and (k.stop is None or k.stop >= 0))), \
                "Negative indexing is not supported."

        if self._result_cache is not None:
            if self._iter is not None:
                # The result cache has only been partially populated, so we may
                # need to fill it out a bit more.
                if isinstance(k, slice):
                    if k.stop is not None:
                        # Some people insist on passing in strings here.
                        bound = int(k.stop)
                    else:
                        bound = None
                else:
                    bound = k + 1
                if len(self._result_cache) < bound:
                    self._fill_cache(bound - len(self._result_cache))
            return self._result_cache[k]

        if isinstance(k, slice):
            qs = self._clone()
            if k.start is not None:
                start = int(k.start)
            else:
                start = None
            if k.stop is not None:
                stop = int(k.stop)
            else:
                stop = None
            if qs._is_curated:
                curated_length = qs._curated_qs.count()
                if start <= curated_length or start is None:
                    qs._curated_qs.query.set_limits(start, stop)
                    start = 0
                if stop > curated_length or stop is None:
                    if stop is not None:
                        stop = stop - curated_length
                    qs.query.set_limits(start, stop)
                else:
                    qs = qs._curated_qs
            else:
                qs.query.set_limits(start, stop)
            return k.step and list(qs)[::k.step] or qs
        try:
            qs = self._clone()
            if qs._is_curated:
                curated_length = len(qs._curated_qs)
                if k >= curated_length:
                    k = k - curated_length
                    qs.query.set_limits(k, k + 1)
                    # set false here to prevent the two from being concatenated when calling list(qs)
                    qs._is_curated = False
                else:
                    qs._curated_qs.query.set_limits(k, k + 1)
                    qs = qs._curated_qs
            else:
                qs.query.set_limits(k, k + 1)
            return list(qs)[0]
        except self.model.DoesNotExist, e:
            raise IndexError(e.args)

    def count(self):
        """
        Performs a SELECT COUNT() and returns the number of records as an
        integer.

        If the QuerySet is already fully cached this simply returns the length
        of the cached results set to avoid multiple SELECT COUNT(*) calls.
        """
        if self._result_cache is not None and not self._iter:
            return len(self._result_cache)

        count = self.query.get_count(using=self.db)

        if self._is_curated:
            curated = self._curated_qs.query.get_count(using=self.db)
            count += curated

        return count

    def reverse(self):
        """
        Reverses the ordering of the QuerySet.
        """
        if self._is_curated:
            raise NotImplementedError("Reverse is not implemented on curated querysets")
        else:
            return super(CuratedQuerySet, self).reverse()
