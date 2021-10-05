#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import
__docformat__ = "restructuredtext en"

# pylint:disable=line-too-long,too-many-public-methods
# pylint:disable=import-outside-toplevel

import os
import contextlib

from hamcrest import is_
from hamcrest import assert_that
from hamcrest import same_instance

from zope import component
from zope import interface

from nti.contentfragments.interfaces import IAllowedAttributeProvider
from nti.contentfragments.interfaces import IHyperlinkFormatter

from nti.testing.matchers import verifiably_provides


try:
    from plistlib import load as load_plist
except ImportError:
    from plistlib import readPlist as load_plist

from nti.contentfragments import interfaces as frg_interfaces

from nti.contentfragments.tests import ContentfragmentsLayerTest
from nti.contentfragments import html as frag_html


class _StringConversionMixin(object):

    # Converting to this interface produces the most suitable
    # derived interfaces
    CONV_IFACE = frg_interfaces.IUnicodeContentFragment

    # This should be set to the most derived interface possible;
    # tests should be structured to group input types that produce
    # this interface.
    EXP_IFACE = None

    # If you're testing particular fragment types as input,
    # set this to the factory (class) that creates that type
    INP_FACTORY = staticmethod(lambda inp: inp)

    def _check_sanitized(self, inp, expect, _again=True):
        # Given exactly a raw string, not a content fragment.
        assert type(inp) in (bytes, type(u'')) # pylint:disable=unidiomatic-typecheck
        inp = self.INP_FACTORY(inp)
        converted = self.CONV_IFACE(inp)
        __traceback_info__ = inp, type(inp), converted, type(converted)
        assert_that(converted, is_(expect.strip()))
        assert_that(converted, verifiably_provides(self.EXP_IFACE))
        return converted

    def _to_one_stripped_line(self, inp):
        """
        Collapse *inp* to one line, with all leading and trailing whitespace removed.
        (Similar to textwrap.dedent)
        """
        one_line = u''.join(l.strip() for l in inp.splitlines())
        assert u'\n' not in one_line
        return one_line

    def tearDown(self):
        from nti.contentfragments.html import _cache_maker
        _cache_maker.clear()
        super(_StringConversionMixin, self).tearDown()


class TestStringInputToPlainTextOutput(_StringConversionMixin, ContentfragmentsLayerTest):

    EXP_IFACE = frg_interfaces.IPlainTextContentFragment

    def test_sanitize_removes_empty(self):
        # If everything is removed, resulting in an empty string, it's just plain text.
        html = u'<html><body><span></span></body></html>'
        exp = u''
        self._check_sanitized(html, exp)

        html = u'<div>'
        self._check_sanitized(html, u'')

    def test_sanitize_remove_inner_elems_empty(self):
        # As for `test_sanitize_removes_empty`, but here we have content hiding
        # inside forbidden elements.
        html = u'<html><body><script><div /><span>Hi</span></script><style><span>hi</span></style></body></html>'
        exp = u''
        self._check_sanitized(html, exp)

    def test_embedded_table(self):
        markdown = u"""
This is a regular paragraph.

<table>
    <tr>
        <td>Foo</td>
    </tr>
    <tr>
        <td>Bar</td>
    </tr>
</table>

This is another regular paragraph.
        """
        exp = """\
This is a regular paragraph.  Foo
---
Bar
This is another regular paragraph.\
        """
        self._check_sanitized(markdown, exp)

    def test_embedded_random_tags(self):
        markdown = u"""
Some beginning text.

<random_tag>
  <ns:foo xmlns:foo="http://example.com">A foo tag.<ns:foo>
</random_tag>

Some ending text.
        """
        exp = """Some beginning text.  A foo tag. Some ending text."""
        self._check_sanitized(markdown, exp)

    def test_sanitize_remove_tags_leave_content(self):
        # If all tags are removed, its just plain text
        html = u'<html><body><div style=" text-align: left;">The text</div></body></html>'
        exp = u'The text'
        self._check_sanitized(html, exp)

    def test_entity_trailing_break_removal(self):
        html = u'Here is something that another friend told me about: themathpage_com/alg/algebra.htm&nbsp;<br><br>'
        expt = u'Here is something that another friend told me about: themathpage_com/alg/algebra.htm'
        self._check_sanitized(html, expt)

        html = u"Sure, Chris. &nbsp;Feel free to chat when I'm online or submit a Quick Question for the community."
        expt = u"Sure, Chris.  Feel free to chat when I'm online or submit a Quick Question for the community."
        self._check_sanitized(html, expt)

        html = u'Hi, Ken. &nbsp;Here is the answer. &nbsp;Check this website www_xyz_com'
        expt = u'Hi, Ken.  Here is the answer.  Check this website www_xyz_com\n'
        self._check_sanitized(html, expt)

class TestByteInputToPlainTextOutput(TestStringInputToPlainTextOutput):

    def _check_sanitized(self, html, expt): # pylint:disable=arguments-differ
        assert isinstance(html, type(u''))
        html = html.encode('latin-1')
        return super(TestByteInputToPlainTextOutput, self)._check_sanitized(html, expt)

class TestStringToSanitizedHTML(_StringConversionMixin, ContentfragmentsLayerTest):

    EXP_IFACE = frg_interfaces.ISanitizedHTMLContentFragment

    def test_sanitize_html_examples(self):
        with open(os.path.join(os.path.dirname(__file__), 'contenttypes-notes-tosanitize.plist'), 'rb') as f:
            strings = load_plist(f) # pylint:disable=deprecated-method
        with open(os.path.join(os.path.dirname(__file__), 'contenttypes-notes-sanitized.txt')) as f:
            sanitized = f.readlines()

        assert len(strings) == len(sanitized)
        for s in zip(strings, sanitized):
            self._check_sanitized(*s)

    def test_sanitize_data_uri(self):
        self._check_sanitized("<audio src='data:foobar' controls />",
                              u'<html><body><audio controls=""></audio></body></html>')

        self._check_sanitized("<audio data-id='ichigo' />",
                              u'<html><body><audio data-id="ichigo"></audio></body></html>')

    def test_normalize_html_text_to_par(self):
        html = u'<html><body><p style=" text-align: left;"><span style="font-family: \'Helvetica\';  font-size: 12pt; color: black;">The pad replies to my note.</span></p>The server edits it.</body></html>'
        exp = u'<html><body><p style="text-align: left;"><span>The pad replies to my note.</span></p><p style="text-align: left;">The server edits it.</p></body></html>'
        self._check_sanitized(html, exp)

    def test_normalize_simple_style_color(self):
        html = u'<html><body><p><span style="color: black;">4</span></p></body></html>'
        exp = html
        sanitized = self._check_sanitized(html, exp)
        assert_that(sanitized, is_(exp))

    def test_normalize_simple_style_font(self):
        html = u'<html><body><p><span style="font-family: sans-serif;">4</span></p></body></html>'
        exp = html
        sanitized = self._check_sanitized(html, exp)

        assert_that(sanitized, is_(exp))

    def test_normalize_style_with_quoted_dash(self):
        html = u'<html><body><p style="text-align: left;"><span style="font-family: \'Helvetica-Bold\'; font-size: 12pt; font-weight: bold; color: black;">4</span></p></body></html>'
        exp = html
        sanitized = self._check_sanitized(html, exp)
        assert_that(sanitized, is_(exp))

    def test_rejected_tags(self):
        html = u'<html><body><style>* { font: "Helvetica";}</style><p style=" text-align: left;">The text</div></body></html>'
        exp = u'<html><body><p style="text-align: left;">The text</p></body></html>'
        self._check_sanitized(html, exp)

        html = u'<html><body><script><p>should be ignored</p> Other stuff.</script><p style=" text-align: left;">The text</div></body></html>'
        exp = u'<html><body><p style="text-align: left;">The text</p></body></html>'
        self._check_sanitized(html, exp)

        html = u'foo<div><br></div><div>http://google.com</div><div><br></div><div>bar</div><div><br></div><div>http://yahoo.com</div>'
        exp = u'<html><body>foo<br /><a href="http://google.com">http://google.com</a><br />bar<br /><a href="http://yahoo.com">http://yahoo.com</a></body></html>'
        self._check_sanitized(html, exp)

    def test_pre_allowed(self):
        html = u'<html><body><pre>The text</pre></body></html>'
        exp = html
        self._check_sanitized(html, exp)

    def test_blog_html_to_text(self):
        exp = u'<html><body>Independence<br />America<br />Expecting<br />Spaces</body></html>'
        plain_text = frg_interfaces.IPlainTextContentFragment(exp)
        assert_that(plain_text, verifiably_provides(frg_interfaces.IPlainTextContentFragment))
        assert_that(plain_text, is_("Independence\nAmerica\nExpecting\nSpaces"))

    def test_links_preserved_plain_string_html_to_text(self):
        html = u'<html><body><div>For help, <a href="email:support@nextthought.com">email us</a></div></html>'
        plain_text = frg_interfaces.IPlainTextContentFragment(html)
        assert_that(plain_text, verifiably_provides(frg_interfaces.IPlainTextContentFragment))
        # The lxml implementation loses the link entirely.
        # expected = """For help, email us"""
        expected = """For help, [email us](email:support@nextthought.com)"""
        assert_that(plain_text, is_(expected))

    def test_sanitize_user_html_chat(self):
        # Note this is badly malformed. The <a> tag is never closed,
        # and neither is the href attribute, exactly: the closing ' is \'
        href = u"""http://tag:nextthought.com,2011-10:julie.zhu-OID-0x148a37:55736572735f315f54657374:hjJe3dfZMVb,"body":["5:::{\"args"""
        html = u"""\
        <html>
        <a href='%s\\'>
        foo
        </html>
        """ % (href,)

        plain_text = frg_interfaces.IPlainTextContentFragment(html)
        assert_that(plain_text, verifiably_provides(frg_interfaces.IPlainTextContentFragment))
        # Was just "foo" in the lxml based implementation (before the addition of spaces)
        # expected = "foo"
        expected = """[ foo"""
        assert_that(plain_text, is_(expected))

        # idempotent
        assert_that(frag_html._sanitize_user_html_to_text(plain_text),
                    is_(same_instance(plain_text)))
        assert_that(frag_html._html_to_sanitized_text(plain_text),
                    is_(same_instance(plain_text)))

    def test_sanitize_img(self):
        html = '<html><body><img style="color: blue; text-align: left; max-width: 10px" href="foo"></body></html>'
        exp = '<html><body><img href="foo" style="color: blue; text-align: left; max-width: 100%;" /></body></html>'
        self._check_sanitized(html, exp)

        html = '<html><body><img style="" href="foo"></body></html>'
        exp = '<html><body><img href="foo" style="max-width: 100%;" /></body></html>'
        self._check_sanitized(html, exp)

        html = '<html><body><img max-width="1%" href="foo"></body></html>'
        exp = '<html><body><img href="foo" style="max-width: 100%;" /></body></html>'
        self._check_sanitized(html, exp)

    def _allowed_attr_provider(self, attrs_to_allow):
        class TestAllowedAttrProvider(object):
            allowed_attributes = attrs_to_allow

        allowed_attribute_provider = TestAllowedAttrProvider()
        interface.alsoProvides(allowed_attribute_provider, (IAllowedAttributeProvider,))
        return allowed_attribute_provider

    def _check_allowed_attribute_provider(self, attr_name, included=True):
        html = '<html><body><a %s="my_value">Bobby Hagen</a></body></html>' % attr_name
        exp = html if included else '<html><body><a>Bobby Hagen</a></body></html>'
        self._check_sanitized(html, exp)

    def test_allowed_attribute_provider(self):
        self._check_allowed_attribute_provider("abc", included=False)

        allowed_attrs = ["abc", "xyz"]
        allowed_attribute_provider = self._allowed_attr_provider(allowed_attrs)

        with _provide_utility(allowed_attribute_provider):
            for attr_name in allowed_attrs:
                self._check_allowed_attribute_provider(attr_name)

    def test_existing_links(self):
        allowed_attribute_provider = self._allowed_attr_provider(["data-nti-entity-href"])

        with _provide_utility(allowed_attribute_provider):
            # Ensure we properly handle html with existing anchors
            html = '<p><a data-nti-entity-href="http://www.google.com" ' \
                   'href="http://www.google.com">www.google.com</a></p>'
            exp = '<html><body><p><a data-nti-entity-href="http://www.google.com" ' \
                  'href="http://www.google.com">www.google.com</a></p></body></html>'
            self._check_sanitized(html, exp)

    def test_link_creation(self):
        # Ensure links are created for url-like text following anchors
        html = '<p><a href="nextthought.com">NTI</a>www.google.com</p>'
        exp = '<html><body><p><a href="nextthought.com">NTI</a>' \
              '<a href="http://www.google.com">www.google.com</a></p></body></html>'
        self._check_sanitized(html, exp)

    def test_no_link_formatter(self):
        with _link_formatter(None):
            html = '<p>look at this</p>'
            exp = '<html><body><p>look at this</p></body></html>'
            self._check_sanitized(html, exp)

    def test_nested_anchors(self):
        # Links should not be created for the url-like text and nesting
        # will be split
        html = '<p><a href="www.nextthought.com">www.nextthought.com' \
               '<a href="www.google.com">www.google.com</a></a></p>'
        exp = '<html><body><p><a href="www.nextthought.com">www.nextthought.com</a>' \
              '<a href="www.google.com">www.google.com</a></p></body></html>'
        self._check_sanitized(html, exp)

    def test_disallowed_within_anchor(self):
        html = '<a href="www.nextthought.com"><div>test</div></a>'
        self._check_sanitized(html, u'<html><body><a href="www.nextthought.com">test</a></body></html>')


class TestHTMLFragmentToPlainText(_StringConversionMixin, ContentfragmentsLayerTest):

    INP_FACTORY = frg_interfaces.HTMLContentFragment
    CONV_IFACE = frg_interfaces.IPlainTextContentFragment
    EXP_IFACE = frg_interfaces.IPlainTextContentFragment

    def test_html_to_text(self):
        # The old lxml implementation didn't produce any newlines in the
        # output if the HTML comes in all on one line. The new version produces
        # the same output either way. The old version also adds leading newlines
        # if there is leading newlines in the input
        raw_html = u"""
        <html>
        <body>
        <p style="text-align: left;">
        <span>The pad replies to my note.</span>
        </p>
        <p style="text-align: left;">The server edits it.</p>
        </body>
        </html>
        """

        one_line_html = self._to_one_stripped_line(raw_html)

        expt = u"The pad replies to my note.\n\nThe server edits it."
        self._check_sanitized(one_line_html, expt)
        self._check_sanitized(raw_html, expt)


class TestSanitizedHTMLFragmentToPlainText(_StringConversionMixin, ContentfragmentsLayerTest):
    INP_FACTORY = frg_interfaces.ISanitizedHTMLContentFragment
    CONV_IFACE = frg_interfaces.IPlainTextContentFragment
    EXP_IFACE = frg_interfaces.IPlainTextContentFragment

    EXAMPLE = u"""
        <html>
        <body>
        <p style=" text-align: left;">
        <span style="font-family: \'Helvetica\';  font-size: 12pt; color: black;">
        The pad replies to my note.
        </span>
        </p>
        The server edits it.
        </body>
        </html>
        """

    def test_html_to_text(self):
        # Just like with ``TestHTMLFragmentToPlainText.test_html_to_text``
        raw_html = self.EXAMPLE
        one_line_html = self._to_one_stripped_line(raw_html)

        expt = u"The pad replies to my note.\n\nThe server edits it."
        for html in one_line_html, raw_html:
            __traceback_info__ = html
            assert_that(self.INP_FACTORY(html),
                        is_(frg_interfaces.SanitizedHTMLContentFragment))
            self._check_sanitized(html, expt)


class TestSanitizeUserHtmlFunction(TestHTMLFragmentToPlainText):
    # Just like going through the interfaces, but called directly.
    # this is legacy functionality for callers passing a method directly.

    def CONV_IFACE(self, html):
        from nti.contentfragments.html import sanitize_user_html
        return sanitize_user_html(html, 'text')



@contextlib.contextmanager
def _link_formatter(util):
    gsm = component.getGlobalSiteManager()
    current = gsm.getUtility(IHyperlinkFormatter)
    if current is not None:
        gsm.unregisterUtility(current, IHyperlinkFormatter)

    if util is not None:
        gsm.registerUtility(util, IHyperlinkFormatter)
    try:
        yield
    finally:
        if util is not None:
            gsm.unregisterUtility(util, IHyperlinkFormatter)
        if current is not None:
            gsm.registerUtility(current, IHyperlinkFormatter)

@contextlib.contextmanager
def _provide_utility(util):
    gsm = component.getGlobalSiteManager()
    gsm.registerUtility(util, IAllowedAttributeProvider)
    try:
        yield
    finally:
        gsm.unregisterUtility(util, IAllowedAttributeProvider)
