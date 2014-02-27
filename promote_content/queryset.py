import itertools

from django.db.models.query import QuerySet
from django.db.models import Q
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from .models import Curation


class CuratedQuerySet(QuerySet):
    """
    Custom query set to support chainable object curation
    """

    def __init__(self, model=None, query=None, using=None):
        super(CuratedQuerySet, self).__init__(model, query, using)
        self._is_curated = False
        self._is_contextual = False
        self._curated_qs = []

    def _clone(self, klass=None, setup=False, **kwargs):
        c = super(CuratedQuerySet, self)._clone(klass=klass, setup=setup, **kwargs)
        # persist _is_curated through cloning
        c._is_curated = self._is_curated
        c._curated_qs = self._curated_qs
        return c

    def _get_genericrelation_to(self, model, target):
        gen_rels = model._meta.get_m2m_with_model()
        for gen_rel in gen_rels:
            if gen_rel[0].rel.to == target:
                return gen_rel[0].name

    def curated(self, context=None):
        """
        Returns a queryset of instances
        """
        assert self.query.can_filter(), \
            "Cannot reorder a query once a slice has been taken."

        now = timezone.now()

        curation_rel = self._get_genericrelation_to(self.model, Curation)

        start_lte = {"%s__start__lte" % curation_rel: now}
        start_null = {"%s__start__isnull" % curation_rel: True}
        end_gte = {"%s__end__gte" % curation_rel: now}
        end_null = {"%s__end__isnull" % curation_rel: True}

        start_filter = Q(**start_lte) | Q(**start_null)
        end_filter = Q(**end_gte) | Q(**end_null)

        curated = self.filter(start_filter, end_filter)

        if context is not None:
            # only include curation for supplied context
            context_filter = {
                "%s__context_type" % curation_rel: ContentType.objects.get_for_model(context),
                "%s__context_id" % curation_rel: context.id
            }
            curated = curated.filter(**context_filter)
            uncurated_qs = self.filter(
                ~Q(**context_filter) |
                ~Q(start_filter) |
                ~Q(end_filter)
            )
        else:
            # exclude curation that are applied to a particular context
            no_context_filter = {
                "%s__context_type__isnull" % curation_rel: False
            }
            curated = curated.exclude(**no_context_filter)
            uncurated_qs = self.filter(
                ~Q(**{"%s__isnull" % curation_rel: False}) |
                ~Q(start_filter) |
                ~Q(end_filter) |
                Q(**no_context_filter)
            )

        # order by curation weight first but respect other ordering
        # ordering priority taken from django.db.models.sql.compiler.get_ordering
        if curated.query.extra_order_by:
            ordering = curated.query.extra_order_by
        elif not curated.query.default_ordering:
            ordering = curated.query.order_by
        else:
            ordering = (curated.query.order_by
                        or curated.query.model._meta.ordering
                        or [])

        ordering.insert(0, "-%s__weight" % curation_rel)
        curated.query.clear_ordering()
        curated.query.order_by = ordering

        uncurated_qs._curated_qs = curated

        uncurated_qs._is_curated = True

        return uncurated_qs

    def __len__(self):
        if self._is_curated:
            return super(CuratedQuerySet, self._curated_qs).__len__() + super(CuratedQuerySet, self).__len__()
        return super(CuratedQuerySet, self).__len__()

    def __iter__(self):
        """
        Custom method to support curated querysets
        """
        if self._is_curated and self._result_cache is None:
            return itertools.chain(
                super(CuratedQuerySet, self._curated_qs).__iter__(),
                super(CuratedQuerySet, self).__iter__()
            )
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
                    uncurated_start = start - curated_length
                    if uncurated_start < 0:
                        uncurated_start = 0
                else:
                    start = None
                    uncurated_start = None

                if k.stop is not None:
                    stop = int(k.stop)
                    uncurated_stop = stop - curated_length
                else:
                    stop = None
                    uncurated_stop = None

                # slice falls completely in curated queryset
                if stop <= curated_length and stop is not None:
                    return super(CuratedQuerySet, self._curated_qs).__getitem__(k)

                # slice for uncurated qs
                uncurated_k = slice(uncurated_start, uncurated_stop, k.step)

                # slice falls completely in uncurated queryset
                if start >= curated_length:
                    return super(CuratedQuerySet, qs).__getitem__(uncurated_k)

                # slice spans curated and non-curated querysets
                return itertools.chain(
                    super(CuratedQuerySet, self._curated_qs).__getitem__(k),
                    super(CuratedQuerySet, qs).__getitem__(uncurated_k))
            else:
                if k >= curated_length:
                    k = k - curated_length
                    return super(CuratedQuerySet, qs).__getitem__(k)
                else:
                    return super(CuratedQuerySet, self._curated_qs).__getitem__(k)

    def count(self):
        """
        Return combined count for curated querysets
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
