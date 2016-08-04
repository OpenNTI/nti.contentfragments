#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Helper classes to use content fragments in :mod:`zope.interface`
or :mod:`zope.schema` declarations.

.. $Id: schema.py 85352 2016-03-26 19:08:54Z carlos.sanchez $
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from nti.contentfragments.interfaces import IContentFragment
from nti.contentfragments.interfaces import HTMLContentFragment
from nti.contentfragments.interfaces import IHTMLContentFragment
from nti.contentfragments.interfaces import LatexContentFragment
from nti.contentfragments.interfaces import ILatexContentFragment
from nti.contentfragments.interfaces import UnicodeContentFragment
from nti.contentfragments.interfaces import IUnicodeContentFragment
from nti.contentfragments.interfaces import PlainTextContentFragment
from nti.contentfragments.interfaces import IPlainTextContentFragment
from nti.contentfragments.interfaces import SanitizedHTMLContentFragment
from nti.contentfragments.interfaces import ISanitizedHTMLContentFragment

from nti.schema.field import Object
from nti.schema.field import ValidText as Text
from nti.schema.field import ValidTextLine as TextLine

def _massage_kwargs(self, kwargs):

    assert self._iface.isOrExtends(IUnicodeContentFragment)
    assert self._iface.implementedBy(self._impl)

    # We're imported too early for ZCA to be configured and we can't automatically
    # adapt.
    if 'default' in kwargs and not self._iface.providedBy(kwargs['default']):
        kwargs['default'] = self._impl(kwargs['default'])
    if 'default' not in kwargs and 'defaultFactory' not in kwargs and not kwargs.get('min_length'):  # 0/None
        kwargs['defaultFactory'] = self._impl
    return kwargs

class TextUnicodeContentFragment(Object, Text):
    """
    A :class:`zope.schema.Text` type that also requires the object implement
    an interface descending from :class:`~.IUnicodeContentFragment`.

    Pass the keyword arguments for :class:`zope.schema.Text` to the constructor; the ``schema``
    argument for :class:`~zope.schema.Object` is already handled.
    """

    _iface = IUnicodeContentFragment
    _impl = UnicodeContentFragment

    def __init__(self, *args, **kwargs):
        super(TextUnicodeContentFragment, self).__init__(self._iface, *args, **_massage_kwargs(self, kwargs))

    def fromUnicode(self, string):
        """
        We implement :class:`.IFromUnicode` by adapting the given object
        to our text schema.
        """
        return super(TextUnicodeContentFragment, self).fromUnicode(self.schema(string))

class TextLineUnicodeContentFragment(Object, TextLine):
    """
    A :class:`zope.schema.TextLine` type that also requires the object implement
    an interface descending from :class:`~.IUnicodeContentFragment`.

    Pass the keyword arguments for :class:`zope.schema.TextLine` to the constructor; the ``schema``
    argument for :class:`~zope.schema.Object` is already handled.

    If you pass neither a `default` nor `defaultFactory` argument, a `defaultFactory`
    argument will be provided to construct an empty content fragment.
    """

    _iface = IContentFragment
    _impl = UnicodeContentFragment

    def __init__(self, *args, **kwargs):
        super(TextLineUnicodeContentFragment, self).__init__(self._iface, *args, **_massage_kwargs(self, kwargs))

    def fromUnicode(self, string):
        """
        We implement :class:`.IFromUnicode` by adapting the given object
        to our text schema.
        """
        return super(TextLineUnicodeContentFragment, self).fromUnicode(self.schema(string))

class LatexFragmentTextLine(TextLineUnicodeContentFragment):
    """
    A :class:`~zope.schema.TextLine` that requires content to be in LaTeX format.

    Pass the keyword arguments for :class:`~zope.schema.TextLine` to the constructor; the ``schema``
    argument for :class:`~zope.schema.Object` is already handled.

    .. note:: If you provide a ``default`` string that does not already provide :class:`.ILatexContentFragment`,
        one will be created simply by copying; no validation or transformation will occur.
    """

    _iface = ILatexContentFragment
    _impl = LatexContentFragment

class PlainTextLine(TextLineUnicodeContentFragment):
    """
    A :class:`~zope.schema.TextLine` that requires content to be plain text.

    Pass the keyword arguments for :class:`~zope.schema.TextLine` to the constructor; the ``schema``
    argument for :class:`~zope.schema.Object` is already handled.

    .. note:: If you provide a ``default`` string that does not already provide :class:`.ILatexContentFragment`,
        one will be created simply by copying; no validation or transformation will occur.
    """

    _iface = IPlainTextContentFragment
    _impl = PlainTextContentFragment

class HTMLContentFragment(TextUnicodeContentFragment):
    """
    A :class:`~zope.schema.Text` type that also requires the object implement
    an interface descending from :class:`.IHTMLContentFragment`.

    Pass the keyword arguments for :class:`zope.schema.Text` to the constructor; the ``schema``
    argument for :class:`~zope.schema.Object` is already handled.

    .. note:: If you provide a ``default`` string that does not already provide :class:`.IHTMLContentFragment`,
        one will be created simply by copying; no validation or transformation will occur.
    """

    _iface = IHTMLContentFragment
    _impl = HTMLContentFragment

class SanitizedHTMLContentFragment(HTMLContentFragment):
    """
    A :class:`Text` type that also requires the object implement
    an interface descending from :class:`.ISanitizedHTMLContentFragment`.

    Pass the keyword arguments for :class:`zope.schema.Text` to the constructor; the ``schema``
    argument for :class:`~zope.schema.Object` is already handled.

    .. note:: If you provide a ``default`` string that does not already provide :class:`.ISanitizedHTMLContentFragment`,
        one will be created simply by copying; no validation or transformation will occur.

    """

    _iface = ISanitizedHTMLContentFragment
    _impl = SanitizedHTMLContentFragment

class PlainText(TextUnicodeContentFragment):
    """
    A :class:`zope.schema.Text` that requires content to be plain text.

    Pass the keyword arguments for :class:`~zope.schema.Text` to the constructor; the ``schema``
    argument for :class:`~zope.schema.Object` is already handled.

    .. note:: If you provide a ``default`` string that does not already provide :class:`.IPlainTextContentFragment`,
        one will be created simply by copying; no validation or transformation will occur.
    """

    _iface = IPlainTextContentFragment
    _impl = PlainTextContentFragment

class Tag(PlainTextLine):
    """
    Requires its content to be only one plain text word that is lowercased.
    """

    def fromUnicode(self, value):
        return super(Tag, self).fromUnicode(value.lower())

    def constraint(self, value):
        return super(Tag, self).constraint(value) and ' ' not in value

def Title():
    """
    Return a :class:`zope.schema.interfaces.IField` representing
    the standard title of some object. This should be stored in the `title`
    field.
    """
    return PlainTextLine(
                    max_length=140,  # twitter
                    required=False,
                    title="The human-readable title of this object",
                    __name__='title')
