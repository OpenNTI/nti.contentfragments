#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__docformat__ = "restructuredtext en"

from hamcrest import assert_that
from hamcrest import calling
from hamcrest import raises
from hamcrest import is_

from nti.contentfragments.interfaces import IPlainTextContentFragment
from nti.contentfragments.interfaces import IRstContentFragment

from nti.contentfragments.rst import check_user_rst
from nti.contentfragments.rst import RstParseError

from nti.contentfragments.tests import ContentfragmentsLayerTest

from nti.testing.matchers import verifiably_provides


class TestRST(ContentfragmentsLayerTest):

    def test_check_rst(self):
        content = "=====\nTitle\n=====\n\n.. sidebar:: sidebar title\n\n   Some more content"
        check_user_rst(content)

    def test_check_rst_failure(self):
        content = "=====\nTitle\n=====\n\n.. sidebar:: sidebar title\n\nSome more content"
        assert_that(calling(check_user_rst).with_args(content),
                    raises(RstParseError, "Content block expected"))

    def test_plaintext(self):
        content = u"== ==\nH1 H2\n-- --\nc1 c2\n== ==\n\n"\
                  u".. sidebar:: sidebar title\n\n   Some more content"
        rst_content = IRstContentFragment(content)
        assert_that(rst_content, verifiably_provides(IRstContentFragment))

        plaintext = IPlainTextContentFragment(rst_content)
        assert_that(plaintext, is_("\n\n\n\nH1\n\nH2\n\nc1\n\nc2\n\nsidebar title\n\nSome more content"))

