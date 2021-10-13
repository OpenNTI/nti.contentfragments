#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Converters and utilities for dealing with HTML content fragments.
In particular, sanitazation.

.. $Id: html.py 92331 2016-07-15 01:55:44Z carlos.sanchez $
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import re

from zope import interface
from zope import component

from lxml import etree

from html5lib import HTMLParser
from html5lib import serializer
from html5lib import treewalkers
from html5lib import treebuilders
from html5lib.filters import sanitizer

from repoze.lru import CacheMaker

from html2text import html2text

from nti.contentfragments.interfaces import IAllowedAttributeProvider

try:
    basestring
except NameError:
    # Py3
    basestring = str
    unicode = str

Element = getattr(etree, 'Element')
etree_tostring = getattr(etree, 'tostring')

# This regex is basen on one from Python 3's html.parser module;
# it is used in the parser's ``check_for_whole_start_tag`` method.
# That regex in turn comes from the HTML5 specification.
locatestarttagend_tolerant = re.compile(r"""
  <[a-zA-Z][^\t\n\r\f />\x00]*       # tag name
  (?:[\s/]*                          # optional whitespace before attribute name
    (?:(?<=['"\s/])[^\s/>][^\s/=>]*  # attribute name
      (?:\s*=+\s*                    # value indicator
        (?:'[^']*'                   # LITA-enclosed value
          |"[^"]*"                   # LIT-enclosed value
          |(?!['"])[^>\s]*           # bare value
         )
        \s*                          # possibly followed by a space
       )?(?:\s|/(?!>))*
     )*
   )?
  \s*                                # trailing whitespace
""", re.VERBOSE)
# Likewise, these come from the same module. The detect ``&nbsp;``
# and friends.
entityref = re.compile(u'&([a-zA-Z][-.a-zA-Z0-9]*)[^a-zA-Z0-9]')
charref = re.compile(u'&#(?:[0-9]+|[xX][0-9a-fA-F]+)[^0-9a-fA-F]')
# TODO: It would be nice (perhaps a performance win?) to be able to combine
# the three expressions into a single expression. The naive way, simply
# concatenating them with ``(...)|(...)|(...)``, doesn't work (probably
# because of the VERBOSE flag)


# serializer.xhtmlserializer.XHTMLSerializer is removed in html5lib 1.0.
# It was simply defined as:
#
# class XHTMLSerializer(HTMLSerializer):
#   quote_attr_values = True
#   minimize_boolean_attributes = False
#   use_trailing_solidus = True
#   escape_lt_in_attrs = True
#   omit_optional_tags = False
#   escape_rcdata = True
#
# Note that this did not actually guarantee that the results were valid XHTML
# (which is why it was removed). We define our own version
# that works similarly but has a less confusing name, plus includes
# our standard options

class _Serializer(serializer.HTMLSerializer):

    # attribute quoting options
    quote_attr_values = 'always'

    # tag syntax options
    omit_optional_tags = False
    use_trailing_solidus = True
    minimize_boolean_attributes = False
    space_before_trailing_solidus = True

    # escaping options
    escape_lt_in_attrs = True
    escape_rcdata = True

    # miscellaneous options
    # In 1.0b3, the order changed to preserve
    # the source order. But for tests, its best of
    # they are in a known order
    alphabetical_attributes = True
    inject_meta_charset = False
    strip_whitespace = True
    sanitize = False

from nti.contentfragments.interfaces import IHyperlinkFormatter
from nti.contentfragments.interfaces import IHTMLContentFragment
from nti.contentfragments.interfaces import PlainTextContentFragment
from nti.contentfragments.interfaces import IPlainTextContentFragment
from nti.contentfragments.interfaces import SanitizedHTMLContentFragment
from nti.contentfragments.interfaces import ISanitizedHTMLContentFragment

# HTML5Lib has a bug in its horribly-complicated regular expressions
# it uses for CSS (https://github.com/html5lib/html5lib-python/issues/69):
# It disallows dashes as being part of a quoted value, meaning you can't
# use a font-name like "Helvetica-Bold" (though the literal ``sans-serif``
# is fine; the problem is only in quotes). We fix this by patching the regex
# in place. This is a very targeted fix.
# TODO: Could this allow malformed CSS through now, enough to crash
# the rest of the method?

class FakeRe(object):

    def match(self, regex, val):
        if regex == r"""^([:,;#%.\sa-zA-Z0-9!]|\w-\w|'[\s\w]+'|"[\s\w]+"|\([\d,\s]+\))*$""":
            regex = r"""^([:,;#%.\sa-zA-Z0-9!-]|\w-\w|'[\s\w-]+'|"[\s\w-]+"|\([\d,\s]+\))*$"""
        return re.match(regex, val)

    def __getattr__(self, attr):
        return getattr(re, attr)
sanitizer.re = FakeRe()

from html5lib.constants import namespaces


@interface.implementer(IHyperlinkFormatter)
class _NoopHyperlinkFormatter(object):
    """
    A fallback hyperlink formatter that does not attempt to identify
    links in the provided text.
    """

    def find_links(self, text):
        return (text, )

    def format(self, html_fragment):
        # TODO should this just return html_fragment?
        raise NotImplementedError # pragma: no cover


# But we define our own sanitizer mixin subclass and filter to be able to
# customize the allowed tags and protocols
class _SanitizerFilter(sanitizer.Filter):
    # In order to be able to serialize a complete document, we
    # must whitelist the root tags as of 0.95. But we don't want the mathml and svg tags
    # TODO: Maybe this means now we can parse and serialize in one step?

    def __init__(self, *args, **kwargs):
        super(_SanitizerFilter, self).__init__(*args, **kwargs)
        self.link_finder = component.queryUtility(IHyperlinkFormatter,
                                                  default=_NoopHyperlinkFormatter())

        acceptable_elements = frozenset([
            'a', 'audio',
            'b', 'big', 'br',
            'center',
            'em',
            'font',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr',
            'i', 'img',
            'p', 'pre',
            'small', 'span', 'strong', 'sub', 'sup',
            'tt',
            'u',
            'ul', 'li', 'ol'
        ])
        allowed_elements = acceptable_elements | frozenset(['html', 'head', 'body'])
        self.allowed_elements = frozenset(((namespaces['html'], tag) for tag in allowed_elements))

        # Lock down attributes for safety
        allowed_attributes = frozenset([
            'color',
            'data-id',
            'controls',
            'href',
            'src',
            'style',
            'xml:lang'
        ])

        allowed_attr_provider = component.queryUtility(IAllowedAttributeProvider)
        if allowed_attr_provider:
            additional_attrs_allowed = frozenset(allowed_attr_provider.allowed_attributes)
            allowed_attributes = allowed_attributes | additional_attrs_allowed

        self.allowed_attributes = frozenset(((None, attr) for attr in allowed_attributes))

        # We use data: URIs to communicate images and sounds in one
        # step. FIXME: They aren't really safe and we should have tighter restrictions
        # on them, such as by size.
        self.allowed_protocols = self.allowed_protocols | frozenset(['data'])

        # Lock down CSS for safety
        self.allowed_css_properties = frozenset([
            'font-style',
            'font',
            'font-weight',
            'font-size',
            'font-family',
            'color',
            'text-align',
            'text-decoration'
        ])

        # Things we don't even try to preserve the text content of
        # NOTE: These are not namespaced
        self._ignored_elements = frozenset(['script', 'style'])
        self._ignoring_stack = []

        self._anchor_depth = 0

    @property
    def _in_anchor(self):
        return self._anchor_depth > 0

    def __iter__(self):
        for token in super(_SanitizerFilter, self).__iter__():
            if token:
                __traceback_info__ = token
                token_type = token["type"]
                if token_type == 'Characters' and not self._in_anchor:
                    for text_token in self._find_links_in_text(token):
                        yield text_token
                else:
                    yield token

    def _find_links_in_text(self, token):
        text = token['data']
        text_and_links = self.link_finder.find_links(text)
        if len(text_and_links) != 1 or text_and_links[0] != text:

            def _unicode(x):
                return unicode(x, 'utf-8') if isinstance(x, bytes) else x

            for text_or_link in text_and_links:
                if isinstance(text_or_link, basestring):
                    sub_token = token.copy()
                    sub_token['data'] = _unicode(text_or_link)
                    yield sub_token
                else:
                    start_token = {'type': 'StartTag',
                                   'name': 'a',
                                   'namespace': 'None',
                                   'data': {(None, u'href'): _unicode(text_or_link.attrib['href'])}}
                    yield start_token
                    text_token = token.copy()
                    text_token['data'] = _unicode(text_or_link.text)
                    yield text_token

                    end_token = {'type': 'EndTag',
                                 'name': 'a',
                                 'namespace': 'None',
                                 'data': {}}
                    yield end_token
        else:
            yield token

    def sanitize_token(self, token):
        """
        Alters the super class's behaviour to not write escaped version of disallowed tags
        and to reject certain tags and their bodies altogether. If we instead write escaped
        version of the tag, then we get them back when we serialize to text, which is not what we
        want. The rejected tags have no sensible text content.

        This works in cooperation with :meth:`disallowed_token`.
        """
        #accommodate filters which use token_type differently
        token_type = token["type"]

        if token_type == 'Characters' and self._ignoring_stack:
            # character data beneath a rejected element
            return None

        # Indicate whether we're in an anchor tag
        if token.get('name') == 'a':
            # Trigger on start/end tags, not others (e.g. empty tags)
            if token_type == 'StartTag':
                self._anchor_depth += 1
            elif token_type == 'EndTag':
                self._anchor_depth -= 1

        result = super(_SanitizerFilter, self).sanitize_token(token)
        return result

    def disallowed_token(self, token):
        token_type = token['type']
        # We're making some assumptions here, like all the things we reject are not empty
        if token['name'] in self._ignored_elements:
            if token_type == 'StartTag':
                self._ignoring_stack.append(token)
            elif token_type == 'EndTag':
                self._ignoring_stack.pop()
            return None

        if self._ignoring_stack:
            # element data beneath something we're rejecting
            # XXX: JAM: I can't get this condition to happen in tests!
            return None # pragma: no cover

        # Otherwise, don't escape the tag, simply drop the tag name, but
        # preserve the contents.
        token['data'] = u''
        token["type"] = "Characters"

        del token["name"]
        return token

def _html5lib_tostring(doc, sanitize=True):
    """
    :return: A unicode string representing the document in normalized
        HTML5 form, parseable as XML.
    """
    walker = treewalkers.getTreeWalker("lxml")
    stream = walker(doc)
    if sanitize:
        stream = _SanitizerFilter(stream)

    # We want to produce parseable XML so that it's easy to deal with
    # outside a browser; this
    # We do not strip whitespace here. In most cases, we want to preserve
    # user added whitespace.
    s = _Serializer(strip_whitespace=False)

    # By not passing the 'encoding' arg, we get a unicode string
    output_generator = s.serialize(stream)
    string = u''.join(output_generator)
    return string

def _to_sanitized_doc(user_input):
    # We cannot sanitize and parse in one step; if there is already
    # HTML around it, then we wind up with escaped HTML as text:
    # <html>...</html> => <html><body>&lthtml&gt...&lt/html&gt</html>
    __traceback_info__ = user_input
    p = HTMLParser(tree=treebuilders.getTreeBuilder("lxml"),
                   namespaceHTMLElements=False)
    doc = p.parse(user_input)
    string = _html5lib_tostring(doc, sanitize=True)

    # Our normalization is pathetic.
    # replace unicode nbsps
    string = string.replace(u'\u00A0', u' ')

    # Back to lxml to do some dom manipulation
    p = HTMLParser(tree=treebuilders.getTreeBuilder("lxml"),
                   namespaceHTMLElements=False)
    doc = p.parse(string)
    return doc

def sanitize_user_html(user_input, method='html'):
    """
    Given a user input string of plain text, HTML or HTML fragment, sanitize
    by removing unsupported/dangerous elements and doing some normalization.
    If it can be represented in plain text, do so.

    :param string method: One of the ``method`` values acceptable to
        :func:`lxml.etree.tostring`. The default value, ``html``, causes this
        method to produce either HTML or plain text, whatever is most appropriate.
        Passing the value ``text`` causes this method to produce only plain text captured
        by traversing the elements with lxml. Note: this is legacy functionality,
        and callers should generally convert via calling the interfaces.

    :return: Something that implements :class:`frg_interfaces.IUnicodeContentFragment`,
        typically either :class:`frg_interfaces.IPlainTextContentFragment` or
        :class:`frg_interfaces.ISanitizedHTMLContentFragment`.
    """
    # Registered as the adapter from (bytes/unicode) -> IUnicodeContentFragment
    # And as the adapter from IHTMLContentFragment -> ISanitizedHTMLContentFragment
    # (even though that may be plain text).

    if not may_contain_html_like_markup(user_input):
        return _sanitize_user_html_to_text(user_input, _guaranteed_no_markup=True)

    if method == 'text':
        return _sanitize_user_html_to_text(user_input)

    doc = _to_sanitized_doc(user_input)

    for node in doc.iter():
        # Turn top-level non-whitespace text nodes into paragraphs.
        # Note that we get a mix of unicode and str values for 'node.tag'
        # on Python 2.
        if node.tag == 'p' and node.tail and node.tail.strip():
            tail = node.tail
            node.tail = None
            p = Element(node.tag, node.attrib)
            p.text = tail
            node.addnext(p)

        # Insert a line break.
        elif node.tag == 'br' and len(node) == 0 and not node.text:
            node.text = u'\n'

        # Strip spans that are the empty (they used to contain style but no longer).
        elif node.tag == 'span' and len(node) == 0 and not node.text:
            node.getparent().remove(node)

        # Spans that are directly children of a paragraph (and so could not contain
        # other styling through inheritance) that have the pad's default style get that removed
        # so they render as default on the browser as well
        elif node.tag == 'span' and node.getparent().tag == 'p' and \
             node.get('style') == 'font-family: \'Helvetica\'; font-size: 12pt; color: black;':
            del node.attrib['style']

        # Contain the image width to our container size (max-width=100%).
        # We could also do the same via CSS. Seems like doing so here
        # for user-provided images might be preferable.
        elif node.tag == 'img':
            node.attrib.pop('max-width', None)
            style = node.attrib.get('style') or ''
            # max-width is not in our allowed list of styles
            assert 'max-width' not in style
            new_style = style + (' ' if style else '') + 'max-width: 100%;'
            node.attrib['style'] = new_style

    string = _html5lib_tostring(doc, sanitize=False)
    # If we can go back to plain text, do so.
    normalized = string[len('<html><head></head><body>'): 0 - len('</body></html>')]
    while normalized.endswith('<br />'):
        # remove trailing breaks
        normalized = normalized[0:-6]

    # If it has no more tags, we can be plain text.
    if not may_contain_html_like_markup(normalized):
        # Going via the to-markdown converter yields prettier results than simply
        # returning a PlainTextContentFragment. This does mean we parse it twice,
        # but html2text is fast.
        # TODO: does this suffer from issue 44, notably, being too aggressive about
        # some conversions?
        string = _sanitize_user_html_to_text(user_input)
    else:
        string = SanitizedHTMLContentFragment(u"<html><body>" + normalized + u"</body></html>")
    return string

# Caching these can be quite effective, especially during
# content indexing operations when the same content is indexed
# for multiple users. Both input and output are immutable
# TODO: For the non-basestring cases, we could actually cache the representation
# in a non-persistent field of the object? (But the objects aren't Persistent, so
# _v fields might not work?)

_cache_maker = CacheMaker(10000)

def _ensure_unicode_non_lossy(user_input):
    # Decode to unicode using an encoding that doesn't lose any bytes;
    # let the HTML parser deal with anything at a higher level.
    if isinstance(user_input, bytes):
        user_input = user_input.decode('latin-1')
    return user_input

@_cache_maker.lrucache()
def may_contain_html_like_markup(user_input):
    # Detect if there are valid start tags or entity/character references that should
    # be stripped/replaced.

    # Python 2 can match bytes patterns against unicode or bytes input, and vice versa,
    # unicode patterns against bytes or unicode input. However, Python 3 only works
    # when both pattern and input are the same type. The patterns will be unicode on Python 3,
    # so make sure our input is as well.
    user_input = _ensure_unicode_non_lossy(user_input)

    # search() -> match anywhere in the string; match() -> only the beginning

    return (
        locatestarttagend_tolerant.search(user_input)
        or entityref.search(user_input)
        or charref.search(user_input)
    )


@interface.implementer(IPlainTextContentFragment)
@component.adapter(basestring)
@_cache_maker.lrucache()
def _sanitize_user_html_to_text(user_input, _guaranteed_no_markup=False):
    """
    _sanitize_user_html_to_text(user_input) -> str

    Registered as an adapter with the name 'text' for convenience.

    See :func:`sanitize_user_html`.

    .. caution::
       While this adapter accepts an arbitrary base string, it does not actually
       guarantee the output is totally plain text suitable for any purpose.
       In particular, it only attempts to extract human-readable text from things
       that look like HTML markup while preserving most information such as links.
       It does not attempt to extract human-readable text from things like
       LaTeX or ReST input; input in forms like that may be returned unaltered or
       altered beyond recognition.

       This adapter also does not attempt to escape any characters that may have
       special meaning to HTML, such as ``<`` if the input does not otherwise appear to be
       HTML.

    """
    # We are sometimes used as a named adapter, or even sadly called
    # directly, which means we can get called even with the right kind
    # of input already. It messes the content up if we try to reparse
    if IPlainTextContentFragment.providedBy(user_input):
        return user_input

    # Decode to unicode using a sequence that doesn't lose any bytes;
    # let the HTML parser deal with anything at a higher level.
    user_input = _ensure_unicode_non_lossy(user_input)

    if _guaranteed_no_markup or not may_contain_html_like_markup(user_input):
        output = user_input
    else:
        # Using a wider bodywidth helps prevent unneeded line breaks,
        # especially in tests.
        output = html2text(user_input, bodywidth=100)

    # The old lxml-based implementation stripped trailing whitespace on each line; for compatibility
    # do the same
    output = '\n'.join(l.rstrip() for l in output.splitlines())
    output = output.rstrip()
    return PlainTextContentFragment(output)

@interface.implementer(IPlainTextContentFragment)
@component.adapter(IHTMLContentFragment)
@_cache_maker.lrucache()
def _html_to_sanitized_text(html):
    return _sanitize_user_html_to_text(html)

@interface.implementer(IPlainTextContentFragment)
@component.adapter(ISanitizedHTMLContentFragment)
@_cache_maker.lrucache()
def _sanitized_html_to_sanitized_text(sanitized_html):
    return _sanitize_user_html_to_text(sanitized_html)

try:
    from zope.testing.cleanup import addCleanUp
except ImportError: # pragma: no cover
    pass
else:
    addCleanUp(_cache_maker.clear)
