======================
 nti.contentfragments
======================

.. image:: https://img.shields.io/pypi/v/nti.contentfragments.svg
        :target: https://pypi.python.org/pypi/nti.contentfragments/
        :alt: Latest release

.. image:: https://img.shields.io/pypi/pyversions/nti.contentfragments.svg
        :target: https://pypi.org/project/nti.contentfragments/
        :alt: Supported Python versions

.. image:: https://travis-ci.org/NextThought/nti.contentfragments.svg?branch=master
        :target: https://travis-ci.org/NextThought/nti.contentfragments

.. image:: https://coveralls.io/repos/github/NextThought/nti.contentfragments/badge.svg
        :target: https://coveralls.io/github/NextThought/nti.contentfragments

.. image:: https://readthedocs.org/projects/nticontentfragments/badge/?version=latest
        :target: https://nticontentfragments.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

Support for working with string-based content in a Zope3/ZTK
environment.

Overview
========

In a client/server environment dealing with various types of content
from users, it's important to know what not just the Python type of a
particular string is, but also what the *semantic* type of the string
is: HTML, plain text, LaTeX, etc.

This package defines interfaces and classes to be able to record this
information. It also features a framework for transforming between the
various supported semantic types (e.g., HTML to plain text).

Other features:

- Support for making arbitrary incoming HTML safe (sanitizing it).
- Support for very configurable (optionally) event-based profanity
  censoring that integrates with nti.schema/zope.schema.

See `the documentation <http://nticontentfragments.readthedocs.io/en/latest/>`_ for more details.
