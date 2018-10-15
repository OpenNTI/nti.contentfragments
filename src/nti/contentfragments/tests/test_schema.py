# -*- coding: utf-8 -*-
"""
Tests for schema.py

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest

from hamcrest import assert_that
from hamcrest import has_key
from hamcrest import has_entries

from zope.dottedname import resolve as dottedname

from nti.contentfragments.tests import FieldTestsMixin

def _make_test_class(kind_name):

    iface = dottedname.resolve('nti.contentfragments.interfaces.I' + kind_name + 'Field')
    kind = dottedname.resolve('nti.contentfragments.schema.' + kind_name)

    def getTargetClass(self): # pylint:disable=unused-argument
        return kind

    def getTargetInterface(self): # pylint:disable=unused-argument
        return iface

    test = type(
        'Test' + kind_name,
        (unittest.TestCase, FieldTestsMixin),
        {'_getTargetClass': getTargetClass, '_getTargetInterface': getTargetInterface}
    )
    return test


TestTextUnicodeContentFragment = _make_test_class('TextUnicodeContentFragment')
TestTextLineUnicodeContentFragment = _make_test_class('TextLineUnicodeContentFragment')
TestLatexFragmentTextLine = _make_test_class('LatexFragmentTextLine')
TestPlainTextLine = _make_test_class('PlainTextLine')
TestHTMLContentFragment = _make_test_class('HTMLContentFragment')
TestSanitizedHTMLContentFragment = _make_test_class('SanitizedHTMLContentFragment')
TestPlainText = _make_test_class('PlainText')
TestTag = _make_test_class('Tag')


class TestTitle(unittest.TestCase, FieldTestsMixin):

    def _getTargetInterface(self):
        from nti.contentfragments.interfaces import IPlainTextLineField
        return IPlainTextLineField

    def _getTargetClass(self):
        from nti.contentfragments.schema import Title
        return Title

    def test_schema(self):
        from zope.interface import Interface
        from nti.schema.jsonschema import JsonSchemafier

        class IFoo(Interface): # pylint:disable=inherit-non-class
            title = self._makeOne()

        schema = JsonSchemafier(IFoo).make_schema()
        assert_that(schema, has_key('title'))

        assert_that(schema['title'],
                    has_entries(name=u'title', max_length=140, min_length=0))
