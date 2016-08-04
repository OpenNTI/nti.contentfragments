#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id: punctuation.py 85352 2016-03-26 19:08:54Z carlos.sanchez $
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import re

from zope import interface

from nti.contentfragments.interfaces import IPunctuationMarkPattern
from nti.contentfragments.interfaces import IPunctuationMarkExpression
from nti.contentfragments.interfaces import IPunctuationMarkPatternPlus
from nti.contentfragments.interfaces import IPunctuationMarkExpressionPlus

default_punk_mark_expression = (ur'[\?|!|(|)|"|\''
                                u'|\u2039|\u203a'  # single angle quotes
                                u'|\u2018|\u2019'  # single curly quotes
                                u'|\u201c|\u201d'  # double curly quotes
                                u'|\u00ab|\u00bb'  # double angle quotes
                                ur'|`|{|}|\[|\]|:|;|,|\.|\^|%|&|#|\*|@|'
                                u'$|\u20ac'  # dollar and euro
                                ur'|&|+|\-|<|>|=|_|\~|\\|/|\|]')

default_punk_mark_expression_plus = (default_punk_mark_expression[:-1] +
                                     ur'|\s'
                                     ur'|\u200b|\u2060]')  # zero-width space, word joiner

default_punk_mark_pattern = re.compile(default_punk_mark_expression,
                                       re.I | re.MULTILINE | re.DOTALL | re.UNICODE)

default_punk_mark_pattern_plus = re.compile(default_punk_mark_expression_plus,
                                            re.I | re.MULTILINE | re.DOTALL | re.UNICODE)

@interface.implementer(IPunctuationMarkExpression)
def _default_punctuation_mark_expression():
    return default_punk_mark_expression

@interface.implementer(IPunctuationMarkPattern)
def _default_punctuation_mark_pattern():
    return default_punk_mark_pattern

@interface.implementer(IPunctuationMarkExpressionPlus)
def _default_punctuation_mark_expression_plus():
    return default_punk_mark_expression_plus

@interface.implementer(IPunctuationMarkPatternPlus)
def _default_punctuation_mark_pattern_plus():
    return default_punk_mark_pattern_plus
