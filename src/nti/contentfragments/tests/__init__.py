#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import
__docformat__ = "restructuredtext en"

# pylint:disable=useless-object-inheritance

from hamcrest import assert_that

from nti.testing.layers import ZopeComponentLayer
from nti.testing.layers import ConfiguringLayerMixin
from nti.testing.matchers import verifiably_provides

import zope.testing.cleanup

class ContentfragmentsTestLayer(ZopeComponentLayer, ConfiguringLayerMixin):

    set_up_packages = ('nti.contentfragments',)

    @classmethod
    def setUp(cls):
        cls.setUpPackages()

    @classmethod
    def tearDown(cls):
        cls.tearDownPackages()
        zope.testing.cleanup.cleanUp()

    @classmethod
    def testSetUp(cls, test=None): # pylint:disable=arguments-differ
        pass

    @classmethod
    def testTearDown(cls):
        pass

import unittest

class ContentfragmentsLayerTest(unittest.TestCase):
    layer = ContentfragmentsTestLayer


class FieldTestsMixin(object):

    def _makeOne(self, *args, **kwargs):
        return self._getTargetClass()(*args, **kwargs)

    def _getTargetClass(self):
        raise NotImplementedError()

    def _getTargetInterface(self):
        raise NotImplementedError()

    def test_implements_interface(self):
        inst = self._makeOne()
        assert_that(inst, verifiably_provides(self._getTargetInterface()))
