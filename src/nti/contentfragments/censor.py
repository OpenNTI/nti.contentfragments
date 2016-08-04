#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
algorithms for content censoring.

The algorithms contained in here are trivially simple.
We could do much better, for example, with prefix trees.
See https://hkn.eecs.berkeley.edu/~dyoo/python/ahocorasick/
and http://pypi.python.org/pypi/trie/0.1.1

If efficiency really matters, and we have many different filters we are
applying, we would need to do a better job pipelining to avoid copies

.. $Id: censor.py 85352 2016-03-26 19:08:54Z carlos.sanchez $
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import re
import array
import codecs
import io

from zope import component
from zope import interface

from zope.event import notify

import html5lib

from lxml import etree

from html5lib import treebuilders

from zope.cachedescriptors.property import Lazy

from .interfaces import CensoredContentEvent
from .interfaces import IHTMLContentFragment
from .interfaces import ICensoredContentPolicy
from .interfaces import UnicodeContentFragment
from .interfaces import ICensoredContentScanner
from .interfaces import ICensoredContentStrategy
from .interfaces import CensoredHTMLContentFragment
from .interfaces import CensoredUnicodeContentFragment
from .interfaces import IPunctuationMarkExpressionPlus
from .interfaces import ICensoredUnicodeContentFragment

etree_tostring = getattr(etree, 'tostring')
resource_string = __import__('pkg_resources').resource_string

# certain old versions of Python 2 up through at least 2.7.9 can't
# handle a unicode character as the array.array descriptor. 2.7.12
# seems to handle it fine, though.
try:
    unicode
except NameError:
    PY2 = False
    unicode = str
    _ARRAY_CHAR_TYPE = 'u'
else:
    PY2 = True
    _ARRAY_CHAR_TYPE = b'u'

def punkt_re_char(lang='en'):
    return component.getUtility(IPunctuationMarkExpressionPlus, name=lang)

def _get_censored_fragment(org_fragment, new_fragment, factory=CensoredUnicodeContentFragment):
    try:
        result = org_fragment.censored(new_fragment)
    except AttributeError:
        result = factory(new_fragment)
        # We used to check this and then do alsoProvides if it wasn't there,
        # but this is only called with two factory arguments, both of which
        # provide the interface.
        assert ICensoredUnicodeContentFragment.providedBy(result)
    return result

@interface.implementer(ICensoredContentStrategy)
class SimpleReplacementCensoredContentStrategy(object):

    def __init__(self, replacement_char='*'):
        assert len(replacement_char) == 1
        self._replacement_array = array.array(_ARRAY_CHAR_TYPE, replacement_char)

    def censor_ranges(self, content_fragment, censored_ranges):
        # Since we will be replacing each range with its equal length
        # of content and not shortening, then sorting the ranges doesn't matter
        content_fragment = content_fragment.decode('utf-8') \
                            if isinstance(content_fragment, bytes) else content_fragment
        buf = array.array(_ARRAY_CHAR_TYPE, content_fragment)

        for start, end in censored_ranges:
            buf[start:end] = self._replacement_array * (end - start)

        new_fragment = buf.tounicode()
        result = _get_censored_fragment(content_fragment, new_fragment)
        return result

class BasicScanner(object):

    def test_range(self, new_range, yielded):
        for t in yielded:
            if new_range[0] >= t[0] and new_range[1] <= t[1]:
                # new_range is entirely included in something we already yielded
                return False
        return True

    def do_scan(self, fragment, ranges):
        """
        do_scan is passed a fragment that is guaranteed to be unicode and lower case.
        """
        raise NotImplementedError()

    def scan(self, content_fragment):
        yielded = []  # A simple, inefficient way of making sure we don't send overlapping ranges
        content_fragment = content_fragment.decode('utf-8') \
                            if isinstance(content_fragment, bytes) else content_fragment
        content_fragment = content_fragment.lower()
        result = self.do_scan(content_fragment, yielded)
        return result

@interface.implementer(ICensoredContentScanner)
class TrivialMatchScanner(BasicScanner):

    def __init__(self, prohibited_values=()):
        # normalize case, ignore blanks
        # In this implementation, the most common values should
        # clearly go at the front of the list
        self.prohibited_values = [x.lower() for x in prohibited_values if x]

    def do_scan(self, content_fragment, yielded):
        for the_word in self.prohibited_values:
            # Find all occurrences of each prohibited word,
            # one at a time
            idx = content_fragment.find(the_word, 0)
            while idx != -1:
                match_range = (idx, idx + len(the_word))
                if self.test_range(match_range, yielded):
                    yield match_range
                idx = content_fragment.find(the_word, match_range[1])

@interface.implementer(ICensoredContentScanner)
class WordMatchScanner(BasicScanner):

    def __init__(self, white_words=(), prohibited_words=()):
        self.white_words = tuple([word.lower() for word in white_words])
        self.prohibited_words = tuple([word.lower() for word in prohibited_words])

    @Lazy
    def char_tester(self):
        return re.compile(punkt_re_char())

    def _test_start(self, idx, content_fragment):
        result = idx == 0 or self.char_tester.match(content_fragment[idx - 1])
        return result

    def _test_end(self, idx, content_fragment):
        result = idx == len(content_fragment) or self.char_tester.match(content_fragment[idx])
        return result

    def _find_ranges(self, word_list, content_fragment):
        for the_word in word_list: # Find all occurrences of each word one by one
            idx = content_fragment.find(the_word, 0)
            while idx != -1:
                endidx = idx + len(the_word)
                match_range = (idx, endidx)
                if  self._test_start(idx, content_fragment) and \
                    self._test_end(endidx, content_fragment):
                    yield match_range
                idx = content_fragment.find(the_word, endidx)

    def do_scan(self, content_fragment, yielded):
        # Here, 'yielded' is the ranges we examine and either guarantee
        # they are good, or guarantee they are bad
        ranges = self._find_ranges(self.white_words, content_fragment)
        yielded.extend(ranges)

        # yield/return any prohibited_words
        ranges = self._find_ranges(self.prohibited_words, content_fragment)
        for match_range in ranges:
            if self.test_range(match_range, yielded):
                yield match_range

@interface.implementer(ICensoredContentScanner)
class PipeLineMatchScanner(BasicScanner):

    def __init__(self, scanners=()):
        self.scanners = tuple(scanners)

    def do_scan(self, content_fragment, yielded):
        for s in self.scanners:
            matched_ranges = s.do_scan(content_fragment, yielded)
            for match_range in matched_ranges:
                if self.test_range(match_range, yielded):
                    yield match_range

def _read(fname, rot13):
    data = resource_string(__name__, fname)
    data_text = data.decode('utf-8')
    # Go through StringIO for universal newline handling
    src = io.StringIO(data_text)
    if rot13:
        words = {codecs.encode(x, 'rot13').strip().lower() for x in src.readlines()}
    else:
        words = {x.strip().lower() for x in src.readlines()}
    return frozenset(words)

_white_words = _read('white_list.txt', False)
_prohibited_words = _read('prohibited_words.txt', True)
_profane_words = _read('profanity_list.txt', True)

@interface.implementer(ICensoredContentScanner)
def _word_profanity_scanner():
    """
    External files are stored in rot13.
    """
    return WordMatchScanner(_white_words, _prohibited_words)

@interface.implementer(ICensoredContentScanner)
def _word_plus_trivial_profanity_scanner():
    return PipeLineMatchScanner([_word_profanity_scanner(), TrivialMatchScanner(_profane_words)])

@interface.implementer(ICensoredContentPolicy)
class DefaultCensoredContentPolicy(object):
    """
    A content censoring policy that looks up the default
    scanner and strategy utilities and uses them.

    This package does not register this policy as an adapter for
    anything, you must do that yourself, on (content-fragment, target-object);
    it can also be registered as a utility or instantiated directly with
    no arguments.
    """

    def __init__(self, fragment=None, target=None):
        pass

    def censor(self, fragment, target):
        if IHTMLContentFragment.providedBy(fragment):
            result = self.censor_html(fragment, target)
        else:
            result = self.censor_text(fragment, target)
        return result

    def censor_text(self, fragment, target):
        scanner = component.getUtility(ICensoredContentScanner)
        strat = component.getUtility(ICensoredContentStrategy)
        return strat.censor_ranges(fragment, scanner.scan(fragment))

    def censor_html(self, fragment, target):
        result = None
        try:
            p = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("lxml"),
                                    namespaceHTMLElements=False)
            doc = p.parse(fragment)
            for node in doc.iter():
                for name in ('text', 'tail'):
                    text = getattr(node, name, None)
                    if text:
                        text = self.censor_text(UnicodeContentFragment(text), target)
                        setattr(node, name, text)

            docstr = etree_tostring(doc, encoding=unicode)
            # be sure to return the best interface
            result = _get_censored_fragment(fragment, docstr,
                                            CensoredHTMLContentFragment)
        except Exception:
            result = self.censor_text(fragment, target)
        return result

@interface.implementer(ICensoredContentPolicy)
class NoOpCensoredContentPolicy(object):
    """
    A content censoring policy that does no censoring whatesover.

    This package does not register this policy as an adapter for
    anything, you must do that yourself, on (content-fragment, target-object);
    it can also be registered as a utility or instantiated directly with
    no arguments.
    """

    def __init__(self, *args, **kwargs):
        pass

    def censor(self, fragment, _target):
        return fragment

from nti.schema.interfaces import BeforeTextAssignedEvent

def censor_before_text_assigned(fragment, target, event):
    """
    Watches for field values to be assigned, and looks for specific policies for the
    given object and field name to handle censoring. If such a policy is found and returns
    something that is not the original fragment, the event is updated (and so the value
    assigned to the target is also updated).
    """

    if ICensoredUnicodeContentFragment.providedBy(fragment):
        # Nothing to do, already censored
        return None, None

    # Does somebody want to censor assigning values of fragments' type to objects of
    # target's type to the field named event.name?
    policy = component.queryMultiAdapter((fragment, target),
                                         ICensoredContentPolicy,
                                         name=event.name)
    if policy is not None:
        censored_fragment = policy.censor(fragment, target)
        if censored_fragment is not fragment and censored_fragment != fragment:
            event.object = censored_fragment

            # notify censoring
            context = event.context or target
            notify(CensoredContentEvent(fragment, censored_fragment,
                                        event.name, context))

            # as an optimization when we are called directly
            return event.object, True
    return fragment, False

def censor_before_assign_components_of_sequence(sequence, target, event):
    """
    Register this adapter for (usually any) sequence, some specific interface target, and
    the :class:`nti.schema.interfaces.IBeforeSequenceAssignedEvent` and it will
    iterate across the fields and attempt to censor each of them.

    This package DOES NOT register this event.
    """
    if sequence is None:
        return

    # There are many optimization opportunities here
    s2 = []
    _changed = False
    evt = BeforeTextAssignedEvent(None, event.name, event.context)
    for obj in sequence:
        evt.object = obj
        val, changed = censor_before_text_assigned(obj, target, evt)
        _changed |= changed
        s2.append(val)

    # only copy the list/tuple/whatever if we need to
    if _changed:
        event.object = type(event.object)(s2)

def censor_assign(fragment, target, field_name):
    """
    Perform manual censoring of assigning an object to a field.
    """
    evt = BeforeTextAssignedEvent(fragment, field_name, target)
    return censor_before_text_assigned(fragment, target, evt)[0]
