#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import is_not
from hamcrest import raises
from hamcrest import calling
from hamcrest import assert_that
from hamcrest import same_instance
does_not = is_not


from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides
from nti.testing.matchers import is_false

import unittest
import mimetypes
try:
    import cPickle as pickle
except ImportError:
    import pickle

from zope import interface

from zope.schema.interfaces import ConstraintNotSatisfied

from . import ContentfragmentsLayerTest

from ..interfaces import HTMLContentFragment
from ..interfaces import UnicodeContentFragment
from ..interfaces import PlainTextContentFragment
from ..interfaces import IPlainTextContentFragment
from ..interfaces import SanitizedHTMLContentFragment
from ..interfaces import IUnicodeContentFragment

from nti.contentfragments.schema import Title
from nti.contentfragments.schema import Tag
from nti.contentfragments.schema import TextUnicodeContentFragment

try:
    unicode
except NameError:
    unicode = str

class ITest(interface.Interface):
    pass

class TestMisc(unittest.TestCase):

    def test_html_math(self):
        s1 = SanitizedHTMLContentFragment('safe')
        s2 = SanitizedHTMLContentFragment('safe2')
        h1 = HTMLContentFragment('unsafe')

        assert_that(s1 + s2, is_(SanitizedHTMLContentFragment),
                    "Adding two sanitized fragments produces sanitized fragments")
        assert_that(s1 + s2, is_('safesafe2'))

        assert_that(s1 + h1, is_(HTMLContentFragment),
                    'Adding an unsanitized produces unsanitized')

        assert_that(h1 + s1, is_(HTMLContentFragment))
        assert_that(h1 + s1, is_('unsafesafe'))
        assert_that(s1 + h1, is_('safeunsafe'))

        assert_that(s1 * 2, is_(SanitizedHTMLContentFragment),
                     "Multiplication produces the same types")
        assert_that(h1 * 2, is_(HTMLContentFragment))
        assert_that(s1 * 2, is_('safesafe'))
        assert_that(h1 * 2, is_('unsafeunsafe'))

        assert_that(2 * s1, is_(SanitizedHTMLContentFragment),
                     "Right multiplication produces the same types")
        assert_that(2 * h1, is_(HTMLContentFragment))
        assert_that(2 * s1, is_('safesafe'))
        assert_that(2 * h1, is_('unsafeunsafe'))

    def test_mime_types(self):
        assert_that(mimetypes.guess_type('foo.jsonp'),
                    is_(('application/json', None)))

    def test_cant_get_dict_weakref_of_frag(self):
        frag = HTMLContentFragment()
        assert_that(calling(getattr).with_args(frag, '__dict__'),
                    raises(AttributeError))
        assert_that(calling(getattr).with_args(frag, '__weakref__'),
                    raises(AttributeError))

    def test_setstate_discards_extra(self):
        frag = HTMLContentFragment()
        frag.__setstate__({'key': 1, 'okey': 2})

    def test_upper_preserves(self):
        h = HTMLContentFragment("HI")
        assert_that(h.upper(), is_(same_instance(h)))

    def test_container_methods(self):
        h = HTMLContentFragment()
        assert_that(calling(h.__delitem__).with_args(1),
                    raises(TypeError))
        assert_that(calling(h.__setitem__).with_args(1, 'b'),
                    raises(TypeError))

    def test_cannot_set_attributes_but_can_provide_interfaces_across_pickles(self):

        all_ucf_subclasses = set()
        def r(t):
            if t in all_ucf_subclasses:
                return
            all_ucf_subclasses.add(t)
            for x in t.__subclasses__():
                r(x)
        r(UnicodeContentFragment)

        # Plus some fixed one just 'cause
        all_ucf_subclasses.update((SanitizedHTMLContentFragment, HTMLContentFragment,
                                   PlainTextContentFragment, UnicodeContentFragment))
        for t in all_ucf_subclasses:
            if t.__module__ != 'nti.contentfragments.interfaces':
                continue

            s1 = t('safe')

            assert_that(calling(setattr).with_args(s1, '__parent__', 'foo'),
                        raises(AttributeError))

            # If we do sneak one into the dictionary, it doesn't survive pickling
            try:
                s1dict = unicode.__getattribute__(s1, '__dict__')
                s1dict['__parent__'] = 'foo'
            except AttributeError:
                if t is not UnicodeContentFragment:
                    # The root really doesn't allow this,
                    # but for some reason of inheritance the
                    # subclasses do?
                    raise

            copy = pickle.loads(pickle.dumps(s1))

            assert_that(copy, is_(s1))
            try:
                copy_dict = unicode.__getattribute__(copy, '__dict__')
            except AttributeError:
                if t is not UnicodeContentFragment:
                    raise
                copy_dict = {}
            assert_that(copy_dict, is_({}))

            # But if they provided extra interfaces, this does persist
            interface.alsoProvides(s1, ITest)

            copy = pickle.loads(pickle.dumps(s1))

            assert_that(copy, verifiably_provides(ITest))

    def test_dont_lose_type_on_common_ops(self):

        for t in SanitizedHTMLContentFragment, HTMLContentFragment, PlainTextContentFragment:
            s1 = t('safe')

            assert_that(s1.translate({ord('s'): 't'}), is_(t))
            assert_that(s1.translate({ord('s'): 't'}), is_('tafe'))

            assert_that(unicode(s1), is_(t))
            assert_that(s1.lower(), is_(t))
            assert_that(s1.upper(), is_(t))

    def test_cannot_have_line_breaks_in_text_line(self):
        ipt = PlainTextContentFragment('This\nis\nnot\nvalid')
        assert_that(ipt, validly_provides(IPlainTextContentFragment))

        assert_that(calling(Title().validate).with_args(ipt),
                    raises(ConstraintNotSatisfied))

class TestMiskConfigured(ContentfragmentsLayerTest):

    def test_TextUnicodeContentFragment(self):
        t = TextUnicodeContentFragment(default='abc')
        assert_that(t.default, validly_provides(IUnicodeContentFragment))


        assert_that(t.fromUnicode(t.default), is_(t.default))

    def test_Tag(self):
        t = Tag()

        assert_that(t.fromUnicode("HI"), is_('hi'))
        assert_that(t.constraint("oh hi"), is_false())
