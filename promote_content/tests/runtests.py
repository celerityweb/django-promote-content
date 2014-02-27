#! /usr/bin/env python

import sys
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'test_settings'

from django.conf import settings
from django.test.simple import DjangoTestSuiteRunner

test_runner = DjangoTestSuiteRunner(verbosity=1)
failures = test_runner.run_tests(['promote_content', ])
if failures:
    sys.exit(failures)
