=========
 Changes
=========

1.1.0
-----

- Depend on zope.mimetype >= 2.1.0 for better support of Python 3.

1.0.0
------

- Add support for Python 3.
- Stop configuring plone.i18n. It's a big dependency and doesn't work
  on Python 3.
- Introduce our own interfaces for IUnicode and IString, subclassing
  dolmen.builtins.IUnicode and IString, respectively, if possible.
- The word lists used in censoring are cached in memory.
- :class:`nti.contentfragments.html._Serializer` has been renamed and
  is no longer public.
