from setuptools import setup

import promote_content

setup(
    name='django-promote-content',
    version=promote_content.__version__,
    packages=['promote_content'],
    url='https://github.com/celerityweb/django-promote-content/',
    license='LGPL v3 - see LICENSE file',
    author='Tosh Lyons',
    author_email='tlyons@celerity.com',
    description='The django-promote-content app allows you to curate '
                'promoted content among Model objects in a queryset, '
                'elevating them to the top of any sort order',
    long_description=open('README.rst').read(),
)
