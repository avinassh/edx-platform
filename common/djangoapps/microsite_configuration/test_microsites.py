# -*- coding: utf-8 -*-
"""
Tests microsite_configuration templatetags and helper functions.
"""
from django.test import TestCase
from django.conf import settings
from .templatetags import microsite_templatetags


class MicroSiteTests(TestCase):
    def test_breadcrumbs(self):
        crumbs = ['my', 'less specific', 'Page']
        expected = u'my | less specific | Page | edX'
        title = microsite_templatetags.page_title_breadcrumbs(*crumbs)
        self.assertEqual(expected, title)

    def test_unicode_title(self):
        crumbs = [u'øo', u'π tastes gréât', u'驴']
        expected = u'øo | π tastes gréât | 驴 | edX'
        title = microsite_templatetags.page_title_breadcrumbs(*crumbs)
        self.assertEqual(expected, title)

    def test_platform_name(self):
        pname = microsite_templatetags.platform_name()
        self.assertEqual(pname, settings.PLATFORM_NAME)

    def test_breadcrumb_tag(self):
        crumbs = ['my', 'less specific', 'Page']
        expected = u'my | less specific | Page | edX'
        title = microsite_templatetags.page_title_breadcrumbs_tag(None, *crumbs)
        self.assertEqual(expected, title)

