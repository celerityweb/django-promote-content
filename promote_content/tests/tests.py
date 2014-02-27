import datetime
from operator import attrgetter

from django.conf import settings
from django.core.management import call_command
from django.db.models import loading
from django.test import TestCase
from django.utils import timezone

from .models import TestContent, TestContextTarget
from ..models import Curation


class PromoteContentTestsBase(TestCase):
    apps = ('promote_content.tests',)

    def _pre_setup(self):
        # convert INSTALLED_APPS to list, could be tuple
        installed_apps_list = list(settings.INSTALLED_APPS)
        # store original installed apps
        self._original_installed_apps = installed_apps_list
        # append new apps to installed apps
        for app in self.apps:
            installed_apps_list.append(app)
        settings.INSTALLED_APPS = installed_apps_list
        loading.cache.loaded = False
        call_command('syncdb', interactive=False, verbosity=0)
        # Call the original method that does the fixtures etc.
        super(PromoteContentTestsBase, self)._pre_setup()

    def _post_teardown(self):
        super(PromoteContentTestsBase, self)._post_teardown()
        # Restore installed apps to original value
        settings.INSTALLED_APPS = self._original_installed_apps
        loading.cache.loaded = False


class OrderingTests(PromoteContentTestsBase):
    def setUp(self):
        self.c1 = TestContent.objects.create(
            name="Test 1"
        )

        self.c2 = TestContent.objects.create(
            name="Test 2"
        )

        self.c3 = TestContent.objects.create(
            name="Test 3"
        )

        # self.curate1 = Curation.objects.create(weight=1)
        # self.curate2 = Curation.objects.create(weight=2)

    def tearDown(self):
        TestContent.objects.all().delete()
        Curation.objects.all().delete()
        TestContextTarget.objects.all().delete()

    def test_uncurated(self):
        self.assertQuerysetEqual(
            TestContent.objects.all().order_by('id'),
            [
                self.c1.name,
                self.c2.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

    def test_curated_null(self):
        self.assertQuerysetEqual(
            TestContent.objects.curated(),
            [
                self.c1.name,
                self.c2.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

    def test_curated_no_ordering(self):
        c = Curation(content_object=self.c3)
        c.save()
        # self.c3.curation = self.curate1
        # self.c3.save()

        self.assertQuerysetEqual(
            TestContent.objects.curated(),
            [
                self.c3.name,
                self.c1.name,
                self.c2.name,
            ],
            attrgetter("name")
        )

    def test_curated_extra_ordering(self):
        c = Curation(content_object=self.c2)
        c.save()
        # self.c2.curation = self.curate1
        # self.c2.save()

        self.assertQuerysetEqual(
            TestContent.objects.curated().order_by('-id'),
            [
                self.c2.name,
                self.c3.name,
                self.c1.name,
            ],
            attrgetter("name")
        )

        self.assertQuerysetEqual(
            TestContent.objects.curated().order_by('id'),
            [
                self.c2.name,
                self.c1.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

    def test_curated_weights(self):
        c1 = Curation(content_object=self.c2, weight=2)
        c1.save()
        c2 = Curation(content_object=self.c1, weight=1)
        c2.save()
        # self.c2.curation = self.curate2
        # self.c2.save()
        # self.c1.curation = self.curate1
        # self.c1.save()

        self.assertQuerysetEqual(
            TestContent.objects.curated(),
            [
                self.c2.name,
                self.c1.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

    def test_filter_curated(self):
        """
        Specific filters should apply even to promoted objects
        Promotion should still apply to promoted objects still included in qs
        """
        c1 = Curation(content_object=self.c2, weight=1)
        c1.save()
        c2 = Curation(content_object=self.c3, weight=2)
        c2.save()
        # self.c2.curation = self.curate1
        # self.c2.save()
        # self.c3.curation = self.curate2
        # self.c3.save()

        self.assertQuerysetEqual(
            TestContent.objects.exclude(id=self.c2.id).curated(),
            [
                self.c3.name,
                self.c1.name,
            ],
            attrgetter("name")
        )

        self.assertQuerysetEqual(
            TestContent.objects.filter(id__lt=3).curated(),
            [
                self.c2.name,
                self.c1.name,
            ],
            attrgetter("name")
        )

    def test_curated_slice(self):
        c = Curation(content_object=self.c2)
        c.save()
        # self.c2.curation = self.curate1
        # self.c2.save()

        self.assertQuerysetEqual(
            TestContent.objects.curated()[:1],
            [
                self.c2.name,
            ],
            attrgetter("name")
        )

        self.assertQuerysetEqual(
            TestContent.objects.curated()[1:],
            [
                self.c1.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

        self.assertQuerysetEqual(
            TestContent.objects.curated()[1:2],
            [
                self.c1.name,
            ],
            attrgetter("name")
        )

        self.assertQuerysetEqual(
            TestContent.objects.curated()[1:3],
            [
                self.c1.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

        self.assertQuerysetEqual(
            TestContent.objects.curated()[:3],
            [
                self.c2.name,
                self.c1.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

        self.assertQuerysetEqual(
            TestContent.objects.curated()[0:2],
            [
                self.c2.name,
                self.c1.name,
            ],
            attrgetter("name")
        )

        self.assertEqual(
            TestContent.objects.curated()[0].name,
            self.c2.name,
        )

        self.assertEqual(
            TestContent.objects.curated()[1].name,
            self.c1.name,
        )

        self.assertEqual(
            TestContent.objects.curated()[2].name,
            self.c3.name,
        )

    def test_counts(self):
        c = Curation(content_object=self.c2)
        c.save()
        # self.c2.curation = self.curate1
        # self.c2.save()

        # print TestContent.objects.curated()
        # print TestContent.objects.all()
        self.assertEqual(
            TestContent.objects.curated().count(),
            3,
        )

        self.assertEqual(
            TestContent.objects.all().count(),
            3,
        )

    def test_uncurated_len(self):
        self.assertEqual(
            len(TestContent.objects.all()),
            3
        )

    def test_curated_len(self):
        c = Curation(content_object=self.c2)
        c.save()
        # self.c2.curation = self.curate1
        # self.c2.save()

        self.assertEqual(
            len(TestContent.objects.all()),
            len(TestContent.objects.curated())
        )

class CurationStartEndTests(PromoteContentTestsBase):
    def setUp(self):
        self.c1 = TestContent.objects.create(
            name="Test 1"
        )

        self.c2 = TestContent.objects.create(
            name="Test 2"
        )

        self.c3 = TestContent.objects.create(
            name="Test 3"
        )

        # self.curate1 = Curation.objects.create(weight=1)
        # self.curate2 = Curation.objects.create(weight=2)

    def tearDown(self):
        TestContent.objects.all().delete()
        Curation.objects.all().delete()

    def test_past_start(self):
        # set promotion to start yesterday
        now = timezone.now()
        yesterday = now - datetime.timedelta(days=1)
        # self.curate1.start = yesterday
        # self.curate1.save()

        # self.c3.curation = self.curate1
        # self.c3.save()
        c = Curation(content_object=self.c3, start=yesterday)
        c.save()

        self.assertQuerysetEqual(
            TestContent.objects.curated(),
            [
                self.c3.name,
                self.c1.name,
                self.c2.name,
            ],
            attrgetter("name")
        )

    def test_future_start(self):
        # set promotion to start tomorrow
        now = timezone.now() # datetime.datetime.now()
        tomorrow = now + datetime.timedelta(days=1)
        # self.curate1.start = tomorrow
        # self.curate1.save()

        # self.c3.curation = self.curate1
        # self.c3.save()
        c = Curation(content_object=self.c3, start=tomorrow)
        c.save()

        self.assertQuerysetEqual(
            TestContent.objects.curated(),
            [
                self.c1.name,
                self.c2.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

    def test_past_end(self):
        # set promotion to end yesterday
        now = timezone.now()
        yesterday = now - datetime.timedelta(days=1)
        # self.curate1.end = yesterday
        # self.curate1.save()

        # self.c3.curation = self.curate1
        # self.c3.save()
        c = Curation(content_object=self.c3, end=yesterday)
        c.save()

        self.assertQuerysetEqual(
            TestContent.objects.curated(),
            [
                self.c1.name,
                self.c2.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

    def test_future_end(self):
        # set promotion to end tomorrow
        now = timezone.now() # datetime.datetime.now()
        tomorrow = now + datetime.timedelta(days=1)
        # self.curate1.end = tomorrow
        # self.curate1.save()

        # self.c3.curation = self.curate1
        # self.c3.save()
        c = Curation(content_object=self.c3, end=tomorrow)
        c.save()

        self.assertQuerysetEqual(
            TestContent.objects.curated(),
            [
                self.c3.name,
                self.c1.name,
                self.c2.name,
            ],
            attrgetter("name")
        )





class ContextualCurationOrderingTests(PromoteContentTestsBase):
    def setUp(self):
        self.c1 = TestContent.objects.create(
            name="Test 1"
        )

        self.c2 = TestContent.objects.create(
            name="Test 2"
        )

        self.c3 = TestContent.objects.create(
            name="Test 3"
        )

        self.context1 = TestContextTarget.objects.create(name="Context1")
        self.context2 = TestContextTarget.objects.create(name="Context2")

        self.curated_context = Curation.objects.create(
            weight=1,
            context_object=self.context1,
            content_object=self.c2
        )
        # self.curated_context = CurationContext.objects.create(
        #     curation=self.curate1,
        #     context_object=self.context1,
        #     content_object=self.c2
        # )

    def tearDown(self):
        TestContent.objects.all().delete()
        Curation.objects.all().delete()
        TestContextTarget.objects.all().delete()


    def test_contextual_ordering_single(self):
        self.assertQuerysetEqual(
            TestContent.objects.curated(context=self.context1),
            [
                self.c2.name,
                self.c1.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

        self.assertQuerysetEqual(
            TestContent.objects.curated(),
            [
                self.c1.name,
                self.c2.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

    def test_contextual_ordering_multiple(self):
        curated_context2 = Curation.objects.create(
            # curation=self.curate2,
            weight=2,
            context_object=self.context1,
            content_object=self.c3
        )

        self.assertQuerysetEqual(
            TestContent.objects.curated(context=self.context1),
            [
                self.c3.name,
                self.c2.name,
                self.c1.name,
            ],
            attrgetter("name")
        )

        self.assertQuerysetEqual(
            TestContent.objects.curated(),
            [
                self.c1.name,
                self.c2.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

    def test_contextual_ordering_with_other_curation(self):
        # self.c3.curation = self.curate2
        # self.c3.save()
        c = Curation.objects.create(
            weight=2,
            content_object=self.c3
        )

        self.assertQuerysetEqual(
            TestContent.objects.curated(context=self.context1),
            [
                self.c2.name,
                self.c1.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

        self.assertQuerysetEqual(
            TestContent.objects.curated(),
            [
                self.c3.name,
                self.c1.name,
                self.c2.name,
            ],
            attrgetter("name")
        )

    def test_contextual_curated_extra_ordering(self):
        self.assertQuerysetEqual(
            TestContent.objects.curated(context=self.context1).order_by('-id'),
            [
                self.c2.name,
                self.c3.name,
                self.c1.name,
            ],
            attrgetter("name")
        )

        self.assertQuerysetEqual(
            TestContent.objects.curated(context=self.context1).order_by('id'),
            [
                self.c2.name,
                self.c1.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

    def test_contextual_filter_curated(self):
        """
        Specific filters should apply even to promoted objects
        Promotion should still apply to promoted objects still included in qs
        """
        curated_context2 = Curation.objects.create(
            # curation=self.curate2,
            weight=2,
            context_object=self.context1,
            content_object=self.c3
        )

        self.assertQuerysetEqual(
            TestContent.objects.exclude(id=self.c2.id).curated(context=self.context1),
            [
                self.c3.name,
                self.c1.name,
            ],
            attrgetter("name")
        )

        self.assertQuerysetEqual(
            TestContent.objects.filter(id__lt=3).curated(context=self.context1),
            [
                self.c2.name,
                self.c1.name,
            ],
            attrgetter("name")
        )

    def test_contextual_slice_curated_only(self):
        self.assertQuerysetEqual(
            TestContent.objects.curated(context=self.context1)[:1],
            [
                self.c2.name,
            ],
            attrgetter("name")
        )

    def test_contextual_slice_uncurated_only(self):
        self.assertQuerysetEqual(
            TestContent.objects.curated(context=self.context1)[1:],
            [
                self.c1.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

    def test_contextual_slice_partial_uncurated(self):
        self.assertQuerysetEqual(
            TestContent.objects.curated(context=self.context1)[1:2],
            [
                self.c1.name,
            ],
            attrgetter("name")
        )

    def test_contextual_slice_uncurated_only_two_index(self):
        self.assertQuerysetEqual(
            TestContent.objects.curated(context=self.context1)[1:3],
            [
                self.c1.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

    def test_contextual_slice_combined_two_index(self):
        self.assertQuerysetEqual(
            TestContent.objects.curated(context=self.context1)[:3],
            [
                self.c2.name,
                self.c1.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

    def test_contextual_slice_combined_partial_uncurated(self):
        self.assertQuerysetEqual(
            TestContent.objects.curated(context=self.context1)[0:2],
            [
                self.c2.name,
                self.c1.name,
            ],
            attrgetter("name")
        )

    def test_contextual_index_curated(self):
        self.assertEqual(
            TestContent.objects.curated(context=self.context1)[0].name,
            self.c2.name,
        )

    def test_contextual_index_uncurated(self):
        self.assertEqual(
            TestContent.objects.curated(context=self.context1)[1].name,
            self.c1.name,
        )

        self.assertEqual(
            TestContent.objects.curated(context=self.context1)[2].name,
            self.c3.name,
        )

    def test_contextual_slice_mixed_curation(self):
        """
        Adding curation directly to an object outside of any context should not
        affect ordering within a context
        """
        # self.c3.curation = self.curate2
        # self.c3.save()
        c = Curation.objects.create(
            weight=2,
            content_object=self.c3
        )
        self.test_contextual_slice_curated_only()
        self.test_contextual_slice_uncurated_only()
        self.test_contextual_slice_partial_uncurated()
        self.test_contextual_slice_uncurated_only_two_index()
        self.test_contextual_slice_combined_two_index()
        self.test_contextual_slice_combined_partial_uncurated()
        self.test_contextual_index_curated()
        self.test_contextual_index_uncurated()

    def test_contextual_counts(self):
        self.assertEqual(
            TestContent.objects.curated(context=self.context1).count(),
            3,
        )

        self.assertEqual(
            TestContent.objects.all().count(),
            3,
        )

    def test_contextual_uncurated_len(self):
        self.assertEqual(
            len(TestContent.objects.all()),
            3
        )

    def test_contextual_curated_len(self):
        self.assertEqual(
            len(TestContent.objects.all()),
            len(TestContent.objects.curated(context=self.context1))
        )



class ContextualCurationStartEndTests(PromoteContentTestsBase):
    def setUp(self):
        self.c1 = TestContent.objects.create(
            name="Test 1"
        )

        self.c2 = TestContent.objects.create(
            name="Test 2"
        )

        self.c3 = TestContent.objects.create(
            name="Test 3"
        )

        # self.curate1 = Curation.objects.create(weight=1)
        # self.curate2 = Curation.objects.create(weight=2)

        self.context1 = TestContextTarget.objects.create(name="Context1")
        self.context2 = TestContextTarget.objects.create(name="Context2")

        self.curated_context = Curation.objects.create(
            # curation=self.curate1,
            weight=1,
            context_object=self.context1,
            content_object=self.c2
        )

    def tearDown(self):
        TestContent.objects.all().delete()
        Curation.objects.all().delete()
        TestContextTarget.objects.all().delete()

    def test_contextual_past_start(self):
        # set promotion to start yesterday
        now = timezone.now()
        yesterday = now - datetime.timedelta(days=1)
        # self.curate1.start = yesterday
        # self.curate1.save()
        self.curated_context.start = yesterday
        self.curated_context.save()

        self.assertQuerysetEqual(
            TestContent.objects.curated(context=self.context1),
            [
                self.c2.name,
                self.c1.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

    def test_contextual_future_start(self):
        # set promotion to start tomorrow
        now = timezone.now()
        tomorrow = now + datetime.timedelta(days=1)
        # self.curate1.start = tomorrow
        # self.curate1.save()
        self.curated_context.start = tomorrow
        self.curated_context.save()

        self.assertQuerysetEqual(
            TestContent.objects.curated(context=self.context1),
            [
                self.c1.name,
                self.c2.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

    def test_contextual_past_end(self):
        # set promotion to end yesterday
        now = timezone.now()
        yesterday = now - datetime.timedelta(days=1)
        # self.curate1.end = yesterday
        # self.curate1.save()
        self.curated_context.end = yesterday
        self.curated_context.save()

        self.assertQuerysetEqual(
            TestContent.objects.curated(context=self.context1),
            [
                self.c1.name,
                self.c2.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

    def test_contextual_future_end(self):
        # set promotion to end tomorrow
        now = timezone.now()
        tomorrow = now + datetime.timedelta(days=1)
        # self.curate1.end = tomorrow
        # self.curate1.save()
        self.curated_context.end = tomorrow
        self.curated_context.save()

        self.assertQuerysetEqual(
            TestContent.objects.curated(context=self.context1),
            [
                self.c2.name,
                self.c1.name,
                self.c3.name,
            ],
            attrgetter("name")
        )

    def mixed_setup(self):
        non_context_curation = Curation.objects.create(
            weight=3,
            content_object=self.c3
        )

    def test_mixed_curations_past_start(self):
        self.mixed_setup()
        self.test_contextual_past_start()

    def test_mixed_curations_future_start(self):
        self.mixed_setup()
        self.test_contextual_future_start()

    def test_mixed_curations_past_end(self):
        self.mixed_setup()
        self.test_contextual_past_end()

    def test_mixed_curations_future_end(self):
        self.mixed_setup()
        self.test_contextual_future_end()
