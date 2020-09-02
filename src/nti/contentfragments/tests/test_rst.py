#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__docformat__ = "restructuredtext en"

from hamcrest import assert_that
from hamcrest import calling
from hamcrest import raises

from nti.contentfragments.rst import check_user_rst
from nti.contentfragments.rst import RstParseError

from nti.contentfragments.tests import ContentfragmentsLayerTest


class TestRST(ContentfragmentsLayerTest):

    def test_check_rst(self):
        content = "=====\nTitle\n=====\n\n.. sidebar:: sidebar title\n\n   Some more content"
        check_user_rst(content)

    def test_check_rst_failure(self):
        content = "=====\nTitle\n=====\n\n.. sidebar:: sidebar title\n\nSome more content"
        assert_that(calling(check_user_rst).with_args(content),
                    raises(RstParseError, "Content block expected"))
