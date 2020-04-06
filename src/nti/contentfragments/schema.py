#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Helper classes to use content fragments in :mod:`zope.interface`
or :mod:`zope.schema` declarations.

.. $Id: schema.py 85352 2016-03-26 19:08:54Z carlos.sanchez $
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

# pylint: disable=too-many-ancestors
# pylint:disable=useless-object-inheritance

import unicodedata

from zope.interface import implementer

from .interfaces import HTMLContentFragment as HTMLContentFragmentType
from .interfaces import IHTMLContentFragment
from .interfaces import LatexContentFragment
from .interfaces import ILatexContentFragment
from .interfaces import UnicodeContentFragment
from .interfaces import IUnicodeContentFragment
from .interfaces import PlainTextContentFragment
from .interfaces import IPlainTextContentFragment
from .interfaces import SanitizedHTMLContentFragment as SanitizedHTMLContentFragmentType
from .interfaces import ISanitizedHTMLContentFragment

from .interfaces import ITextUnicodeContentFragmentField
from .interfaces import ITextLineUnicodeContentFragmentField
from .interfaces import ILatexFragmentTextLineField
from .interfaces import IPlainTextLineField
from .interfaces import IPlainTextField
from .interfaces import IHTMLContentFragmentField
from .interfaces import ISanitizedHTMLContentFragmentField
from .interfaces import ITagField

from nti.schema.field import Object
from nti.schema.field import ValidText as Text
from nti.schema.field import ValidTextLine as TextLine

class _FromUnicodeMixin(object):

    # Set the interface to use as self.schema. This will be implemented by
    # objects returned from ``fromUnicode``. However...
    _iface = None
    # If the adapter registered to produce _iface may produce some
    # interface less restrictive than that (e.g., _iface is HTML, but
    # we can produce plain text)
    # set this to become self.schema.
    _iface_upper_bound = None
    # This is the class used to copy defaults.
    _impl = lambda *args: None

    def __init__(self, *args, **kwargs):
        super(_FromUnicodeMixin, self).__init__(
            self._iface_upper_bound or self._iface, # Becomes self.schema.
            *args,
            **self.__massage_kwargs(kwargs))

    def __massage_kwargs(self, kwargs):

        assert self._iface.isOrExtends(IUnicodeContentFragment), self._iface
        assert self._iface.implementedBy(self._impl), self._impl

        # We're imported too early for ZCA to be configured and we can't automatically
        # adapt.
        if 'default' in kwargs and not self._iface.providedBy(kwargs['default']):
            kwargs['default'] = self._impl(kwargs['default'])
        if 'default' not in kwargs and 'defaultFactory' not in kwargs and not kwargs.get('min_length'):  # 0/None
            kwargs['defaultFactory'] = self._impl
        # Disable unicode normalization at this level; we need to handle it
        # to properly deal with our content fragment subclasses.
        assert 'unicode_normalization' not in kwargs
        kwargs['unicode_normalization'] = None
        return kwargs

    def fromUnicode(self, value):
        """
        We implement :class:`.IFromUnicode` by adapting the given object
        to our text schema.

        This happens *after* unicode normalization.
        """
        # unicodedate.normalize does not preserve the class of the
        # object it's given (it goes back to text_type; always under PyPy, only if
        # changes are needed under CPython). So we must handle normalization ourself
        # before converting to the schema.
        value = unicodedata.normalize(self.__class__.unicode_normalization, value)
        value = self.schema(value)
        result = super(_FromUnicodeMixin, self).fromUnicode(value)
        return result


@implementer(ITextUnicodeContentFragmentField)
class TextUnicodeContentFragment(_FromUnicodeMixin, Object, Text):
    """
    A :class:`zope.schema.Text` type that also requires the object implement
    an interface descending from :class:`~.IUnicodeContentFragment`.

    Pass the keyword arguments for :class:`zope.schema.Text` to the constructor; the ``schema``
    argument for :class:`~zope.schema.Object` is already handled.
    """

    _iface = IUnicodeContentFragment
    _impl = UnicodeContentFragment


@implementer(ITextLineUnicodeContentFragmentField)
class TextLineUnicodeContentFragment(_FromUnicodeMixin, Object, TextLine):
    """
    A :class:`zope.schema.TextLine` type that also requires the object implement
    an interface descending from :class:`~.IUnicodeContentFragment`.

    Pass the keyword arguments for :class:`zope.schema.TextLine` to the constructor; the ``schema``
    argument for :class:`~zope.schema.Object` is already handled.

    If you pass neither a `default` nor `defaultFactory` argument, a `defaultFactory`
    argument will be provided to construct an empty content fragment.
    """

    _iface = IUnicodeContentFragment
    _impl = UnicodeContentFragment


@implementer(ILatexFragmentTextLineField)
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


@implementer(IPlainTextLineField)
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


@implementer(IHTMLContentFragmentField)
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
    _impl = HTMLContentFragmentType


@implementer(ISanitizedHTMLContentFragmentField)
class SanitizedHTMLContentFragment(HTMLContentFragment):
    """
    A :class:`Text` type that also requires the object implement
    an interface descending from :class:`.ISanitizedHTMLContentFragment`.
    Note that the default adapter for this can actually produce
    ``IPlainTextContentFragment`` if there is no HTML present in the input.

    Pass the keyword arguments for :class:`zope.schema.Text` to the constructor; the ``schema``
    argument for :class:`~zope.schema.Object` is already handled.

    .. note:: If you provide a ``default`` string that does not already provide :class:`.ISanitizedHTMLContentFragment`,
        one will be created simply by copying; no validation or transformation will occur.

    """

    _iface = ISanitizedHTMLContentFragment
    _impl = SanitizedHTMLContentFragmentType

@implementer(IPlainTextField)
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


@implementer(ITagField)
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
        title=u"The human-readable title of this object",
        __name__='title')
