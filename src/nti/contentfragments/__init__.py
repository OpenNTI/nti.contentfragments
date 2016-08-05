#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A package supporting working with and transforming among
snippets of content (mostly that can be represented as unicode strings).

This package and interfaces are mostly concerned with the representations
of content fragments within the system.


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

.. $Id: __init__.py 58673 2015-02-02 17:52:58Z carlos.sanchez $
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)
