# -*- coding: utf-8 -*-
"""
Tests for schema.py

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


from hamcrest import assert_that
from hamcrest import has_key
from hamcrest import has_entries
from hamcrest import is_

from zope.dottedname import resolve as dottedname

from nti.testing.matchers import validly_provides
from nti.testing.matchers import is_false


from nti.contentfragments.tests import FieldTestsMixin
from . import ContentfragmentsLayerTest

def _make_test_class(kind_name, iface_name=None):
    if not iface_name:
        iface_name = 'I' + kind_name + 'Field'
    iface_name = 'nti.contentfragments.interfaces.' + iface_name

    iface = dottedname.resolve(iface_name)
    kind = dottedname.resolve('nti.contentfragments.schema.' + kind_name)

    class T(FieldTestsMixin, ContentfragmentsLayerTest):
        def _getTargetClass(self): # pylint:disable=unused-argument
            return kind

        def _getTargetInterface(self): # pylint:disable=unused-argument
            return iface

    T.__name__ = 'Test' + kind_name
    T.__qualname__ = __name__ + '.' + T.__name__
    return T


class TestTextUnicodeContentFragment(_make_test_class('TextUnicodeContentFragment')):
    def test_defaults(self):
        t = self._makeOne(default=u'abc')
        assert_that(t.default, validly_provides(t.schema))
        assert_that(t.fromUnicode(t.default), is_(t.default))

TestTextLineUnicodeContentFragment = _make_test_class('TextLineUnicodeContentFragment')
TestLatexFragmentTextLine = _make_test_class('LatexFragmentTextLine')
TestPlainTextLine = _make_test_class('PlainTextLine')
TestHTMLContentFragment = _make_test_class('HTMLContentFragment')


class TestSanitizedHTMLContentFragment(_make_test_class('SanitizedHTMLContentFragment')):
    def _transform_raw_for_fromUnicode(self, raw):
        result = u'<p>' + raw + '</p>'
        return result

    def _transform_normalized_for_comparison(self, val):
        return u"<html><body>" + self._transform_raw_for_fromUnicode(val) + u'</body></html>'


TestPlainText = _make_test_class('PlainText')

class TestTag(_make_test_class('Tag')):

    _transform_normalized_for_comparison = staticmethod(type(u'').lower)

    def test_constraint(self):
        t = self._makeOne()
        assert_that(t.fromUnicode(u"HI"), is_(u'hi'))
        assert_that(t.constraint(u"oh hi"), is_false())


class TestTitle(_make_test_class('Title', 'IPlainTextLineField')):

    def test_schema(self):
        from zope.interface import Interface
        from nti.schema.jsonschema import JsonSchemafier

        class IFoo(Interface): # pylint:disable=inherit-non-class,too-many-ancestors
            title = self._makeOne()

        schema = JsonSchemafier(IFoo).make_schema()
        assert_that(schema, has_key('title'))

        assert_that(schema['title'],
                    has_entries(name=u'title', max_length=140, min_length=0))
