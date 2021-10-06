=========
 Changes
=========

1.8.1 (unreleased)
==================

- Nothing changed yet.


1.8.0 (2021-10-06)
==================

- Add support for Python 3.9 and 3.10.
- Move to Github Actions from Travis CI.
- The algorithm for converting HTML to plain text has been changed and
  produces higher quality output. For example, links are preserved in
  a human-readable fashion. See `issue 39 <https://github.com/NextThought/nti.contentfragments/issues/39>`_.
- Fix an error getting link text when there was no link formatter
  utility installed. See `PR 42
  <https://github.com/NextThought/nti.contentfragments/pull/41#event-5422788226>`_.

1.7.0 (2020-10-07)
==================

- Allow conversion of reStructuredText fragments to plain text.


1.6.1 (2020-09-14)
==================

- Ensure disallowed tags nested within anchors do not raise.
  See `issue 34 <https://github.com/NextThought/nti.contentfragments/issues/34>`_.


1.6.0 (2020-09-02)
==================

- Add support for reStructuredText content fragments and corresponding
  fields.


1.5.0 (2020-07-23)
==================

- When sanitizing html, disable link creation when already under an anchor.


1.4.0 (2020-06-17)
==================

- Allow ``IAllowedAttributeProvider`` to be registered to provide
  additional attributes that would be allowed in sanitized content
  fragments.


1.3.0 (2020-04-06)
==================

- Add support for Python 3.8.

- Depend on zope.interface 5.0.

- Update the datrie dependency. See https://github.com/NextThought/nti.contentfragments/issues/24

- Make ``IUnicodeContentFragment`` extend
  ``zope.interface.common.collections.ISequence`` instead of the
  semi-deprecated ``zope.interface.common.sequence.IReadSequence``.

- Replace custom interfaces ``IString``, ``IUnicode`` and ``IBytes``
  with aliases for ``INativeString``, ``ITextString`` and
  ``IByteString`` from ``zope.interface.common.builtins``. These
  custom aliases are now deprecated. See https://github.com/NextThought/nti.contentfragments/issues/23.

- Fix unicode normalization breaking schema fields with zope.schema
  6.0. See https://github.com/NextThought/nti.contentfragments/issues/26

- Ensure all objects have consistent resolution orders.

1.2.1 (2019-11-07)
==================

- Remove a word from the censored word list. See issue https://github.com/NextThought/nti.contentfragments/issues/22.


1.2.0 (2018-10-15)
==================

- Add support for Python 3.7. Note that ``datrie`` is not yet
  available for Python 3.7.

- Add support for PyPy3.

- Add interfaces for all schema fields defined in
  ``nti.contentfragments.schema`` and make the respective classes
  implement them.

1.1.1 (2018-06-29)
==================

- Packaging: Do not use ``html5lib[datrie]`` and instead copy that
  dependency into our own dependencies to workaround a buildout error.
  See https://github.com/NextThought/nti.contentfragments/issues/17


1.1.0 (2017-06-14)
==================

- Remove dependency of ``dolmen.builtins``. The interfaces
  ``IUnicode``, ``IBytes`` and ``IString`` are now always defined by this package.

- Add support for Python 3.6.


1.0.0 (2016-08-19)
==================

- Add support for Python 3.
- Stop configuring plone.i18n. It's a big dependency and doesn't work
  on Python 3.
- Introduce our own interfaces for IUnicode and IString, subclassing
  dolmen.builtins.IUnicode and IString, respectively, if possible.
- The word lists used in censoring are cached in memory.
- ``nti.contentfragments.html._Serializer`` has been renamed and
  is no longer public.
- Depend on zope.mimetype >= 2.1.0 for better support of Python 3.
