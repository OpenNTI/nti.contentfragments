# -*- coding: utf-8 -*-
"""
Tests for schema.py

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


from hamcrest import assert_that
from hamcrest import calling
from hamcrest import has_key
from hamcrest import has_entries
from hamcrest import is_
from hamcrest import raises

from zope.dottedname import resolve as dottedname

from nti.schema.interfaces import InvalidValue

from nti.testing.matchers import validly_provides
from nti.testing.matchers import is_false

from nti.contentfragments.interfaces import IPlainTextContentFragment
from nti.contentfragments.interfaces import ISanitizedHTMLContentFragment
from nti.contentfragments.tests import FieldTestsMixin
from . import ContentfragmentsLayerTest

def _make_test_class(kind_name, iface_name=None, base=FieldTestsMixin):
    if not iface_name:
        iface_name = 'I' + kind_name + 'Field'
    iface_name = 'nti.contentfragments.interfaces.' + iface_name

    iface = dottedname.resolve(iface_name)
    kind = dottedname.resolve('nti.contentfragments.schema.' + kind_name)

    assert issubclass(base, FieldTestsMixin)

    class T(base, ContentfragmentsLayerTest):
        def _getTargetClass(self): # pylint:disable=unused-argument
            return kind

        def _getTargetInterface(self): # pylint:disable=unused-argument
            return iface

    T.__name__ = 'Test' + kind_name
    T.__qualname__ = __name__ + '.' + T.__name__
    return T


class _FieldDoesConversionTestsMixin(FieldTestsMixin): # pylint:disable=abstract-method
    """
    For classes that automatically do HTML -> SanitizedHTML or
    PlainText conversion.
    """

    fdctm_invalid_html = u'<div><a onclick="window.location=\'http://google.com\'">Hi there!</a></div>'
    fdctm_sanitized_text = u'<html><body><a>Hi there!</a></body></html>'
    fdctm_sanitize_to = ISanitizedHTMLContentFragment

    def test_invalid_html_sanitizes(self):
        t = self._makeOne()

        result = t.fromUnicode(self.fdctm_invalid_html)
        assert_that(result, validly_provides(self.fdctm_sanitize_to))
        assert_that(result, validly_provides(t.schema))
        assert_that(result, is_(self.fdctm_sanitized_text))

    def test_simple_html_to_plain_text(self):
        t = self._makeOne()
        result = t.fromUnicode(u'<div>goody</div>')
        assert_that(result, validly_provides(IPlainTextContentFragment))
        assert_that(result, validly_provides(t.schema))
        assert_that(result, is_(u'goody'))


class TestTextUnicodeContentFragment(_make_test_class('TextUnicodeContentFragment',
                                                      base=_FieldDoesConversionTestsMixin)):
    def test_defaults(self):
        t = self._makeOne(default=u'abc')
        assert_that(t.default, validly_provides(t.schema))
        assert_that(t.fromUnicode(t.default), is_(t.default))

TestTextLineUnicodeContentFragment = _make_test_class('TextLineUnicodeContentFragment',
                                                      base=_FieldDoesConversionTestsMixin)
TestLatexFragmentTextLine = _make_test_class('LatexFragmentTextLine')
TestPlainTextLine = _make_test_class('PlainTextLine',
                                     base=_FieldDoesConversionTestsMixin)
TestPlainTextLine.fdctm_sanitize_to = IPlainTextContentFragment
TestPlainTextLine.fdctm_sanitized_text = u"Hi there!"
TestHTMLContentFragment = _make_test_class('HTMLContentFragment')


class TestRstContentFragment(_make_test_class('RstContentFragment')):

    def test_invalid_rst(self):
        fragment = self._makeOne()
        assert_that(calling(fragment.fromUnicode).with_args(u".. invalid::"),
                    raises(InvalidValue, u"Unknown directive"))


class TestSanitizedHTMLContentFragment(_make_test_class('SanitizedHTMLContentFragment')):
    def _transform_raw_for_fromUnicode(self, raw):
        result = u'<p>' + raw + '</p>'
        return result

    def _transform_normalized_for_comparison(self, val):
        return u"<html><body>" + self._transform_raw_for_fromUnicode(val) + u'</body></html>'


TestPlainText = _make_test_class('PlainText', base=_FieldDoesConversionTestsMixin)
TestPlainText.fdctm_sanitize_to = IPlainTextContentFragment
TestPlainText.fdctm_sanitized_text = u"Hi there!"

class TestTag(_make_test_class('Tag', base=_FieldDoesConversionTestsMixin)):

    _transform_normalized_for_comparison = staticmethod(type(u'').lower)

    fdctm_invalid_html = _FieldDoesConversionTestsMixin.fdctm_invalid_html.replace(
        # can't have spaces, and that's not converted away
        u'Hi there!',
        u'Hithere!'
    )
    fdctm_sanitized_text = u'hithere!'
    fdctm_sanitize_to = IPlainTextContentFragment

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
