#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Support for reStructuredText content fragments.
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import sys

import six

from docutils.core import publish_parts
from docutils.utils import SystemMessage

from .interfaces import RstContentFragment


SETTINGS = {
    # Prevent local files from being included into the rendered output.
    # This is a security concern because people can insert files
    # that are part of the system, such as /etc/passwd.
    "file_insertion_enabled": False,

    # Halt rendering and throw an exception if there was any errors or
    # warnings from docutils.
    "halt_level": 3,

    # Disable raw html as enabling it is a security risk, we do not want
    # people to be able to include any old HTML in the final output.
    "raw_enabled": False,

    # Disable all system messages from being reported.
    "report_level": 5,

    # Use the short form of syntax highlighting so that the generated
    # Pygments CSS can be used to style the output.
    "syntax_highlight": "none",
}


class RstParseError(Exception):
    """
    An error has occurred parsing reStructuredText
    """


def check_user_rst(input):

    if input:
        try:
            settings = SETTINGS.copy()
            publish_parts(input, settings_overrides=settings)
        except SystemMessage as e:
            six.reraise(RstParseError, RstParseError(*e.args), sys.exc_info()[2])

    return RstContentFragment(input)
