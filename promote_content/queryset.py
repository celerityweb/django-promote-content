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

        uncurated_qs = self.filter(Q(curation__isnull=True) | Q(curation__start__gt=now) | Q(curation__end__lt=now))

        curated = self.filter(curation__isnull=False).filter(
            Q(curation__start__lte=now) | Q(curation__start__isnull=True)
        ).filter(
            Q(curation__end__gte=now) | Q(curation__end__isnull=True)
        )

        # order by curation weight first, but respect other ordering
        curated.query.order_by[:0] = ['-curation__weight']

        uncurated_qs._curated_qs = curated

        uncurated_qs._is_curated = True

        return uncurated_qs

    def __iter__(self):
        """
        Custom method to support curated querysets
        """
        if self._is_curated and self._result_cache is None:
            self._iter = itertools.chain(
                super(CuratedQuerySet, self._curated_qs).iterator(),
                super(CuratedQuerySet, self).iterator()
            )
            self._result_cache = []
            return self._result_iter()
        else:
            return super(CuratedQuerySet, self).__iter__()

    def __getitem__(self, k):
        """
        Retrieves an item or slice from the set of results.
        """
        if not self._is_curated:
            return super(CuratedQuerySet, self).__getitem__(k)
        else:
            curated_length = len(self._curated_qs)
            # set _is_curated to false so we can work with
            # the querysets independently
            qs = self._clone()
            qs._is_curated = False
            if isinstance(k, slice):
                if k.start is not None:
                    start = int(k.start)
                    non_start = start - curated_length
                    if non_start < 0:
                        non_start = 0
                else:
                    start = None
                    non_start = None

                if k.stop is not None:
                    stop = int(k.stop)
                    non_stop = stop - curated_length
                else:
                    stop = None
                    non_stop = None

                # slice falls completely in curated queryset
                if stop <= curated_length and stop is not None:
                    return super(CuratedQuerySet, self._curated_qs).__getitem__(k)

                # slice for non curated qs
                non_k = slice(non_start, non_stop, k.step)

                # slice falls completely in non curated queryset
                if start >= curated_length:
                    return super(CuratedQuerySet, qs).__getitem__(non_k)

                # slice spans curated and non-curated querysets
                return itertools.chain(
                    super(CuratedQuerySet, self._curated_qs).__getitem__(k),
                    super(CuratedQuerySet, qs).__getitem__(non_k))
            else:
                if k >= curated_length:
                    k = k - curated_length
                    return super(CuratedQuerySet, qs).__getitem__(k)
                else:
                    return super(CuratedQuerySet, self._curated_qs).__getitem__(k)

    def count(self):
        """
        Performs a SELECT COUNT() and returns the number of records as an
        integer.

        If the QuerySet is already fully cached this simply returns the length
        of the cached results set to avoid multiple SELECT COUNT(*) calls.
        """
        if self._is_curated:
            return super(CuratedQuerySet, self._curated_qs).count() + super(CuratedQuerySet, self).count()
        else:
            return super(CuratedQuerySet, self).count()

    def reverse(self):
        """
        Reverses the ordering of the QuerySet.
        """
        if self._is_curated:
            raise NotImplementedError("Reverse is not implemented on curated querysets")
        else:
            return super(CuratedQuerySet, self).reverse()
