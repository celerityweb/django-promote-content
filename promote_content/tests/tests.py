import datetime
from operator import attrgetter

from django.conf import settings
from django.core.management import call_command
from django.db.models import loading
from django.test import TestCase
from django.utils import timezone

from .models import TestContent
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

        self.curate1 = Curation.objects.create(weight=1)
        self.curate2 = Curation.objects.create(weight=2)

    def tearDown(self):
        TestContent.objects.all().delete()
        Curation.objects.all().delete()

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
        self.c3.curation = self.curate1
        self.c3.save()

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
        self.c2.curation = self.curate1
        self.c2.save()

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
        self.c2.curation = self.curate2
        self.c2.save()
        self.c1.curation = self.curate1
        self.c1.save()

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
        self.c2.curation = self.curate1
        self.c2.save()
        self.c3.curation = self.curate2
        self.c3.save()

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
        self.c1.curation = self.curate1
        self.c1.save()

        self.assertQuerysetEqual(
            TestContent.objects.curated()[:1],
            [
                self.c1.name,
            ],
            attrgetter("name")
        )

        self.assertQuerysetEqual(
            TestContent.objects.curated()[1:],
            [
                self.c2.name,
                self.c3.name,
            ],
            attrgetter("name")
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

        self.curate1 = Curation.objects.create(weight=1)
        self.curate2 = Curation.objects.create(weight=2)

    def tearDown(self):
        TestContent.objects.all().delete()
        Curation.objects.all().delete()

    def test_past_start(self):
        # set promotion to start yesterday
        now = timezone.now() # datetime.datetime.now()
        yesterday = now - datetime.timedelta(days=1)
        self.curate1.start = yesterday
        self.curate1.save()

        self.c3.curation = self.curate1
        self.c3.save()

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
        self.curate1.start = tomorrow
        self.curate1.save()

        self.c3.curation = self.curate1
        self.c3.save()

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
        self.curate1.end = yesterday
        self.curate1.save()

        self.c3.curation = self.curate1
        self.c3.save()

        self.assertQuerysetEqual(
            TestContent.objects.curated(),
            TestContent.objects.all()
            # [
            #     self.c1.name,
            #     self.c2.name,
            #     self.c3.name,
            # ],
            # attrgetter("name")
        )

    def test_future_end(self):
        # set promotion to end tomorrow
        now = timezone.now() # datetime.datetime.now()
        tomorrow = now + datetime.timedelta(days=1)
        self.curate1.end = tomorrow
        self.curate1.save()

        self.c3.curation = self.curate1
        self.c3.save()

        self.assertQuerysetEqual(
            TestContent.objects.curated(),
            [
                self.c3.name,
                self.c1.name,
                self.c2.name,
            ],
            attrgetter("name")
        )
