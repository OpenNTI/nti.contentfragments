#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import
__docformat__ = "restructuredtext en"

# pylint:disable=useless-object-inheritance

from hamcrest import assert_that
from hamcrest import is_

from nti.testing.layers import ZopeComponentLayer
from nti.testing.layers import ConfiguringLayerMixin
from nti.testing.matchers import verifiably_provides

import zope.testing.cleanup

class ContentfragmentsTestLayer(ZopeComponentLayer, ConfiguringLayerMixin):

    set_up_packages = ('nti.contentfragments',)

    @classmethod
    def setUp(cls):
        cls.setUpPackages()

    @classmethod
    def tearDown(cls):
        cls.tearDownPackages()
        zope.testing.cleanup.cleanUp()

    @classmethod
    def testSetUp(cls, test=None): # pylint:disable=arguments-differ
        pass

    @classmethod
    def testTearDown(cls):
        pass

import unittest

class ContentfragmentsLayerTest(unittest.TestCase):
    layer = ContentfragmentsTestLayer


class FieldTestsMixin(object):

    def _makeOne(self, *args, **kwargs):
        return self._getTargetClass()(*args, **kwargs)

    def _getTargetClass(self):
        raise NotImplementedError()

    def _getTargetInterface(self):
        raise NotImplementedError()

    def _transform_normalized_for_comparison(self, val):
        return val

    def _transform_raw_for_fromUnicode(self, raw):
        return raw

    def test_implements_interface(self):
        inst = self._makeOne()
        assert_that(inst, verifiably_provides(self._getTargetInterface()))

    def test_fromUnicode_implements_schema(self):
        inst = self._makeOne()
        assert_that(
            inst.fromUnicode(
                self._transform_raw_for_fromUnicode(u'abc')),
            verifiably_provides(inst.schema))

    def test_fromUnicode_normalizes(self):
        import unicodedata
        inst = self._makeOne()
        raw = b'A\xcc\x88O\xcc\x88U\xcc\x88'.decode('utf-8')
        normalized = unicodedata.normalize('NFC', raw)
        self.assertEqual(
            [unicodedata.name(c) for c in raw],
            [
                'LATIN CAPITAL LETTER A',
                'COMBINING DIAERESIS',
                'LATIN CAPITAL LETTER O',
                'COMBINING DIAERESIS',
                'LATIN CAPITAL LETTER U',
                'COMBINING DIAERESIS',
            ]
        )
        assert_that(
            [unicodedata.name(c) for c in normalized],
            is_([
                'LATIN CAPITAL LETTER A WITH DIAERESIS',
                'LATIN CAPITAL LETTER O WITH DIAERESIS',
                'LATIN CAPITAL LETTER U WITH DIAERESIS',
            ])
        )

        fromUnicode = inst.fromUnicode(self._transform_raw_for_fromUnicode(raw))
        self.assertEqual(fromUnicode, self._transform_normalized_for_comparison(normalized))
        assert_that(fromUnicode, verifiably_provides(inst.schema))
