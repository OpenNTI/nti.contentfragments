#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Converters and utilities for dealing with HTML content fragments.
In particular, sanitazation.

.. $Id: html.py 92331 2016-07-15 01:55:44Z carlos.sanchez $
"""

from __future__ import print_function, unicode_literals, absolute_import, division
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

from repoze.lru import lru_cache

try:
    basestring
except NameError:
    # Py3
    basestring = str
    unicode = str

Element = getattr(etree, 'Element')
etree_tostring = getattr(etree, 'tostring')

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

# But we define our own sanitizer mixin subclass and filter to be able to
# customize the allowed tags and protocols
class _SanitizerFilter(sanitizer.Filter):
    # In order to be able to serialize a complete document, we
    # must whitelist the root tags as of 0.95. But we don't want the mathml and svg tags
    # TODO: Maybe this means now we can parse and serialize in one step?

    def __init__(self, *args, **kwargs):
        super(_SanitizerFilter, self).__init__(*args, **kwargs)
        self.link_finder = component.queryUtility(IHyperlinkFormatter)

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

    def __iter__(self):
        for token in super(_SanitizerFilter, self).__iter__():
            if token:
                token_type = token["type"]
                if token_type == 'Characters':
                    for text_token in self._find_links_in_text(token):
                        yield text_token
                else:
                    yield token

    def _find_links_in_text(self, token):
        text = token['data']
        text_and_links = self.link_finder.find_links(text) if self.link_finder else ()
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
                                   'data': {(None, 'href'): _unicode(text_or_link.attrib['href'])}}
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
        token['data'] = ''
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
    string = string.replace(u'\u00A0', ' ')

    # Back to lxml to do some dom manipulation
    p = HTMLParser(tree=treebuilders.getTreeBuilder("lxml"),
                   namespaceHTMLElements=False)
    doc = p.parse(string)
    return doc

def _doc_to_plain_text(doc):
    string = etree_tostring(doc, method='text', encoding=unicode)
    return PlainTextContentFragment(string)

def sanitize_user_html(user_input, method='html'):
    """
    Given a user input string of plain text, HTML or HTML fragment, sanitize
    by removing unsupported/dangerous elements and doing some normalization.
    If it can be represented in plain text, do so.

    :param string method: One of the ``method`` values acceptable to
        :func:`lxml.etree.tostring`. The default value, ``html``, causes this
        method to produce either HTML or plain text, whatever is most appropriate.
        Passing the value ``text`` causes this method to produce only plain text captured
        by traversing the elements with lxml.

    :return: Something that implements :class:`frg_interfaces.IUnicodeContentFragment`,
        typically either :class:`frg_interfaces.IPlainTextContentFragment` or
        :class:`frg_interfaces.ISanitizedHTMLContentFragment`.
    """

    doc = _to_sanitized_doc(user_input)

    for node in doc.iter():
        # Turn top-level non-whitespace text nodes into paragraphs.
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

    if method == 'text':
        return _doc_to_plain_text(doc)

    string = _html5lib_tostring(doc, sanitize=False)
    # If we can go back to plain text, do so.
    normalized = string[len('<html><head></head><body>'): 0 - len('</body></html>')]
    while normalized.endswith('<br />'):
        # remove trailing breaks
        normalized = normalized[0:-6]

    # If it has no more tags, we can be plain text.
    # TODO: This probably breaks on entities like &lt;
    if '<' not in normalized:
        # 03.2016 - JZ - We no longer want to lstrip.
        string = PlainTextContentFragment(normalized.rstrip())
    else:
        string = SanitizedHTMLContentFragment("<html><body>" + normalized + "</body></html>")
    return string

# Caching these can be quite effective, especially during
# content indexing operations when the same content is indexed
# for multiple users. Both input and output are immutable
# TODO: For the non-basestring cases, we could actually cache the representation
# in a non-persistent field of the object? (But the objects aren't Persistent, so
# _v fields might not work?)

@interface.implementer(IPlainTextContentFragment)
@component.adapter(basestring)
@lru_cache(10000)
def _sanitize_user_html_to_text(user_input):
    """
    Registered as an adapter with the name 'text' for convenience.

    See :func:`sanitize_user_html`.
    """
    # We are sometimes used as a named adapter, or even sadly called
    # directly, which means we can get called even with the right kind
    # of input already. It messes the content up if we try to reparse
    if IPlainTextContentFragment.providedBy(user_input):
        return user_input
    __traceback_info__ = user_input, type(user_input)

    return sanitize_user_html(user_input, method='text')

@interface.implementer(IPlainTextContentFragment)
@component.adapter(IHTMLContentFragment)
@lru_cache(10000)
def _html_to_sanitized_text(html):
    if IPlainTextContentFragment.providedBy(html):
        return html
    __traceback_info__ = html, type(html)

    return _doc_to_plain_text(_to_sanitized_doc(html))

@interface.implementer(IPlainTextContentFragment)
@component.adapter(ISanitizedHTMLContentFragment)
@lru_cache(10000)
def _sanitized_html_to_sanitized_text(sanitized_html):
    p = HTMLParser(tree=treebuilders.getTreeBuilder("lxml"),
                   namespaceHTMLElements=False)
    doc = p.parse(sanitized_html)
    return _doc_to_plain_text(doc)
