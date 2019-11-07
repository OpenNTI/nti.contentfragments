=========
 Changes
=========

1.2.1 (2019-11-07)
==================

- Remove a word from the censored word list. See issue #22.


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
